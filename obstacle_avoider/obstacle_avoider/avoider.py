import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool
import math

class Avoider(Node):
    def __init__(self):
        super().__init__("avoider")
        self.is_active = False
        self.publisher_ = self.create_publisher(Twist,"/cmd_vel",10)
        self.subscriber_ = self.create_subscription(LaserScan,"/scan",self.topic_callback,10)
        self.server_ = self.create_service(SetBool, "/toggle_robot",self.service_callback)
        self.velocityx = 0.0
        self.angularz = 0.0
        self.rotated = 0


            

    def topic_callback(self,msg):
        self.mssg = Twist()
        if(not self.is_active): 
            self.mssg.linear.x = 0.0
            self.mssg.angular.z = 0.0
         
            self.get_logger().info("Robot not started")
        else:
            left_index = 90
            right_index = 270
            index = 0
            self.front_distance = msg.ranges[index]
            self.get_logger().info("Robot in spinning motion:" + str(msg.ranges[0]))

            if not (self.front_distance <= msg.range_max):
                self.front_distance = float('inf')

            if(self.front_distance >  1 and self.front_distance != float('-inf')):
                self.angularz *= 0.9996
                self.mssg.linear.x = self.velocityx
                self.mssg.angular.z = self.angularz
            else:
                left_distance = msg.ranges[left_index]
                right_distance = msg.ranges[right_index]
                if not (msg.range_min <= left_distance <= msg.range_max):
                    left_distance = float('inf')
                if not (msg.range_min <= right_distance <= msg.range_max):
                    right_distance = float('inf')

            
                if(left_distance > right_distance):
                    self.mssg.linear.x = self.velocityx
                    self.mssg.angular.z = 0.3
                    self.get_logger().info("Robot turning to left")

                else:
                    self.mssg.angular.z = -0.3
                    self.mssg.linear.x = self.velocityx
                    self.get_logger().info("Robot turning to right")
            self.publisher_.publish(self.mssg)
            

    def service_callback(self,srv,response):
        if(srv.data == True):
            self.is_active = True
            if(self.velocityx == 0):
                self.velocityx = 0.2
                self.angularz = 0.3
        else:
            self.is_active = False

        response.success = True
        return response

def main(args = None):
    rclpy.init(args=args)
    node = Avoider()
    rclpy.spin(node)
    rclpy.shutdown()