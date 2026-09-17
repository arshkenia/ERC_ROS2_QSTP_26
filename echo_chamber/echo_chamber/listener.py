import rclpy
from rclpy.node import Node
from std_msgs import msg

class Listener(Node):
    def __init__(self):
        super().__init__("listener")
        self.subscriber = self.create_subscription(msg.Float32,"/random_number",self.callback,10)

    def callback(self,msg):
        self.get_logger().info("Received: " + str(msg.data) +" Multiplied value: " + str(2*msg.data))


def main(args = None):
    rclpy.init(args=args)
    node = Listener()
    rclpy.spin(node)
    rclpy.shutdown()
