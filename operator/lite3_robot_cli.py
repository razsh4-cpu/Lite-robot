#!/usr/bin/env python3
"""Laptop operator CLI for safe, state-aware Lite3 posture commands."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROBOT = os.environ.get("LITE3_ROBOT_SSH", "abx@192.168.2.32")
GUARD = os.environ.get(
    "LITE3_POSTURE_GUARD",
    "/home/abx/ros2_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_posture_guard")
PREFIX = "/c2/robot_01/laptop_xbox"
ENV_MARKER = "LITE3_ROBOT_CLI_ROS_ENV"


def ensure_ros_environment():
    if os.environ.get(ENV_MARKER) == "1":
        return
    quoted = " ".join(shlex.quote(arg)
                      for arg in [str(Path(__file__).resolve()), *sys.argv[1:]])
    overlays = ["/opt/ros/jazzy/setup.bash",
                "/home/raz/ros-robot-cc/install/setup.bash"]
    sources = " && ".join(
        f"source {path}" for path in overlays if Path(path).is_file())
    shell = (f"{sources} && export ROS_DOMAIN_ID=0 "
             "ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET "
             "FASTDDS_BUILTIN_TRANSPORTS=UDPv4 && "
             f"export {ENV_MARKER}=1 && exec {quoted}")
    os.execv("/bin/bash", ["/bin/bash", "-lc", shell])


def remote_guard(*arguments, timeout=10):
    command = [
        "ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
        "-o", "ConnectionAttempts=1", "-o", "ServerAliveInterval=2",
        "-o", "ServerAliveCountMax=1", ROBOT, GUARD, *arguments]
    result = None
    for attempt in range(2):
        try:
            result = subprocess.run(
                command, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            if attempt == 0:
                continue
            return 124, {"ok": False, "message": "ROBOT CONNECTION TIMEOUT"}
        if result.returncode != 255 or attempt == 1:
            break
        time.sleep(0.25)
    assert result is not None
    if result.returncode == 255:
        return result.returncode, {"ok": False, "message": "ROBOT OFFLINE"}
    for line in reversed(result.stdout.splitlines()):
        try:
            return result.returncode, json.loads(line)
        except json.JSONDecodeError:
            continue
    return result.returncode or 2, {
        "ok": False, "message": result.stdout.strip() or "ROBOT STATUS UNAVAILABLE"}


def neutral_message(Joy):
    return Joy(axes=[0.0] * 8, buttons=[0] * 15)


def posture_message(Joy):
    message = neutral_message(Joy)
    message.buttons[0] = 1  # validated vendor SIT_STAND edge
    return message


def print_status(data):
    confidence = 100.0 * float(data.get("localization_confidence", 0.0))
    print(f"CONNECTION ........ {'CONNECTED' if data.get('connected') else 'OFFLINE'}")
    print(f"POSTURE ........... {str(data.get('posture', 'unknown')).upper()}")
    print(f"HIGH-LEVEL ........ {'HEALTHY' if data.get('high_level_healthy') else 'UNHEALTHY'}")
    print(f"COMMAND SOURCE .... {data.get('command_source', 'UNKNOWN')}")
    print("LOCALIZATION ...... "
          f"{confidence:.1f}% {data.get('localization_state', 'UNAVAILABLE')}")


def perform(action, dry_run=False):
    code, initial = remote_guard("preflight", action)
    message = initial.get("message", "POSTURE PREFLIGHT FAILED")
    if code or not initial.get("ok"):
        print(message)
        return code or 3
    if message in {"ROBOT ALREADY STANDING", "ROBOT ALREADY DOWN"}:
        print(message)
        return 0
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Joy
    from std_msgs.msg import Bool, String

    class PostureClient(Node):
        def __init__(self):
            super().__init__("lite3_robot_posture_cli")
            self.request = self.create_publisher(Bool, PREFIX + "/request", 10)
            self.heartbeat = self.create_publisher(Bool, PREFIX + "/heartbeat", 10)
            self.joy = self.create_publisher(Joy, PREFIX + "/joy", 10)
            self.relay = None
            self.create_subscription(String, PREFIX + "/robot_status", self._status, 10)

        def _status(self, message):
            try:
                self.relay = json.loads(message.data)
            except json.JSONDecodeError:
                self.relay = None

        def send(self, enabled, pose_edge=False):
            self.request.publish(Bool(data=enabled))
            self.heartbeat.publish(Bool(data=enabled))
            self.joy.publish(posture_message(Joy) if pose_edge else neutral_message(Joy))

        def cycle(self, seconds, enabled=True, pose_edge=False):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                self.send(enabled, pose_edge)
                rclpy.spin_once(self, timeout_sec=0.02)
                time.sleep(0.03)

    rclpy.init()
    node = PostureClient()

    def guard_while_heartbeating(*arguments, timeout=10):
        """Keep the 300 ms C2 watchdog fed during the remote safety probe."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                remote_guard, *arguments, timeout=timeout)
            deadline = time.monotonic() + timeout + 1.0
            while not future.done() and time.monotonic() < deadline:
                node.cycle(0.10)
            if not future.done():
                return 124, {"ok": False, "message": "ROBOT CONNECTION TIMEOUT"}
            return future.result()

    result = 4
    try:
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            node.cycle(0.15)
            relay = node.relay or {}
            if (relay.get("command_source") == "LAPTOP_XBOX"
                    and relay.get("manual_available")):
                break
        else:
            print("POSTURE BLOCKED: C2 lease was not acquired")
            return 4

        code, armed = guard_while_heartbeating(
            "preflight", action, "--allow-source", "LAPTOP_XBOX")
        if code or not armed.get("ok"):
            print(armed.get("message", "POSTURE PREFLIGHT FAILED"))
            return code or 4

        if dry_run:
            print(f"DRY RUN READY: robot {action}; temporary C2 lease acquired "
                  "and released; no posture command sent")
            result = 0
            return result

        node.cycle(0.40)
        node.cycle(0.20, pose_edge=True)
        node.cycle(0.50)
        deadline = time.monotonic() + 25.0
        while time.monotonic() < deadline:
            node.cycle(0.20)
            code, confirmed = guard_while_heartbeating(
                "confirm", action, "--allow-source", "LAPTOP_XBOX")
            if code == 0 and confirmed.get("ok"):
                print(confirmed["message"])
                result = 0
                break
        else:
            print(f"ROBOT {action.upper()} NOT CONFIRMED")
    finally:
        for _ in range(8):
            node.send(False)
            rclpy.spin_once(node, timeout_sec=0.03)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return result


def main():
    ensure_ros_environment()
    if len(sys.argv) < 2 or sys.argv[1] not in {"stand", "down", "status"}:
        print("Usage: robot {stand|down|status}")
        return 2
    action = sys.argv[1]
    dry_run = "--dry-run" in sys.argv[2:]
    if action == "status":
        code, data = remote_guard("status")
        if code:
            print(data.get("message", "ROBOT STATUS UNAVAILABLE"))
            return code
        print_status(data)
        return 0
    return perform(action, dry_run=dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
