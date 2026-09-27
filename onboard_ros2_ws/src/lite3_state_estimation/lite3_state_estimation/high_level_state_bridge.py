#!/usr/bin/env python3
"""Receive-only Lite3 Motion Host telemetry to ROS 2.

This process owns UDP 43897 but creates no command socket and has no send path.
It must not run concurrently with another Motion Host telemetry receiver.
"""

import importlib.util
from pathlib import Path
import socket
import sys
import time
import types

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState
from std_msgs.msg import Bool, Float32, Int32
from tf2_ros import TransformBroadcaster

from .core import (
    JOINT_NAMES,
    PlanarStartupOrigin,
    decode_joint_state,
    decode_robot_state,
    feedback_is_fresh,
    quaternion_from_rpy,
)


def load_codecs(plugin_root):
    package_dir = Path(plugin_root).expanduser() / "lite3_plugin"
    package_name = "_lite3_high_level_state_protocol"
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_dir)]
    sys.modules[package_name] = package
    loaded = {}
    for name in ("protocol", "codecs"):
        path = package_dir / f"{name}.py"
        spec = importlib.util.spec_from_file_location(f"{package_name}.{name}", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load high-level protocol file: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        setattr(package, name, module)
        spec.loader.exec_module(module)
        loaded[name] = module
    return loaded["codecs"]


class HighLevelStateBridge(Node):
    def __init__(self):
        super().__init__("lite3_high_level_state_bridge")
        self.declare_parameter("robot_ip", "192.168.1.120")
        self.declare_parameter("bind_host", "192.168.1.102")
        self.declare_parameter("telemetry_port", 43897)
        self.declare_parameter("plugin_root", "/home/abx/emos-plugin-lite3")
        self.declare_parameter("stale_timeout_s", 0.30)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")

        self.robot_ip = str(self.get_parameter("robot_ip").value)
        bind_host = str(self.get_parameter("bind_host").value)
        telemetry_port = int(self.get_parameter("telemetry_port").value)
        self.stale_timeout = float(self.get_parameter("stale_timeout_s").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.codecs = load_codecs(str(self.get_parameter("plugin_root").value))

        # Deliberately omit SO_REUSEADDR/SO_REUSEPORT: a second receiver must
        # fail closed rather than steal unicast telemetry from robot control.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((bind_host, telemetry_port))
        except Exception:
            self.sock.close()
            raise
        self.sock.setblocking(False)

        self.odom_pub = self.create_publisher(Odometry, "/odom", 20)
        self.imu_pub = self.create_publisher(Imu, "/imu/data", 20)
        self.joint_pub = self.create_publisher(JointState, "/joint_states", 20)
        self.state_pub = self.create_publisher(Int32, "/lite3/robot_basic_state", 10)
        self.battery_pub = self.create_publisher(Float32, "/lite3/battery_percent", 10)
        self.fresh_pub = self.create_publisher(Bool, "/lite3/robot_state_fresh", 10)
        self.tf = TransformBroadcaster(self)
        self.odom_origin = PlanarStartupOrigin()
        self.last_robot_state = None
        self.last_fresh_value = None
        self.robot_packets = 0
        self.joint_packets = 0
        self.rate_start = time.monotonic()
        self.create_timer(0.005, self._drain)
        self.create_timer(0.10, self._freshness)
        self.create_timer(5.0, self._report_rate)
        self.get_logger().warning(
            f"RECEIVE ONLY: Motion Host {self.robot_ip} -> {bind_host}:{telemetry_port}; "
            "no command socket, no ownership, no robot packets sent"
        )

    def _drain(self):
        if not rclpy.ok():
            return
        for _ in range(512):
            try:
                raw, source = self.sock.recvfrom(4096)
            except BlockingIOError:
                return
            if source[0] != self.robot_ip:
                continue
            robot = self.codecs.parse_robot_state(raw)
            if robot is not None:
                try:
                    self._publish_robot(decode_robot_state(robot))
                except ValueError as exc:
                    self.get_logger().error(str(exc))
                continue
            joints = self.codecs.parse_joint_state(raw)
            if joints is not None:
                try:
                    self._publish_joints(decode_joint_state(joints))
                except ValueError as exc:
                    self.get_logger().error(str(exc))

    def _publish_robot(self, data):
        stamp = self.get_clock().now().to_msg()
        self.last_robot_state = time.monotonic()
        self.robot_packets += 1

        imu = Imu()
        imu.header.stamp = stamp
        imu.header.frame_id = self.base_frame
        (imu.orientation.x, imu.orientation.y, imu.orientation.z,
         imu.orientation.w) = data["orientation"]
        (imu.angular_velocity.x, imu.angular_velocity.y,
         imu.angular_velocity.z) = data["angular_velocity"]
        (imu.linear_acceleration.x, imu.linear_acceleration.y,
         imu.linear_acceleration.z) = data["linear_acceleration"]
        # Zero covariance means unknown, not a fabricated measurement model.
        self.imu_pub.publish(imu)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        relative_x, relative_y, relative_yaw, first = self.odom_origin.transform(
            data["position_xy"][0], data["position_xy"][1], data["rpy"][2])
        if first:
            self.get_logger().info(
                "Latched high-level odom origin: "
                f"x={data['position_xy'][0]:+.6f} y={data['position_xy'][1]:+.6f} "
                f"yaw={data['rpy'][2]:+.6f} rad")
        odom.pose.pose.position.x = relative_x
        odom.pose.pose.position.y = relative_y
        odom.pose.pose.position.z = 0.0
        # Planar odometry uses yaw only. Full roll/pitch remains on /imu/data.
        yaw_only = quaternion_from_rpy(0.0, 0.0, relative_yaw)
        (odom.pose.pose.orientation.x, odom.pose.pose.orientation.y,
         odom.pose.pose.orientation.z, odom.pose.pose.orientation.w) = yaw_only
        (odom.twist.twist.linear.x, odom.twist.twist.linear.y,
         odom.twist.twist.angular.z) = data["velocity_body"]
        self.odom_pub.publish(odom)

        transform = TransformStamped()
        transform.header = odom.header
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = odom.pose.pose.position.x
        transform.transform.translation.y = odom.pose.pose.position.y
        transform.transform.rotation = odom.pose.pose.orientation
        self.tf.sendTransform(transform)
        self.state_pub.publish(Int32(data=data["basic_state"]))
        self.battery_pub.publish(Float32(data=data["battery"]))
        self._publish_fresh(True)

    def _publish_joints(self, positions):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.base_frame
        msg.name = list(JOINT_NAMES)
        msg.position = list(positions)
        # High-level packets contain no joint velocity, effort or covariance.
        self.joint_pub.publish(msg)
        self.joint_packets += 1

    def _publish_fresh(self, value):
        if value != self.last_fresh_value:
            self.fresh_pub.publish(Bool(data=value))
            self.last_fresh_value = value

    def _freshness(self):
        fresh = feedback_is_fresh(
            self.last_robot_state, time.monotonic(), self.stale_timeout)
        self._publish_fresh(fresh)

    def _report_rate(self):
        elapsed = time.monotonic() - self.rate_start
        self.get_logger().info(
            f"high-level telemetry rates: RobotState={self.robot_packets / elapsed:.1f} Hz "
            f"JointState={self.joint_packets / elapsed:.1f} Hz"
        )
        self.robot_packets = self.joint_packets = 0
        self.rate_start = time.monotonic()

    def destroy_node(self):
        self.sock.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HighLevelStateBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception:
        # SIGTERM may invalidate the ROS context between a timer callback and
        # publish(). Treat that shutdown race as clean, but never hide a live
        # runtime failure.
        if rclpy.ok():
            raise
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
