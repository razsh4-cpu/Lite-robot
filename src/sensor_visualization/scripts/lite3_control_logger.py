#!/usr/bin/env python3
"""Passive JSONL experiment logger for the Lite3 ROS control stack.

The logger only subscribes. It has no publishers, sockets, SDK imports, or
robot-control code.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import signal
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Bool, Float32, Int32, String


class Lite3ControlLogger(Node):
    def __init__(self):
        super().__init__("lite3_control_logger")
        self.declare_parameter("output_directory", "/home/abx/ros2_ws/logs")
        self.declare_parameter("snapshot_hz", 10.0)
        output_dir = Path(str(self.get_parameter("output_directory").value))
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.path = output_dir / f"lite3_control_{stamp}.jsonl"
        self.file = self.path.open("x", encoding="utf-8")
        self.values = {
            "cmd_vel": None,
            "normalized_forward": None,
            "normalized_yaw": None,
            "deadman": None,
            "control_enabled": None,
            "control_reason": None,
            "active_command_source": None,
            "robot_basic_state": None,
            "battery_percent": None,
            "robot_state_fresh": None,
            "odom": None,
        }
        self.updated = {}
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd, qos)
        self.create_subscription(
            Float32, "/lite3/manual_forward_normalized",
            lambda m: self.set_value("normalized_forward", float(m.data)), qos)
        self.create_subscription(
            Float32, "/lite3/manual_yaw_normalized",
            lambda m: self.set_value("normalized_yaw", float(m.data)), qos)
        self.create_subscription(
            Bool, "/lite3/manual_axis_deadman",
            lambda m: self.set_value("deadman", bool(m.data)), qos)
        self.create_subscription(
            Bool, "/lite3/control_enabled",
            lambda m: self.set_value("control_enabled", bool(m.data)), qos)
        self.create_subscription(
            String, "/lite3/control_reason",
            lambda m: self.set_value("control_reason", str(m.data)), qos)
        self.create_subscription(
            String, "/lite3/active_command_source",
            lambda m: self.set_value("active_command_source", str(m.data)), qos)
        self.create_subscription(
            Int32, "/lite3/robot_basic_state",
            lambda m: self.set_value("robot_basic_state", int(m.data)), qos)
        self.create_subscription(
            Float32, "/lite3/battery_percent",
            lambda m: self.set_value("battery_percent", float(m.data)), qos)
        self.create_subscription(
            Bool, "/lite3/robot_state_fresh",
            lambda m: self.set_value("robot_state_fresh", bool(m.data)), qos)
        self.create_subscription(Odometry, "/odom", self.on_odom, qos)
        hz = float(self.get_parameter("snapshot_hz").value)
        if not 1.0 <= hz <= 50.0:
            raise ValueError("snapshot_hz must be within [1, 50]")
        self.create_timer(1.0 / hz, self.snapshot)
        self.get_logger().info(f"Passive control logger: {self.path}")

    def set_value(self, name, value):
        self.values[name] = value
        self.updated[name] = time.monotonic()

    def on_cmd(self, msg):
        self.set_value("cmd_vel", {
            "linear_x": float(msg.linear.x),
            "linear_y": float(msg.linear.y),
            "angular_z": float(msg.angular.z),
        })

    def on_odom(self, msg):
        q = msg.pose.pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        self.set_value("odom", {
            "stamp": msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
            "frame_id": msg.header.frame_id,
            "child_frame_id": msg.child_frame_id,
            "x": float(msg.pose.pose.position.x),
            "y": float(msg.pose.pose.position.y),
            "yaw": yaw,
            "linear_x": float(msg.twist.twist.linear.x),
            "linear_y": float(msg.twist.twist.linear.y),
            "angular_z": float(msg.twist.twist.angular.z),
        })

    def snapshot(self):
        now_mono = time.monotonic()
        row = {
            "wall_time": time.time(),
            "monotonic_time": now_mono,
            **self.values,
            "age_s": {
                key: round(now_mono - value, 6)
                for key, value in self.updated.items()
            },
        }
        self.file.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
        self.file.flush()

    def destroy_node(self):
        if not self.file.closed:
            self.file.flush()
            self.file.close()
        return super().destroy_node()


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def request_clean_shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, request_clean_shutdown)
    signal.signal(signal.SIGTERM, request_clean_shutdown)
    node = Lite3ControlLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
