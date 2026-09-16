#!/usr/bin/env python3
"""Fail-closed Xbox /joy to /cmd_vel teleop for the Lite3 vendor-gait chain.

This node is ROS-only: it owns no network socket and cannot contact the robot.
Robot telemetry, state, battery, and UDP safety gates remain in the downstream
``lite3_manual_axis_control`` node.
"""

from __future__ import annotations

import argparse
import math
import signal
import sys
import time
from dataclasses import dataclass
from typing import Optional, Sequence


AXIS_LATERAL = 0
AXIS_FORWARD = 1
AXIS_YAW = 2
BUTTON_DEADMAN = 10  # RB


@dataclass
class TeleopOutput:
    enabled: bool
    forward: float
    yaw: float
    reason: str


class XboxTeleopCore:
    def __init__(
        self,
        timeout_s: float = 0.300,
        deadzone: float = 0.05,
        max_forward: float = 0.10,
        max_yaw: float = 0.25,
    ):
        if not 0.05 <= timeout_s <= 1.0:
            raise ValueError("timeout_s must be within [0.05, 1.0]")
        if not 0.0 <= deadzone < 0.5:
            raise ValueError("deadzone must be within [0.0, 0.5)")
        if not 0.0 < max_forward <= 0.10:
            raise ValueError("max_forward must be within (0.0, 0.10]")
        if not 0.0 < max_yaw <= 0.25:
            raise ValueError("max_yaw must be within (0.0, 0.25]")
        self.timeout_s = timeout_s
        self.deadzone = deadzone
        self.max_forward = max_forward
        self.max_yaw = max_yaw
        self.last_joy_time: Optional[float] = None
        self.joy_valid = False
        self.deadman = False
        self.forward = 0.0
        self.yaw = 0.0

    def shape(self, value: float) -> float:
        if not math.isfinite(value):
            return 0.0
        value = max(-1.0, min(1.0, float(value)))
        magnitude = abs(value)
        if magnitude <= self.deadzone:
            return 0.0
        shaped = (magnitude - self.deadzone) / (1.0 - self.deadzone)
        return math.copysign(min(1.0, shaped), value)

    def update(self, axes: Sequence[float], buttons: Sequence[int], now: float) -> None:
        self.last_joy_time = now
        self.joy_valid = False
        self.deadman = False
        self.forward = 0.0
        self.yaw = 0.0

        if len(axes) <= max(AXIS_LATERAL, AXIS_FORWARD, AXIS_YAW):
            return
        if len(buttons) <= BUTTON_DEADMAN:
            return
        raw_axes = (axes[AXIS_LATERAL], axes[AXIS_FORWARD], axes[AXIS_YAW])
        if not all(math.isfinite(value) for value in raw_axes):
            return
        if buttons[BUTTON_DEADMAN] not in (0, 1):
            return

        self.joy_valid = True
        self.deadman = bool(buttons[BUTTON_DEADMAN])
        self.forward = self.shape(axes[AXIS_FORWARD]) * self.max_forward
        # Lateral is deliberately ignored. Positive ROS yaw is preserved here;
        # the proven vendor adapter performs the required wire-level inversion.
        self.yaw = self.shape(axes[AXIS_YAW]) * self.max_yaw

    def output(self, now: float) -> TeleopOutput:
        if self.last_joy_time is None or now - self.last_joy_time > self.timeout_s:
            return TeleopOutput(False, 0.0, 0.0, "joy_stale")
        if not self.joy_valid:
            return TeleopOutput(False, 0.0, 0.0, "joy_invalid")
        if not self.deadman:
            return TeleopOutput(False, 0.0, 0.0, "rb_released")
        return TeleopOutput(True, self.forward, self.yaw, "enabled")


