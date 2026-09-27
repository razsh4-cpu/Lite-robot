#!/usr/bin/env python3
"""Fail-closed ROS Twist adapter for the proven Lite3 manual-axis node.

This process has no socket and cannot communicate with the robot directly. It
converts a fresh, explicitly enabled ``/cmd_vel`` stream into the normalized
forward/yaw topics consumed by ``lite3_manual_axis_control``. Lateral motion is
intentionally unsupported and always resolves to zero.
"""

from __future__ import annotations

import argparse
import math
import signal
import sys
import time
from dataclasses import dataclass
from typing import Optional


HARD_MAX_FORWARD = 0.10
HARD_MAX_YAW = 0.25


@dataclass
class AdapterState:
    forward: float = 0.0
    yaw: float = 0.0
    command_valid: bool = False
    command_time: Optional[float] = None
    deadman: bool = False
    deadman_time: Optional[float] = None


class CmdVelCore:
    def __init__(
        self,
        timeout_s: float,
        forward_gain: float,
        yaw_gain: float,
        max_forward: float,
        max_yaw: float,
    ):
        if not 0.05 <= timeout_s <= 1.0:
            raise ValueError("timeout must be within [0.05, 1.0] seconds")
        if not math.isfinite(forward_gain) or forward_gain <= 0.0:
            raise ValueError("forward gain must be finite and positive")
        if not math.isfinite(yaw_gain) or yaw_gain <= 0.0:
            raise ValueError("yaw gain must be finite and positive")
        if not 0.0 < max_forward <= HARD_MAX_FORWARD:
            raise ValueError(f"max_forward must be within (0, {HARD_MAX_FORWARD}]")
        if not 0.0 < max_yaw <= HARD_MAX_YAW:
            raise ValueError(f"max_yaw must be within (0, {HARD_MAX_YAW}]")
        self.timeout_s = timeout_s
        self.forward_gain = forward_gain
        self.yaw_gain = yaw_gain
        self.max_forward = max_forward
        self.max_yaw = max_yaw
        self.state = AdapterState()

    def update_command(
        self, linear_x: float, linear_y: float, angular_z: float, now: float
    ) -> None:
        values = (linear_x, linear_y, angular_z)
        self.state.command_time = now
        if not all(math.isfinite(value) for value in values):
            self.state.forward = 0.0
            self.state.yaw = 0.0
            self.state.command_valid = False
            return
        self.state.forward = max(
            -self.max_forward,
            min(self.max_forward, linear_x * self.forward_gain),
        )
        self.state.yaw = max(
            -self.max_yaw,
            min(self.max_yaw, angular_z * self.yaw_gain),
        )
        self.state.command_valid = True

    def update_deadman(self, enabled: bool, now: float) -> None:
        self.state.deadman = bool(enabled)
        self.state.deadman_time = now

    def output(self, now: float) -> tuple[bool, float, float, str]:
        state = self.state
        if state.deadman_time is None or now - state.deadman_time > self.timeout_s:
            return False, 0.0, 0.0, "deadman_stale"
        if not state.deadman:
            return False, 0.0, 0.0, "deadman_released"
        if state.command_time is None or now - state.command_time > self.timeout_s:
            return False, 0.0, 0.0, "cmd_vel_stale"
        if not state.command_valid:
            return False, 0.0, 0.0, "cmd_vel_invalid"
        return True, state.forward, state.yaw, "enabled"


