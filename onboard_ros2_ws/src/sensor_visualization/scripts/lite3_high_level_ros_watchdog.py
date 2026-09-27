#!/usr/bin/env python3
"""Recover a live systemd service whose HIGH-LEVEL ROS node disappeared.

This process has no publishers, robot sockets, or command-source lease.  A
restart never restores operator authorization or prior motion state.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import os
import signal
import time

import rclpy
from rclpy.node import Node


@dataclass
class RuntimePresenceCore:
    misses_required: int = 3
    startup_grace_s: float = 20.0
    cooldown_s: float = 20.0
    misses: int = 0
    started: float = 0.0
    last_restart: float | None = None

    def observe(self, present: bool, now: float) -> bool:
        if self.started == 0.0:
            self.started = now
        if now - self.started < self.startup_grace_s:
            self.misses = 0
            return False
        if self.last_restart is not None and now - self.last_restart < self.cooldown_s:
            self.misses = 0
            return False
        if present:
            self.misses = 0
            return False
        self.misses += 1
        if self.misses < self.misses_required:
            return False
        self.misses = 0
        self.last_restart = now
        return True


class HighLevelRosWatchdog(Node):
    def __init__(self, parent_pid: int):
        super().__init__("lite3_high_level_ros_watchdog")
        self.declare_parameter("target_node", "/lite3_high_level_runtime")
        self.declare_parameter("check_period_s", 2.0)
        self.declare_parameter("misses_required", 3)
        self.declare_parameter("startup_grace_s", 20.0)
        self.declare_parameter("cooldown_s", 20.0)
        self.target = str(self.get_parameter("target_node").value)
        self.parent_pid = int(parent_pid)
        self.core = RuntimePresenceCore(
            misses_required=max(1, int(self.get_parameter("misses_required").value)),
            startup_grace_s=max(0.0, float(self.get_parameter("startup_grace_s").value)),
            cooldown_s=max(1.0, float(self.get_parameter("cooldown_s").value)),
        )
        self.create_timer(
            max(0.5, float(self.get_parameter("check_period_s").value)), self._check)
        self.get_logger().info(
            f"Monitoring ROS presence of {self.target}; parent_pid={self.parent_pid}; "
            "no robot command path exists")

    def _target_present(self) -> bool:
        return any(
            f"{namespace.rstrip('/')}/{name}".replace("//", "/") == self.target
            for name, namespace in self.get_node_names_and_namespaces())

    def _check(self):
        now = time.monotonic()
        if not self.core.observe(self._target_present(), now):
            return
        self.get_logger().error(
            f"{self.target} absent from DDS after consecutive checks; "
            "restarting persistent HIGH-LEVEL runtime in locked/no-motion state")
        # The wrapper is the systemd MainPID and the unit uses Restart=always.
        # Signalling that same-user parent avoids privileged service control;
        # systemd then replaces the entire control group in a locked state.
        os.kill(self.parent_pid, signal.SIGTERM)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-pid", required=True, type=int)
    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)
    node = HighLevelRosWatchdog(args.parent_pid)
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
