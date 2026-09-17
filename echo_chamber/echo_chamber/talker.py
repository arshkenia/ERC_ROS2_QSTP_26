import rclpy
from rclpy.node import Node
from std_msgs import  msg
import random

class Talker(Node):
    def __init__(self):
        self.counter = 1
        super().__init__("talker")
        self.publisher = self.create_publisher(msg.Float32, "/random_number", 10)
        self.timer = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        message = msg.Float32()
        message.data = random.uniform(0,100)
        self.publisher.publish(message)
        self.get_logger().info("Publishing Message " + str(message.data))
        self.counter += 1

def main(args = None):
    rclpy.init(args = args)
    node = Talker()
    rclpy.spin(node)
    rclpy.shutdown()
    pass


if __name__ == 'main':
    main()