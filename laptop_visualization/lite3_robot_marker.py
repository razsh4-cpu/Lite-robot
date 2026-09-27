#!/usr/bin/env python3
"""Publish a visualization-only Lite3 body marker in base_link."""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from visualization_msgs.msg import Marker


class Lite3RobotMarker(Node):
    def __init__(self):
        super().__init__("lite3_robot_marker")
        qos = QoSProfile(depth=1)
        qos.reliability = ReliabilityPolicy.RELIABLE
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.publisher = self.create_publisher(Marker, "/lite3/robot_body", qos)
        self.timer = self.create_timer(1.0, self.publish_marker)
        self.publish_marker()

    def publish_marker(self):
        marker = Marker()
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.header.frame_id = "base_link"
        marker.ns = "lite3_body"
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose.position.z = 0.06
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.610
        marker.scale.y = 0.370
        marker.scale.z = 0.12
        marker.color.r = 0.05
        marker.color.g = 0.30
        marker.color.b = 1.0
        marker.color.a = 0.55
        self.publisher.publish(marker)


def main():
    rclpy.init()
    node = Lite3RobotMarker()
    try:
        rclpy.spin(node)
    except (ExternalShutdownException, KeyboardInterrupt):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
