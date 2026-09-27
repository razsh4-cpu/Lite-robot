#!/usr/bin/env python3
"""Independent read-only health monitor that revokes AUTONOMY on degradation."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import time

os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32, String


class Nav2SafetyCore:
    def __init__(self, odom_timeout=1.0, scan_timeout=1.0,
                 localization_timeout=3.0, cmd_timeout=0.50,
                 battery_timeout=2.0, min_battery_percent=25.0,
                 localization_soft_min=0.80,
                 localization_hard_min=0.70,
                 localization_grace=2.0):
        self.timeouts = {
            "odom": float(odom_timeout), "scan": float(scan_timeout),
            "localization": float(localization_timeout),
            "cmd_vel": float(cmd_timeout),
            "battery": float(battery_timeout),
        }
        self.min_battery_percent = float(min_battery_percent)
        self.localization_soft_min = float(localization_soft_min)
        self.localization_hard_min = float(localization_hard_min)
        self.localization_grace = float(localization_grace)
        self.localization_below_soft_since = None
        self.stamps = {name: None for name in self.timeouts}
        self.localization_fraction = 0.0
        self.localization_state = "UNAVAILABLE"
        self.cmd = (0.0, 0.0, 0.0)
        self.battery_percent = None

    def touch(self, name, now):
        self.stamps[name] = float(now)

    def update_localization(self, state, fraction, now):
        self.localization_state = str(state)
        self.localization_fraction = float(fraction)
        self.touch("localization", now)

    def update_battery(self, percent, now):
        self.battery_percent = float(percent)
        self.touch("battery", now)

    def update_cmd(self, vx, vy, wz, now):
        self.cmd = (float(vx), float(vy), float(wz))
        self.touch("cmd_vel", now)

    def failure(self, now, require_cmd=True, allow_low_localization=False):
        for name, timeout in self.timeouts.items():
            if name == "cmd_vel" and not require_cmd:
                continue
            stamp = self.stamps[name]
            if stamp is None or float(now) - stamp > timeout:
                return f"{name} stale"
        # Entry into AUTONOMY is still gated separately by three consecutive
        # samples >=80%.  Once moving, tolerate only a short, modest score dip
        # caused by scan changes.  Severe loss (<70%) remains an immediate abort.
        if (not allow_low_localization and
                self.localization_fraction < self.localization_hard_min):
            self.localization_below_soft_since = None
            return "localization below hard safety threshold"
        if (not allow_low_localization and
                (self.localization_state != "LOCALIZED" or
                 self.localization_fraction < self.localization_soft_min)):
            if self.localization_below_soft_since is None:
                self.localization_below_soft_since = float(now)
            elif (float(now) - self.localization_below_soft_since >=
                  self.localization_grace):
                return "localization below 80% beyond grace period"
        else:
            self.localization_below_soft_since = None
        if (self.battery_percent is None or
                not math.isfinite(self.battery_percent) or
                self.battery_percent < self.min_battery_percent):
            return "battery below safe threshold"
        if not all(math.isfinite(value) for value in self.cmd):
            return "non-finite cmd_vel"
        vx, vy, wz = self.cmd
        if abs(vx) > 0.1001 or abs(vy) > 0.0501 or abs(wz) > 0.2001:
            return "cmd_vel exceeds Day-2 limits"
        return None


class Nav2SafetyMonitor(Node):
    def __init__(self):
        super().__init__("lite3_nav2_safety_monitor")
        self.declare_parameter("state_dir", "/run/lite3-control")
        self.source_path = Path(
            str(self.get_parameter("state_dir").value)) / "COMMAND_SOURCE"
        self.core = Nav2SafetyCore()
        self.autonomy_since = None
        self.tripped = False
        sensor_qos = QoSProfile(depth=10)
        sensor_qos.reliability = ReliabilityPolicy.BEST_EFFORT
        status_qos = QoSProfile(depth=1)
        status_qos.reliability = ReliabilityPolicy.RELIABLE
        status_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.create_subscription(Odometry, "/odom", self._odom, sensor_qos)
        self.create_subscription(LaserScan, "/scan", self._scan, sensor_qos)
        self.create_subscription(Twist, "/cmd_vel", self._cmd, 10)
        self.create_subscription(
            Float32, "/lite3/battery_percent", self._battery, sensor_qos)
        self.create_subscription(
            String, "/localization/status", self._localization, status_qos)
        self.create_timer(0.10, self._tick)
        self.get_logger().info(
            "Nav2 safety monitor ready; inert unless COMMAND_SOURCE=AUTONOMY")

    def _now(self):
        return time.monotonic()

    def _odom(self, _msg):
        self.core.touch("odom", self._now())

    def _scan(self, _msg):
        self.core.touch("scan", self._now())

    def _battery(self, msg):
        self.core.update_battery(msg.data, self._now())

    def _cmd(self, msg):
        self.core.update_cmd(
            msg.linear.x, msg.linear.y, msg.angular.z, self._now())

    def _localization(self, msg):
        try:
            data = json.loads(msg.data)
            self.core.update_localization(
                data.get("state", "UNLOCALIZED"),
                data.get("match_fraction", 0.0), self._now())
        except (TypeError, ValueError, json.JSONDecodeError):
            self.core.update_localization("UNAVAILABLE", 0.0, self._now())

    def _source(self):
        try:
            return self.source_path.read_text(encoding="utf-8").strip()
        except OSError:
            return "UNKNOWN"

    def _tick(self):
        now = self._now()
        if self._source() != "AUTONOMY":
            self.autonomy_since = None
            self.tripped = False
            return
        if self.autonomy_since is None:
            self.autonomy_since = now
        # Allow one controller cycle after the explicit source transition.
        if now - self.autonomy_since < 0.25 or self.tripped:
            return
        # Match the adapter's 30 s startup window: health inputs are enforced
        # immediately, while the operator gets time to submit the approved
        # goal before the first cmd_vel. After the first command, 0.5 s applies.
        # A cmd_vel received before this AUTONOMY lease belongs to an earlier
        # run and must not make the new lease fail immediately as "stale".
        # Once this lease sees its first command, the normal 0.5 s watchdog is
        # enforced without any grace-period extension.
        cmd_stamp = self.core.stamps["cmd_vel"]
        command_seen_for_this_lease = (
            cmd_stamp is not None and cmd_stamp >= self.autonomy_since)
        require_cmd = (command_seen_for_this_lease or
                       now - self.autonomy_since >= 30.0)
        recovery_marker = self.source_path.parent / "RELOCALIZATION_ACTIVE"
        recovery_active = recovery_marker.is_file()
        reason = self.core.failure(
            now, require_cmd=require_cmd,
            allow_low_localization=recovery_active)
        if reason is None:
            return
        self.tripped = True
        self.get_logger().error(
            f"AUTONOMY ABORT: {reason}; stopping lease-owning adapter")
        subprocess.run([
            "/usr/bin/sudo", "-n", "/usr/bin/systemctl", "stop",
            "lite3-autonomy-command-source.service"], check=False,
            timeout=4)


def main():
    rclpy.init()
    node = Nav2SafetyMonitor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
