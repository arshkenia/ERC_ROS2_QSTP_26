#!/usr/bin/env python3
"""
mission_client.py

Action client for waypoint_follower/action/Mission.

Sends a mission goal (mission filename given as a ROS parameter, e.g.
`--ros-args -p mission_file:=mission_square.yaml`), prints feedback as it
streams in, prints the final result, and sends a proper cancel request
(rather than just killing the process) on Ctrl+C.
"""

import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from waypoint_follower.action import Mission


class MissionClient(Node):

    def __init__(self):
        super().__init__('mission_client')

        self.declare_parameter('mission_file', 'mission_square.yaml')
        self.mission_file = self.get_parameter('mission_file') \
            .get_parameter_value().string_value

        self._action_client = ActionClient(self, Mission, 'follow_mission')

        self._goal_handle = None
        self._done = False
        self._succeeded = False

    def send_goal(self):
        self.get_logger().info('Waiting for mission server...')
        self._action_client.wait_for_server()

        goal_msg = Mission.Goal()
        goal_msg.mission_file = self.mission_file

        self.get_logger().info(f'Sending mission: {self.mission_file}')
        send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        send_goal_future.add_done_callback(self.goal_response_callback)

    # -- Callbacks ----------------------------------------------------------

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal was rejected by the server.')
            self._done = True
            return

        self.get_logger().info('Goal accepted, mission underway.')
        self._goal_handle = goal_handle

        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'[waypoint {fb.current_waypoint_index}] {fb.status} '
            f'-- {fb.distance_to_target:.2f} m remaining')

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(
            f'Mission finished -- success: {result.success}, '
            f'total_distance: {result.total_distance:.2f} m, '
            f'waypoints_completed: {result.waypoints_completed}')
        self._succeeded = result.success
        self._done = True

    # -- Cancellation ---------------------------------------------------------

    def cancel_mission(self):
        if self._goal_handle is None:
            self.get_logger().info('No active goal to cancel.')
            return None

        self.get_logger().info('Sending cancel request...')
        return self._goal_handle.cancel_goal_async()


def main(args=None):
    rclpy.init(args=args)
    node = MissionClient()
    node.send_goal()

    try:
        # Spin until either a result arrives or the user hits Ctrl+C.
        while rclpy.ok() and not node._done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        node.get_logger().info('Ctrl+C received -- cancelling mission.')
        cancel_future = node.cancel_mission()
        if cancel_future is not None:
            # Give the cancel request a chance to actually reach the
            # server and be acknowledged before we tear the node down.
            rclpy.spin_until_future_complete(node, cancel_future,
                                              timeout_sec=2.0)
            # Drain a bit more so the final (canceled) result callback
            # gets a chance to fire and print.
            end_time = node.get_clock().now().nanoseconds + int(2e9)
            while (rclpy.ok() and not node._done and
                   node.get_clock().now().nanoseconds < end_time):
                rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