def run_self_test() -> int:
    core = XboxTeleopCore()
    assert core.output(0.0).reason == "joy_stale"
    axes = [0.0] * 6
    buttons = [0] * 15
    axes[AXIS_FORWARD] = 1.0
    axes[AXIS_LATERAL] = 1.0
    axes[AXIS_YAW] = -1.0
    core.update(axes, buttons, 1.0)
    assert core.output(1.0) == TeleopOutput(False, 0.0, 0.0, "rb_released")
    buttons[BUTTON_DEADMAN] = 1
    core.update(axes, buttons, 2.0)
    assert core.output(2.0) == TeleopOutput(True, 0.10, -0.25, "enabled")
    # Lateral input never reaches Twist.linear.y.
    assert not hasattr(core.output(2.0), "lateral")
    assert core.output(2.301).reason == "joy_stale"
    core.update([0.0], [0], 3.0)
    assert core.output(3.0).reason == "joy_invalid"
    axes[AXIS_FORWARD] = math.nan
    core.update(axes, buttons, 4.0)
    assert core.output(4.0).reason == "joy_invalid"
    print(
        "SELF_TEST_PASS rb_deadman=YES joy_timeout=300ms deadzone=5% "
        "forward_limit=0.10 yaw_limit=0.25 lateral_forced_zero=YES"
    )
    print("ROBOT_PACKETS_SENT=0")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--self-test", action="store_true")
        parser.parse_args()
        return run_self_test()

    import rclpy
    from geometry_msgs.msg import Twist
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from rclpy.signals import SignalHandlerOptions
    from sensor_msgs.msg import Joy
    from std_msgs.msg import Bool

    class XboxCmdVelTeleopNode(Node):
        def __init__(self):
            super().__init__("lite3_xbox_cmd_vel_teleop")
            self.declare_parameter("timeout_ms", 300)
            self.declare_parameter("deadzone", 0.05)
            self.declare_parameter("max_forward", 0.10)
            self.declare_parameter("max_yaw", 0.25)
            self.declare_parameter("cmd_vel_topic", "/cmd_vel")
            self.declare_parameter(
                "deadman_topic", "/lite3/cmd_vel_deadman"
            )
            self.core = XboxTeleopCore(
                int(self.get_parameter("timeout_ms").value) / 1000.0,
                float(self.get_parameter("deadzone").value),
                float(self.get_parameter("max_forward").value),
                float(self.get_parameter("max_yaw").value),
            )
            qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                reliability=ReliabilityPolicy.BEST_EFFORT,
            )
            cmd_vel_topic = str(self.get_parameter("cmd_vel_topic").value)
            deadman_topic = str(self.get_parameter("deadman_topic").value)
            self.cmd_pub = self.create_publisher(Twist, cmd_vel_topic, qos)
            self.deadman_pub = self.create_publisher(
                Bool, deadman_topic, qos
            )
            self.create_subscription(Joy, "/joy", self.on_joy, qos)
            self.timer = self.create_timer(0.05, self.on_timer)
            self.last_report = None
            self.last_report_time = 0.0
            self.get_logger().warning(
                "Xbox teleop starts disabled: hold RB to enable; "
                "left-Y=forward, right-X=yaw, lateral forced zero"
            )

        def on_joy(self, message: Joy) -> None:
            self.core.update(message.axes, message.buttons, time.monotonic())

        def publish(self, output: TeleopOutput) -> None:
            command = Twist()
            if output.enabled:
                command.linear.x = output.forward
                command.angular.z = output.yaw
            # linear.y and every unused component remain exactly zero.
            self.cmd_pub.publish(command)
            self.deadman_pub.publish(Bool(data=output.enabled))

        def on_timer(self) -> None:
            now = time.monotonic()
            output = self.core.output(now)
            self.publish(output)
            report = (
                output.enabled,
                output.reason,
                round(output.forward, 5),
                round(output.yaw, 5),
            )
            if report != self.last_report or now - self.last_report_time >= 2.0:
                self.get_logger().info(
                    f"enabled={str(output.enabled).lower()} reason={output.reason} "
                    f"linear.x={output.forward:+.3f} linear.y=+0.000 "
                    f"angular.z={output.yaw:+.3f}"
                )
                self.last_report = report
                self.last_report_time = now

        def close(self) -> None:
            zero = TeleopOutput(False, 0.0, 0.0, "shutdown")
            for _ in range(5):
                self.publish(zero)
                rclpy.spin_once(self, timeout_sec=0.0)
                time.sleep(0.02)

    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def request_clean_shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, request_clean_shutdown)
    signal.signal(signal.SIGTERM, request_clean_shutdown)
    node = XboxCmdVelTeleopNode()
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
