#!/usr/bin/env python3
"""ROS graph integration test; intentionally omits the UDP/manual-axis node."""

import os
import signal
import subprocess
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool, Float32


def start(executable, parameters=()):
    command = ["ros2", "run", "sensor_visualization", executable]
    if parameters:
        command += ["--ros-args"]
        for name, value in parameters:
            command += ["-p", f"{name}:={value}"]
    return subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        start_new_session=True)


class Probe(Node):
    def __init__(self):
        super().__init__("lite3_ros_chain_offline_probe")
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST, depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT)
        self.joy = self.create_publisher(Joy, "/joy", qos)
        self.forward = None
        self.yaw = None
        self.deadman = None
        self.create_subscription(
            Float32, "/lite3/manual_forward_normalized",
            lambda m: setattr(self, "forward", float(m.data)), qos)
        self.create_subscription(
            Float32, "/lite3/manual_yaw_normalized",
            lambda m: setattr(self, "yaw", float(m.data)), qos)
        self.create_subscription(
            Bool, "/lite3/manual_axis_deadman",
            lambda m: setattr(self, "deadman", bool(m.data)), qos)


def spin_for(node, seconds, publish=False):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if publish:
            message = Joy()
            message.axes = [0.0, 1.0, 0.4, 0.0, 0.0, 0.0]
            message.buttons = [0] * 15
            message.buttons[10] = 1
            node.joy.publish(message)
        rclpy.spin_once(node, timeout_sec=0.02)


def main():
    children = []
    # No lite3_manual_axis_control is started: this test cannot create robot UDP.
    children.append(start("lite3_xbox_cmd_vel_teleop", (
        ("cmd_vel_topic", "/lite3/xbox/cmd_vel"),
        ("deadman_topic", "/lite3/xbox/deadman"))))
    children.append(start("lite3_cmd_vel_arbiter", (
        ("selected_source", "xbox"),)))
    children.append(start("lite3_cmd_vel_adapter"))
    rclpy.init()
    node = Probe()
    try:
        spin_for(node, 1.0)
        spin_for(node, 1.2, publish=True)
        assert node.deadman is True
        assert node.forward is not None and abs(node.forward - 0.10) < 1e-5
        expected_yaw = (0.4 - 0.05) / 0.95 * 0.25
        assert node.yaw is not None and abs(node.yaw - expected_yaw) < 1e-5
        spin_for(node, 0.75, publish=False)
        assert node.deadman is False
        assert node.forward == 0.0
        assert node.yaw == 0.0
        print("ROS_CHAIN_TEST=PASS")
        print("ACTIVE_FORWARD=0.10")
        print(f"ACTIVE_YAW={expected_yaw:.6f}")
        print("STALE_JOY_OUTPUT=ZERO")
        print("MANUAL_AXIS_UDP_NODE_STARTED=NO")
        print("ROBOT_PACKETS_SENT=0")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGINT)
        deadline = time.monotonic() + 3.0
        for child in children:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=2.0)


if __name__ == "__main__":
    main()
