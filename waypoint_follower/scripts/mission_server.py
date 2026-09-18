#!/usr/bin/env python3
"""
mission_server.py

Action server for waypoint_follower/action/Mission.

Loads a mission YAML file (base point + ordered waypoints + return_to_base
flag), drives the robot through each waypoint with a simple proportional
controller, streams feedback, and supports mid-mission cancellation.
"""

import math
import os
import time

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from waypoint_follower.action import Mission


# --- Tunable control gains -------------------------------------------------
LINEAR_SPEED_MAX = 0.2          # m/s
ANGULAR_SPEED_MAX = 1.0         # rad/s
ANGULAR_GAIN = 2.0              # proportional gain on heading error
DISTANCE_TOLERANCE = 0.1        # m -- close enough to call a waypoint "reached"
HEADING_TOLERANCE = 0.1         # rad -- below this, allow forward motion
CONTROL_PERIOD = 0.1            # s -- 10 Hz control loop


def yaw_from_quaternion(q):
    """Extract yaw (rotation about Z) from a geometry_msgs Quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def normalize_angle(angle):
    """Wrap an angle to [-pi, pi]."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class MissionServer(Node):

    def __init__(self):
        super().__init__('mission_server')

        # Current pose, tracked from odometry.
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        # A reentrant group + multithreaded executor is what lets
        # /odom callbacks and is_cancel_requested checks keep flowing
        # *while* execute_callback is mid-mission (which otherwise
        # blocks in its own control loop).
        self._cb_group = ReentrantCallbackGroup()

        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10,
            callback_group=self._cb_group)

        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self._action_server = ActionServer(
            self,
            Mission,
            'follow_mission',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self._cb_group,
        )

        self.get_logger().info('Mission server ready, waiting for goals.')

    # -- Server callbacks -------------------------------------------------

    def odom_callback(self, msg: Odometry):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        self.current_yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def goal_callback(self, goal_request):
        self.get_logger().info(
            f'Received mission request: {goal_request.mission_file}')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Cancel request received.')
        return CancelResponse.ACCEPT

    # -- Mission loading ---------------------------------------------------

    def load_mission(self, mission_file: str):
        """
        Resolve mission_file inside this package's installed share/missions
        directory and parse it. Returns (waypoints, base, return_to_base).
        """
        package_share = get_package_share_directory('waypoint_follower')
        mission_path = os.path.join(package_share, 'missions', mission_file)

        with open(mission_path, 'r') as f:
            data = yaml.safe_load(f)

        waypoints = data['waypoints']                      # ordered list of {x, y}
        base = data.get('base', {'x': 0.0, 'y': 0.0})
        return_to_base = bool(data.get('return_to_base', False))
        return waypoints, base, return_to_base

    # -- Motion primitives ---------------------------------------------------

    def stop_robot(self):
        self.cmd_vel_pub.publish(Twist())

    def drive_toward(self, target_x, target_y):
        """
        One control tick: turn-to-face then drive-forward proportional
        controller (same heading/distance math style as Week 1's obstacle
        avoider). Returns the current straight-line distance to target.
        """
        dx = target_x - self.current_x
        dy = target_y - self.current_y
        distance = math.hypot(dx, dy)

        target_heading = math.atan2(dy, dx)
        heading_error = normalize_angle(target_heading - self.current_yaw)

        cmd = Twist()

        if abs(heading_error) > HEADING_TOLERANCE:
            # Turn in place to face the waypoint first.
            angular = ANGULAR_GAIN * heading_error
            cmd.angular.z = max(-ANGULAR_SPEED_MAX,
                                 min(ANGULAR_SPEED_MAX, angular))
            cmd.linear.x = 0.0
        else:
            # Roughly facing the target: drive forward (slowing near the
            # goal), with a small heading trim.
            cmd.linear.x = min(LINEAR_SPEED_MAX, distance)
            cmd.angular.z = 0.5 * ANGULAR_GAIN * heading_error

        self.cmd_vel_pub.publish(cmd)
        return distance

    def drive_to_point(self, goal_handle, target_x, target_y,
                        waypoint_index, status_label):
        """
        Drives until the target is reached or cancellation is requested.
        Publishes feedback every control tick. Returns
        (reached: bool, distance_traveled: float).
        """
        distance_traveled = 0.0
        last_x, last_y = self.current_x, self.current_y

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                self.stop_robot()
                goal_handle.canceled()
                return False, distance_traveled

            remaining = self.drive_toward(target_x, target_y)

            step = math.hypot(self.current_x - last_x,
                               self.current_y - last_y)
            distance_traveled += step
            last_x, last_y = self.current_x, self.current_y

            feedback_msg = Mission.Feedback()
            feedback_msg.current_waypoint_index = waypoint_index
            feedback_msg.status = status_label
            feedback_msg.distance_to_target = remaining
            goal_handle.publish_feedback(feedback_msg)

            if remaining <= DISTANCE_TOLERANCE:
                self.stop_robot()
                return True, distance_traveled

            time.sleep(CONTROL_PERIOD)

        self.stop_robot()
        return False, distance_traveled

    # -- Main execute callback ---------------------------------------------

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        self.get_logger().info(f'Executing mission: {goal.mission_file}')

        waypoints, base, return_to_base = self.load_mission(goal.mission_file)

        total_distance = 0.0
        waypoints_completed = 0

        for i, wp in enumerate(waypoints):
            status = f'en route to waypoint {i + 1}/{len(waypoints)}'
            reached, dist = self.drive_to_point(
                goal_handle, wp['x'], wp['y'], i, status)
            total_distance += dist

            if not reached:
                # Canceled mid-flight -- goal_handle.canceled() was
                # already called inside drive_to_point.
                result = Mission.Result()
                result.success = False
                result.total_distance = total_distance
                result.waypoints_completed = waypoints_completed
                return result

            waypoints_completed += 1

        if return_to_base:
            reached, dist = self.drive_to_point(
                goal_handle, base['x'], base['y'],
                len(waypoints), 'returning to base')
            total_distance += dist

            if not reached:
                result = Mission.Result()
                result.success = False
                result.total_distance = total_distance
                result.waypoints_completed = waypoints_completed
                return result

        goal_handle.succeed()

        result = Mission.Result()
        result.success = True
        result.total_distance = total_distance
        result.waypoints_completed = waypoints_completed
        return result


def main(args=None):
    rclpy.init(args=args)
    node = MissionServer()

    # MultiThreadedExecutor so odom callbacks and cancel checks keep
    # running while execute_callback's control loop is mid-mission.
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
