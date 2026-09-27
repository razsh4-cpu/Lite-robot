#!/usr/bin/env python3
"""Passive terminal dashboard for Lite3 ROS control and health topics."""

import signal
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Bool, Float32, Int32, String


class Dashboard(Node):
    def __init__(self):
        super().__init__("lite3_operator_dashboard")
        self.values = {
            "source": "unknown", "cmd": (0.0, 0.0), "deadman": False,
            "enabled": False, "reason": "no_data", "state": None,
            "battery": None, "telemetry": False,
        }
        self.updated = {}
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST, depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(
            String, "/lite3/active_command_source",
            lambda m: self.set("source", m.data), qos)
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd, qos)
        self.create_subscription(
            Bool, "/lite3/cmd_vel_deadman",
            lambda m: self.set("deadman", bool(m.data)), qos)
        self.create_subscription(
            Bool, "/lite3/control_enabled",
            lambda m: self.set("enabled", bool(m.data)), qos)
        self.create_subscription(
            String, "/lite3/control_reason",
            lambda m: self.set("reason", m.data), qos)
        self.create_subscription(
            Int32, "/lite3/robot_basic_state",
            lambda m: self.set("state", int(m.data)), qos)
        self.create_subscription(
            Float32, "/lite3/battery_percent",
            lambda m: self.set("battery", float(m.data)), qos)
        self.create_subscription(
            Bool, "/lite3/robot_state_fresh",
            lambda m: self.set("telemetry", bool(m.data)), qos)
        self.create_timer(1.0, self.report)
        self.get_logger().info("Passive operator dashboard started")

    def set(self, key, value):
        self.values[key] = value
        self.updated[key] = time.monotonic()

    def on_cmd(self, msg):
        self.set("cmd", (float(msg.linear.x), float(msg.angular.z)))

    def report(self):
        battery = self.values["battery"]
        battery_text = "unknown" if battery is None else f"{battery:.0f}%"
        forward, yaw = self.values["cmd"]
        age = (
            "n/a" if "telemetry" not in self.updated
            else f"{time.monotonic() - self.updated['telemetry']:.2f}s"
        )
        self.get_logger().info(
            f"source={self.values['source']} state={self.values['state']} "
            f"battery={battery_text} telemetry={self.values['telemetry']} age={age} "
            f"deadman={self.values['deadman']} enabled={self.values['enabled']} "
            f"reason={self.values['reason']} cmd=({forward:+.3f},0,{yaw:+.3f})"
        )


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    node = Dashboard()
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
