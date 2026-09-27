#!/usr/bin/env python3
"""Bounded, operator-approved body-frame motion for AMCL recovery."""
from __future__ import annotations

import json
import math
import os
import time

os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32, String


class RecoveryCore:
    # Multipliers are applied toward the clearer side. Each excursion returns
    # over the same observed-clear corridor; net lateral displacement is zero.
    PHASES = (
        (0.5, 0.0),
        (1.7, 0.03),
        (0.5, 0.0),
        (1.7, -0.03),
        (0.5, 0.0),
        (1.7, 0.03),
        (0.5, 0.0),
        (1.7, -0.03),
        (0.8, 0.0),
    )

    def __init__(self):
        self.started = None
        self.good_samples = 0

    @property
    def maximum_duration(self):
        return sum(duration for duration, _ in self.PHASES)

    def update_score(self, state, fraction):
        if state == "LOCALIZED" and float(fraction) >= 0.80:
            self.good_samples += 1
        else:
            self.good_samples = 0
        return self.good_samples >= 3

    def command(self, elapsed):
        cursor = 0.0
        for duration, lateral in self.PHASES:
            cursor += duration
            if elapsed < cursor:
                return lateral
        return 0.0


class RelocalizationMotion(Node):
    def __init__(self):
        super().__init__("lite3_relocalization_motion")
        self.core = RecoveryCore()
        self.last = {name: None for name in ("scan", "odom", "battery", "localization")}
        self.battery = None
        self.scan = None
        self.direction = None
        self.done = False
        self.result = "STARTING"
        self.discovery_started = self._now()
        self.discovery_grace = 12.0
        sensor = QoSProfile(depth=10)
        sensor.reliability = ReliabilityPolicy.BEST_EFFORT
        status = QoSProfile(depth=1)
        status.reliability = ReliabilityPolicy.RELIABLE
        status.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.publisher = self.create_publisher(Twist, "/lite3/relocalization/cmd_vel", 10)
        self.create_subscription(LaserScan, "/scan", self._scan, sensor)
        self.create_subscription(Odometry, "/odom", lambda _m: self._touch("odom"), sensor)
        self.create_subscription(Float32, "/lite3/battery_percent", self._battery, sensor)
        self.create_subscription(String, "/localization/status", self._localization, status)
        self.create_timer(0.05, self._tick)

    def _now(self):
        return time.monotonic()

    def _touch(self, name):
        self.last[name] = self._now()

    def _scan(self, msg):
        self.scan = msg
        self._touch("scan")

    def _battery(self, msg):
        self.battery = float(msg.data)
        self._touch("battery")

    def _localization(self, msg):
        try:
            data = json.loads(msg.data)
            if self.core.update_score(data.get("state"), data.get("match_fraction", 0.0)):
                self._finish("LOCALIZED — NAVIGATION READY")
        except (TypeError, ValueError, json.JSONDecodeError):
            self.core.good_samples = 0
        self._touch("localization")

    def _sector_clearance(self, direction):
        if self.scan is None:
            return 0.0
        target = math.pi / 2.0 if direction > 0.0 else -math.pi / 2.0
        values = []
        for index, distance in enumerate(self.scan.ranges):
            angle = self.scan.angle_min + index * self.scan.angle_increment
            delta = math.atan2(math.sin(angle - target), math.cos(angle - target))
            if abs(delta) <= math.radians(35) and math.isfinite(distance):
                values.append(distance)
        return min(values) if values else 0.0

    def _choose_direction(self):
        left = self._sector_clearance(1.0)
        right = self._sector_clearance(-1.0)
        safe = [(left, 1.0, "left"), (right, -1.0, "right")]
        safe = [candidate for candidate in safe if candidate[0] >= 0.55]
        if not safe:
            self.get_logger().warning(
                f"No safe lateral side: left={left:.2f}m right={right:.2f}m")
            return None
        clearance, direction, label = max(safe)
        self.get_logger().info(
            f"Selected {label} recovery side; clearance={clearance:.2f}m")
        return direction

    def _publish(self, lateral=0.0):
        msg = Twist()
        msg.linear.y = float(lateral)
        self.publisher.publish(msg)

    def _finish(self, result):
        if self.done:
            return
        self._publish(0.0)
        self.result = result
        self.done = True
        self.get_logger().info(result)

    def _tick(self):
        if self.done:
            self._publish(0.0)
            return
        now = self._now()
        for name, stamp in self.last.items():
            limit = 2.0 if name in {"battery", "localization"} else 0.8
            if stamp is None:
                self._publish(0.0)
                if now - self.discovery_started >= self.discovery_grace:
                    self._finish(f"RELOCALIZATION ABORTED: {name} unavailable")
                return
            if now - stamp > limit:
                self._finish(f"RELOCALIZATION ABORTED: {name} stale")
                return
        if self.battery is None or self.battery < 25.0:
            self._finish("RELOCALIZATION ABORTED: battery below 25%")
            return
        if self.core.started is None:
            self.core.started = now
        elapsed = now - self.core.started
        lateral = self.core.command(elapsed)
        if lateral != 0.0 and self.direction is None:
            self.direction = self._choose_direction()
            if self.direction is None:
                self._finish("RELOCALIZATION ABORTED: no lateral clearance >=0.55 m")
                return
        lateral *= self.direction if self.direction is not None else 1.0
        if lateral != 0.0 and self._sector_clearance(lateral) < 0.55:
            self._finish("RELOCALIZATION ABORTED: active-side clearance below 0.55 m")
            return
        if elapsed >= self.core.maximum_duration:
            self._finish("UNLOCALIZED — RECOVERY PATTERN COMPLETE")
            return
        self._publish(lateral)


def main():
    if os.environ.get("LITE3_RELOCALIZATION_APPROVED") != "1":
        raise SystemExit("BLOCKED: explicit operator approval missing")
    rclpy.init()
    node = RelocalizationMotion()
    try:
        deadline = time.monotonic() + node.core.maximum_duration + 5.0
        while rclpy.ok() and not node.done and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
        if not node.done:
            node._finish("RELOCALIZATION ABORTED: bounded timeout")
        print(node.result, flush=True)
    finally:
        for _ in range(3):
            node._publish(0.0)
            rclpy.spin_once(node, timeout_sec=0.03)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
