#!/usr/bin/env python3
"""Safe Xbox teleop dry run.

This node only subscribes to sensor_msgs/msg/Joy and logs computed normalized
forward, lateral, and yaw values.  It has no publishers, sockets, Lite3 SDK
imports, or robot-control code.
"""

import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy


class XboxTeleopDryRun(Node):
    """Turn verified Xbox /joy inputs into safe, log-only motion values."""

    AXIS_LATERAL = 0
    AXIS_FORWARD = 1
    AXIS_YAW = 2
    BUTTON_DEADMAN = 10  # RB
    DEADZONE = 0.05
    JOY_TIMEOUT_S = 0.300

    def __init__(self):
        super().__init__('xbox_teleop_dry_run')
        self._last_valid_joy_time = None
        self._last_values = (0.0, 0.0, 0.0)
        self._deadman_held = False
        self._invalid_message = False
        self._last_report = None
        self.create_subscription(Joy, '/joy', self._on_joy, 10)
        # Fixed 2 Hz reporting rate prevents callback-rate log spam.
        self.create_timer(0.5, self._report)
        self.get_logger().info(
            'DRY-RUN ONLY: subscribed to /joy; no command topic, UDP, or Lite3 SDK is used.')

    @classmethod
    def _shape_axis(cls, value):
        """Deadzone, rescale the remaining range, and clamp to [-1, 1]."""
        if not math.isfinite(value):
            return 0.0
        value = max(-1.0, min(1.0, float(value)))
        magnitude = abs(value)
        if magnitude <= cls.DEADZONE:
            return 0.0
        shaped = (magnitude - cls.DEADZONE) / (1.0 - cls.DEADZONE)
        return math.copysign(max(0.0, min(1.0, shaped)), value)

    def _on_joy(self, msg):
        max_axis = max(self.AXIS_LATERAL, self.AXIS_FORWARD, self.AXIS_YAW)
        if len(msg.axes) <= max_axis or len(msg.buttons) <= self.BUTTON_DEADMAN:
            self._invalid_message = True
            self._last_valid_joy_time = None
            self._last_values = (0.0, 0.0, 0.0)
            self._deadman_held = False
            return

        raw_values = (
            msg.axes[self.AXIS_FORWARD],
            msg.axes[self.AXIS_LATERAL],
            msg.axes[self.AXIS_YAW],
        )
        if not all(math.isfinite(value) for value in raw_values):
            self._invalid_message = True
            self._last_valid_joy_time = None
            self._last_values = (0.0, 0.0, 0.0)
            self._deadman_held = False
            return

        self._invalid_message = False
        self._last_valid_joy_time = time.monotonic()
        self._deadman_held = bool(msg.buttons[self.BUTTON_DEADMAN])
        self._last_values = tuple(self._shape_axis(value) for value in raw_values)

    def _command_state(self):
        stale = (self._last_valid_joy_time is None or
                 time.monotonic() - self._last_valid_joy_time > self.JOY_TIMEOUT_S)
        enabled = not stale and not self._invalid_message and self._deadman_held
        if not enabled:
            return False, 0.0, 0.0, 0.0
        forward, lateral, yaw = self._last_values
        return True, forward, lateral, yaw

    def _report(self):
        state = self._command_state()
        # Always log safety state changes. While unchanged, log at 10 Hz by timer.
        enabled, forward, lateral, yaw = state
        self.get_logger().info(
            'enabled=%s forward=%.2f lateral=%.2f yaw=%.2f' %
            ('true' if enabled else 'false', forward, lateral, yaw))
        self._last_report = state

    def destroy_node(self):
        # Explicit safe shutdown indication; this node cannot transmit commands.
        self.get_logger().info('Shutdown: enabled=false forward=0.00 lateral=0.00 yaw=0.00')
        return super().destroy_node()


def main():
    rclpy.init()
    node = XboxTeleopDryRun()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
