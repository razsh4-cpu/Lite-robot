#!/usr/bin/env python3
"""One explicitly approved Stand edge through the existing C2 relay."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
from pathlib import Path
import subprocess
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool

STATE = Path("/run/lite3-control/COMMAND_SOURCE")
PREFIX = "/c2/robot_01/laptop_xbox"


def owner():
    try:
        return STATE.read_text().strip()
    except OSError:
        return "UNKNOWN"


def standing_confirmed():
    result = subprocess.run(
        ["journalctl", "--no-pager", "--since", "30 seconds ago",
         "-u", "lite3-high-level-runtime.service"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=3, check=False)
    return "robot_status=standing" in result.stdout and "telemetry_fresh=true" in result.stdout


class StandRequest(Node):
    def __init__(self):
        super().__init__("lite3_explicit_stand_once")
        self.request = self.create_publisher(Bool, PREFIX + "/request", 10)
        self.heartbeat = self.create_publisher(Bool, PREFIX + "/heartbeat", 10)
        self.joy = self.create_publisher(Joy, PREFIX + "/joy", 10)

    def publish(self, enabled, a=False):
        self.request.publish(Bool(data=enabled))
        self.heartbeat.publish(Bool(data=enabled))
        message = Joy()
        message.axes = [0.0] * 8
        message.buttons = [0] * 15
        message.buttons[0] = 1 if a else 0
        self.joy.publish(message)

    def cycle(self, duration, enabled=True, a=False):
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            self.publish(enabled, a)
            rclpy.spin_once(self, timeout_sec=0.02)
            time.sleep(0.03)


def main():
    if owner() != "NONE":
        raise SystemExit(f"STAND BLOCKED: COMMAND_SOURCE={owner()}")
    rclpy.init()
    node = StandRequest()
    try:
        deadline = time.monotonic() + 30.0
        while owner() != "LAPTOP_XBOX" and time.monotonic() < deadline:
            node.publish(True, False)
            rclpy.spin_once(node, timeout_sec=0.02)
            time.sleep(0.03)
        if owner() != "LAPTOP_XBOX":
            raise SystemExit("STAND BLOCKED: C2 lease was not acquired")
        node.cycle(0.6, True, False)
        node.cycle(0.35, True, True)
        node.cycle(0.6, True, False)
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            node.cycle(0.25, True, False)
            if standing_confirmed():
                print("STAND CONFIRMED: telemetry robot_status=standing")
                return
        raise SystemExit("STAND FAILED: standing telemetry was not confirmed")
    finally:
        for _ in range(8):
            node.publish(False, False)
            rclpy.spin_once(node, timeout_sec=0.03)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