def run_self_test() -> int:
    core = CmdVelCore(0.3, 1.0, 1.0, 0.10, 0.25)
    assert core.output(1.0) == (False, 0.0, 0.0, "deadman_stale")
    core.update_command(1.0, 9.0, -1.0, 1.0)
    core.update_deadman(True, 1.0)
    assert core.output(1.0) == (True, 0.10, -0.25, "enabled")
    # Lateral is accepted only for finite-value validation and never output.
    core.update_command(0.04, -100.0, 0.12, 1.1)
    assert core.output(1.1) == (True, 0.04, 0.12, "enabled")
    core.update_deadman(False, 1.2)
    assert core.output(1.2) == (False, 0.0, 0.0, "deadman_released")
    core.update_deadman(True, 2.0)
    core.update_command(math.nan, 0.0, 0.0, 2.0)
    assert core.output(2.0) == (False, 0.0, 0.0, "cmd_vel_invalid")
    core.update_command(0.10, 0.0, 0.25, 3.0)
    core.update_deadman(True, 3.0)
    assert core.output(3.301) == (False, 0.0, 0.0, "deadman_stale")
    print(
        "SELF_TEST_PASS cmd_vel_fail_closed=YES lateral_forced_zero=YES "
        "forward_limit=0.10 yaw_limit=0.25"
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
    from std_msgs.msg import Bool, Float32

    class CmdVelAdapterNode(Node):
        def __init__(self):
            super().__init__("lite3_cmd_vel_adapter")
            self.declare_parameter("timeout_ms", 300)
            self.declare_parameter("forward_normalized_per_mps", 1.0)
            self.declare_parameter("yaw_normalized_per_radps", 1.0)
            self.declare_parameter("max_forward_normalized", 0.10)
            self.declare_parameter("max_yaw_normalized", 0.25)
            timeout_s = int(self.get_parameter("timeout_ms").value) / 1000.0
            self.core = CmdVelCore(
                timeout_s,
                float(self.get_parameter("forward_normalized_per_mps").value),
                float(self.get_parameter("yaw_normalized_per_radps").value),
                float(self.get_parameter("max_forward_normalized").value),
                float(self.get_parameter("max_yaw_normalized").value),
            )
            qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                reliability=ReliabilityPolicy.BEST_EFFORT,
            )
            self.forward_pub = self.create_publisher(
                Float32, "/lite3/manual_forward_normalized", qos
            )
            self.yaw_pub = self.create_publisher(
                Float32, "/lite3/manual_yaw_normalized", qos
            )
            self.deadman_pub = self.create_publisher(
                Bool, "/lite3/manual_axis_deadman", qos
            )
            self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, qos)
            self.create_subscription(
                Bool, "/lite3/cmd_vel_deadman", self.on_deadman, qos
            )
            self.timer = self.create_timer(0.05, self.on_timer)
            self.last_report = None
            self.last_report_time = 0.0
            self.lateral_warning_time = 0.0
            self.get_logger().warning(
                "ROS-only /cmd_vel adapter started disabled; deadman required; "
                "linear.y is forced to zero"
            )

        def on_cmd_vel(self, message: Twist) -> None:
            now = time.monotonic()
            lateral = float(message.linear.y)
            if math.isfinite(lateral) and abs(lateral) > 1e-6:
                if now - self.lateral_warning_time >= 2.0:
                    self.get_logger().warning("Ignoring nonzero linear.y; lateral=0")
                    self.lateral_warning_time = now
            self.core.update_command(
                float(message.linear.x), lateral, float(message.angular.z), now
            )

        def on_deadman(self, message: Bool) -> None:
            self.core.update_deadman(bool(message.data), time.monotonic())

        def publish(self, enabled: bool, forward: float, yaw: float) -> None:
            self.forward_pub.publish(Float32(data=forward if enabled else 0.0))
            self.yaw_pub.publish(Float32(data=yaw if enabled else 0.0))
            self.deadman_pub.publish(Bool(data=enabled))

        def on_timer(self) -> None:
            now = time.monotonic()
            enabled, forward, yaw, reason = self.core.output(now)
            self.publish(enabled, forward, yaw)
            report = (enabled, reason, round(forward, 6), round(yaw, 6))
            if report != self.last_report or now - self.last_report_time >= 2.0:
                self.get_logger().info(
                    f"enabled={str(enabled).lower()} reason={reason} "
                    f"forward={forward if enabled else 0.0:+.6f} "
                    f"lateral=+0.000000 yaw={yaw if enabled else 0.0:+.6f}"
                )
                self.last_report = report
                self.last_report_time = now

        def close(self) -> None:
            for _ in range(5):
                self.publish(False, 0.0, 0.0)
                rclpy.spin_once(self, timeout_sec=0.0)
                time.sleep(0.02)

    # Keep the ROS context valid until the final fail-closed publications have
    # completed. The default rclpy handler shuts the context down before our
    # finally block can publish them.
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def request_clean_shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, request_clean_shutdown)
    signal.signal(signal.SIGTERM, request_clean_shutdown)
    node = CmdVelAdapterNode()
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
