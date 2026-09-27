#!/usr/bin/env python3
"""Robot-side fail-closed LAPTOP_XBOX relay and command-source lease owner."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import time

os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool, String


class LaptopXboxLease:
    def __init__(self, state_dir):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.source_path = self.state_dir / "COMMAND_SOURCE"
        self.lock_path = self.state_dir / "owner.lock"
        self.lock = None

    def acquire(self):
        if self.lock is not None:
            return True
        lock = self.lock_path.open("a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            return False
        current = (self.source_path.read_text(encoding="utf-8").strip()
                   if self.source_path.exists() else "NONE")
        if current != "NONE":
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
            return False
        self.source_path.write_text("LAPTOP_XBOX\n", encoding="utf-8")
        self.lock = lock
        return True

    def recover_stale_own_marker(self):
        """Clear only an orphaned LAPTOP_XBOX marker.

        The flock is the ownership authority.  A service crash/restart can
        leave the human-readable marker behind after the kernel has released
        the lock.  Never alter NONE or another source's marker.
        """
        if self.lock is not None:
            return False
        lock = self.lock_path.open("a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            return False
        try:
            if self.owner() != "LAPTOP_XBOX":
                return False
            self.source_path.write_text("NONE\n", encoding="utf-8")
            return True
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def release(self):
        if self.lock is None:
            return
        current = (self.source_path.read_text(encoding="utf-8").strip()
                   if self.source_path.exists() else "NONE")
        if current == "LAPTOP_XBOX":
            self.source_path.write_text("NONE\n", encoding="utf-8")
        fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
        self.lock.close()
        self.lock = None

    def owner(self):
        return (self.source_path.read_text(encoding="utf-8").strip()
                if self.source_path.exists() else "NONE")


class LaptopXboxFreshness:
    def __init__(self, timeout_s=0.30):
        self.timeout_s = max(0.05, float(timeout_s))
        self.requested = False
        self.request_time = None
        self.heartbeat_time = None
        self.joy_time = None
        self.joy = None

    def request(self, enabled, now):
        self.requested = bool(enabled)
        self.request_time = float(now)

    def heartbeat(self, enabled, now):
        self.heartbeat_time = float(now) if enabled else None

    def update_joy(self, joy, now):
        self.joy = joy
        self.joy_time = float(now)

    def ready(self, now):
        now = float(now)
        return (self.requested and self.request_time is not None
                and now - self.request_time <= self.timeout_s
                and self.heartbeat_time is not None
                and now - self.heartbeat_time <= self.timeout_s
                and self.joy_time is not None
                and now - self.joy_time <= self.timeout_s)

    def clear(self):
        self.requested = False
        self.request_time = None
        self.heartbeat_time = None
        self.joy_time = None
        self.joy = None


def neutral_joy():
    message = Joy()
    message.axes = [0.0] * 8
    message.buttons = [0] * 15
    return message


class LaptopXboxSource(Node):
    def __init__(self):
        super().__init__("lite3_laptop_xbox_source")
        self.declare_parameter("robot_id", "robot_01")
        self.declare_parameter("state_dir", "/run/lite3-control")
        self.declare_parameter("timeout_s", 0.30)
        self.robot_id = str(self.get_parameter("robot_id").value)
        prefix = f"/c2/{self.robot_id}/laptop_xbox"
        self.freshness = LaptopXboxFreshness(
            self.get_parameter("timeout_s").value)
        self.lease = LaptopXboxLease(self.get_parameter("state_dir").value)
        recovered = self.lease.recover_stale_own_marker()
        self.joy_pub = self.create_publisher(Joy, "/lite3/laptop_xbox/joy", 10)
        self.status_pub = self.create_publisher(String, f"{prefix}/robot_status", 10)
        self.create_subscription(Joy, f"{prefix}/joy", self._on_joy, 10)
        self.create_subscription(Bool, f"{prefix}/heartbeat", self._on_heartbeat, 10)
        self.create_subscription(Bool, f"{prefix}/request", self._on_request, 10)
        self.create_timer(0.05, self._tick)
        self._last_status = None
        self.get_logger().info(
            f"Waiting for explicit C2 request on {prefix}; "
            + ("cleared orphaned LAPTOP_XBOX marker"
               if recovered else "COMMAND_SOURCE unchanged"))

    def _on_joy(self, message):
        self.freshness.update_joy(message, time.monotonic())

    def _on_heartbeat(self, message):
        self.freshness.heartbeat(message.data, time.monotonic())
        if not message.data:
            self._safe_release("heartbeat_false")

    def _on_request(self, message):
        self.freshness.request(message.data, time.monotonic())
        if not message.data:
            self._safe_release("request_revoked")

    def _publish_status(self, state):
        owner = self.lease.owner()
        payload = json.dumps({
            "robot_id": self.robot_id,
            "state": state,
            "command_source": owner,
            "manual_available": self.lease.lock is not None,
            "timestamp_monotonic": time.monotonic(),
        }, sort_keys=True)
        if payload != self._last_status:
            self.status_pub.publish(String(data=payload))
            self._last_status = payload

    def _safe_release(self, reason):
        if self.lease.lock is not None:
            self.joy_pub.publish(neutral_joy())
            self.lease.release()
            self.get_logger().warning(
                f"LAPTOP_XBOX released ({reason}); zero/neutral boundary published")
        self.freshness.clear()
        self._publish_status(reason)

    def _tick(self):
        now = time.monotonic()
        if not self.freshness.ready(now):
            if self.lease.lock is not None:
                self._safe_release("input_stale")
            else:
                self._publish_status("waiting")
            return
        if self.lease.lock is None and not self.lease.acquire():
            self._publish_status("lease_denied")
            return
        self.joy_pub.publish(self.freshness.joy)
        self._publish_status("active_waiting_for_operator_authorization")

    def destroy_node(self):
        try:
            self._safe_release("shutdown")
        finally:
            return super().destroy_node()


def main():
    rclpy.init()
    node = LaptopXboxSource()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
