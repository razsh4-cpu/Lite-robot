#!/usr/bin/env python3
"""Fail-closed terminal keyboard source for the Lite3 command arbiter.

Hold W/S for forward/back or A/D for yaw. Terminal key-repeat refreshes the
command; absence of a key event for 250 ms forces zero/deadman false. SPACE is
an explicit stop and Q exits. This node has no robot socket.
"""

import math
import select
import signal
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Bool


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__("lite3_keyboard_cmd_vel")
        self.declare_parameter("forward", 0.10)
        self.declare_parameter("yaw", 0.25)
        self.declare_parameter("key_timeout_ms", 250)
        self.forward = min(0.10, abs(float(self.get_parameter("forward").value)))
        self.yaw = min(0.25, abs(float(self.get_parameter("yaw").value)))
        self.timeout = int(self.get_parameter("key_timeout_ms").value) / 1000.0
        if not all(math.isfinite(v) for v in (self.forward, self.yaw)):
            raise ValueError("keyboard limits must be finite")
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST, depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT)
        self.cmd_pub = self.create_publisher(
            Twist, "/lite3/keyboard/cmd_vel", qos)
        self.deadman_pub = self.create_publisher(
            Bool, "/lite3/keyboard/deadman", qos)
        self.command = Twist()
        self.last_key = None
        self.stop_requested = False
        # A ROS launch child normally receives /dev/null as stdin. Open the
        # operator's controlling terminal explicitly so the same safe keyboard
        # node works both via `ros2 run` and from the unified launch file.
        self.tty = open("/dev/tty", "r", encoding="utf-8", buffering=1)
        self.create_timer(0.02, self.read_keys)
        self.create_timer(0.05, self.publish)
        self.settings = termios.tcgetattr(self.tty)
        tty.setcbreak(self.tty.fileno())
        self.get_logger().warning("Keyboard: hold W/S or A/D; SPACE stop; Q quit")

    def read_keys(self):
        while select.select([self.tty], [], [], 0.0)[0]:
            key = self.tty.read(1).lower()
            command = Twist()
            if key == "w":
                command.linear.x = self.forward
            elif key == "s":
                command.linear.x = -self.forward
            elif key == "a":
                command.angular.z = self.yaw
            elif key == "d":
                command.angular.z = -self.yaw
            elif key == "q":
                self.stop_requested = True
            elif key != " ":
                continue
            self.command = command
            self.last_key = time.monotonic() if key != " " else None

    def publish(self):
        enabled = (
            self.last_key is not None
            and time.monotonic() - self.last_key <= self.timeout
            and not self.stop_requested
        )
        self.cmd_pub.publish(self.command if enabled else Twist())
        self.deadman_pub.publish(Bool(data=enabled))
        if self.stop_requested:
            raise KeyboardInterrupt

    def close(self):
        for _ in range(5):
            self.cmd_pub.publish(Twist())
            self.deadman_pub.publish(Bool(data=False))
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(0.02)
        termios.tcsetattr(self.tty, termios.TCSADRAIN, self.settings)
        self.tty.close()


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    node = KeyboardTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
