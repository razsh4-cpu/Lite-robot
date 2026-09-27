#!/usr/bin/env python3
"""Synthetic free-space world for localhost-only Nav2 configuration tests.

Never install or run this on the robot. It publishes only synthetic ROS data
and contains no joystick, command-source, service, socket, or robot transport.
"""
import math

import rclpy
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster


class OfflineWorld(Node):
    def __init__(self):
        super().__init__("lite3_nav2_offline_world")
        map_qos = QoSProfile(depth=1)
        map_qos.reliability = ReliabilityPolicy.RELIABLE
        map_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.map_pub = self.create_publisher(OccupancyGrid, "/map", map_qos)
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.scan_pub = self.create_publisher(LaserScan, "/scan", 10)
        self.tf = TransformBroadcaster(self)
        self.static_tf = StaticTransformBroadcaster(self)
        self.map = self._map()
        self._publish_static_tf()
        self.create_timer(0.10, self._tick)

    def _map(self):
        msg = OccupancyGrid()
        msg.header.frame_id = "map"
        msg.info.resolution = 0.05
        msg.info.width = 120
        msg.info.height = 120
        msg.info.origin.position.x = -3.0
        msg.info.origin.position.y = -3.0
        msg.info.origin.orientation.w = 1.0
        data = [0] * (msg.info.width * msg.info.height)
        for x in range(msg.info.width):
            data[x] = 100
            data[(msg.info.height - 1) * msg.info.width + x] = 100
        for y in range(msg.info.height):
            data[y * msg.info.width] = 100
            data[y * msg.info.width + msg.info.width - 1] = 100
        msg.data = data
        return msg

    def _publish_static_tf(self):
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = "base_link"
        transform.child_frame_id = "lidar_link"
        transform.transform.translation.x = 0.20
        transform.transform.rotation.w = 1.0
        self.static_tf.sendTransform(transform)

    def _tick(self):
        stamp = self.get_clock().now().to_msg()
        self.map.header.stamp = stamp
        self.map_pub.publish(self.map)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.orientation.w = 1.0
        self.odom_pub.publish(odom)

        scan = LaserScan()
        scan.header.stamp = stamp
        scan.header.frame_id = "lidar_link"
        scan.angle_min = -math.pi
        scan.angle_max = math.pi
        scan.angle_increment = 2.0 * math.pi / 360.0
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = 0.10
        scan.range_max = 8.0
        scan.ranges = [5.0] * 361
        self.scan_pub.publish(scan)

        map_odom = TransformStamped()
        map_odom.header.stamp = stamp
        map_odom.header.frame_id = "map"
        map_odom.child_frame_id = "odom"
        map_odom.transform.rotation.w = 1.0
        odom_base = TransformStamped()
        odom_base.header.stamp = stamp
        odom_base.header.frame_id = "odom"
        odom_base.child_frame_id = "base_link"
        odom_base.transform.rotation.w = 1.0
        self.tf.sendTransform([map_odom, odom_base])


def main():
    rclpy.init()
    node = OfflineWorld()
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
