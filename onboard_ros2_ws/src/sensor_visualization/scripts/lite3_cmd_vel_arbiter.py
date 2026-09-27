#!/usr/bin/env python3
"""Fail-closed single-source arbiter for Xbox, keyboard, and future Nav2."""

from __future__ import annotations

import math
import signal
import time
from dataclasses import dataclass, field
from typing import Optional


SOURCES = ("xbox", "keyboard", "nav2")


@dataclass
class SourceState:
    forward: float = 0.0
    lateral: float = 0.0
    yaw: float = 0.0
    command_time: Optional[float] = None
    command_valid: bool = False
    deadman: bool = False
    deadman_time: Optional[float] = None


@dataclass
class ArbiterOutput:
    enabled: bool
    forward: float
    lateral: float
    yaw: float
    source: str
    reason: str


class ArbiterCore:
    def __init__(self, timeout_s=0.300, selected="none"):
        if not 0.05 <= timeout_s <= 1.0:
            raise ValueError("timeout must be within [0.05, 1.0]")
        self.timeout_s = timeout_s
        self.states = {name: SourceState() for name in SOURCES}
        self.selected = "none"
        self.select(selected)

    def select(self, source):
        if source not in (*SOURCES, "none"):
            return False
        self.selected = source
        return True

    def update_command(self, source, forward, lateral, yaw, now):
        state = self.states[source]
        state.command_time = now
        values = (forward, lateral, yaw)
        state.command_valid = all(math.isfinite(value) for value in values)
        if state.command_valid:
            state.forward, state.lateral, state.yaw = map(float, values)
        else:
            state.forward = state.lateral = state.yaw = 0.0

    def update_deadman(self, source, enabled, now):
        state = self.states[source]
        state.deadman = bool(enabled)
        state.deadman_time = now

    def output(self, now):
        if self.selected == "none":
            return ArbiterOutput(False, 0.0, 0.0, 0.0, "none", "no_source")
        state = self.states[self.selected]
        if state.deadman_time is None or now - state.deadman_time > self.timeout_s:
            return ArbiterOutput(False, 0.0, 0.0, 0.0, self.selected, "deadman_stale")
        if not state.deadman:
            return ArbiterOutput(False, 0.0, 0.0, 0.0, self.selected, "deadman_released")
        if state.command_time is None or now - state.command_time > self.timeout_s:
            return ArbiterOutput(False, 0.0, 0.0, 0.0, self.selected, "command_stale")
        if not state.command_valid:
            return ArbiterOutput(False, 0.0, 0.0, 0.0, self.selected, "command_invalid")
        return ArbiterOutput(
            True, state.forward, state.lateral, state.yaw, self.selected, "enabled"
        )


def main():
    import rclpy
    from geometry_msgs.msg import Twist
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from rclpy.signals import SignalHandlerOptions
    from std_msgs.msg import Bool, String

    class ArbiterNode(Node):
        def __init__(self):
            super().__init__("lite3_cmd_vel_arbiter")
            self.declare_parameter("timeout_ms", 300)
            self.declare_parameter("selected_source", "none")
            self.core = ArbiterCore(
                int(self.get_parameter("timeout_ms").value) / 1000.0,
                str(self.get_parameter("selected_source").value),
            )
            qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                reliability=ReliabilityPolicy.BEST_EFFORT,
            )
            self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", qos)
            self.deadman_pub = self.create_publisher(
                Bool, "/lite3/cmd_vel_deadman", qos
            )
            self.source_pub = self.create_publisher(
                String, "/lite3/active_command_source", qos
            )
            self.create_subscription(
                String, "/lite3/select_command_source", self.on_select, qos
            )
            for source in SOURCES:
                self.create_subscription(
                    Twist,
                    f"/lite3/{source}/cmd_vel",
                    lambda message, source=source: self.on_command(source, message),
                    qos,
                )
                self.create_subscription(
                    Bool,
                    f"/lite3/{source}/deadman",
                    lambda message, source=source: self.on_deadman(source, message),
                    qos,
                )
            self.create_timer(0.05, self.on_timer)
            self.last_report = None
            self.get_logger().warning(
                f"Command arbiter selected_source={self.core.selected}; "
                "all unselected sources are ignored"
            )

        def on_select(self, message):
            previous = self.core.selected
            if not self.core.select(str(message.data)):
                self.get_logger().error(f"Rejected unknown command source: {message.data}")
                return
            self.publish_zero()
            self.get_logger().warning(
                f"Command source changed {previous} -> {self.core.selected}; output zeroed"
            )

        def on_command(self, source, message):
            self.core.update_command(
                source, message.linear.x, message.linear.y, message.angular.z,
                time.monotonic(),
            )

        def on_deadman(self, source, message):
            self.core.update_deadman(source, message.data, time.monotonic())

        def publish_zero(self):
            self.cmd_pub.publish(Twist())
            self.deadman_pub.publish(Bool(data=False))

        def on_timer(self):
            output = self.core.output(time.monotonic())
            command = Twist()
            if output.enabled:
                command.linear.x = output.forward
                command.linear.y = output.lateral
                command.angular.z = output.yaw
            self.cmd_pub.publish(command)
            self.deadman_pub.publish(Bool(data=output.enabled))
            self.source_pub.publish(String(data=output.source))
            report = (output.enabled, output.source, output.reason)
            if report != self.last_report:
                self.get_logger().info(
                    f"enabled={str(output.enabled).lower()} source={output.source} "
                    f"reason={output.reason}"
                )
                self.last_report = report

        def close(self):
            for _ in range(5):
                self.publish_zero()
                rclpy.spin_once(self, timeout_sec=0.0)
                time.sleep(0.02)

    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    node = ArbiterNode()
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
