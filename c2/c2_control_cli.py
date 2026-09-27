#!/usr/bin/env python3
"""Explicit C2 robot selection and LAPTOP_XBOX lease commands."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROS_SETUP = "/opt/ros/jazzy/setup.bash"
NODE = "/lite3_c2_xbox"
SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY = SCRIPT_DIR / "robots.json"
sys.path.insert(0, str(SCRIPT_DIR))


def run(*args: str, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)


def ros2(command: str, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    return run("bash", "-lc",
               f"source {ROS_SETUP} && export ROS_DOMAIN_ID=0 "
               f"ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET "
               f"FASTDDS_BUILTIN_TRANSPORTS=UDPv4 && {command}",
               timeout=timeout)


def configured_robots() -> set[str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {entry["robot_id"] for entry in data["robots"]}


def set_parameter(name: str, value: str) -> tuple[bool, str]:
    try:
        result = ros2(f"ros2 param set {NODE} {name} {value}")
    except subprocess.TimeoutExpired:
        return False, f"setting {name} timed out"
    if result.returncode != 0 or "successful" not in result.stdout.lower():
        lines = result.stdout.strip().splitlines()
        return False, lines[-1] if lines else f"could not set {name}"
    return True, ""


def selected_robot() -> str:
    try:
        result = ros2(f"ros2 param get {NODE} selected_robot")
    except subprocess.TimeoutExpired:
        return ""
    marker = "String value is:"
    return result.stdout.split(marker, 1)[1].strip() if marker in result.stdout else ""


def wait_status(robot_id: str, expected_source: str,
                timeout_s: float = 12.0) -> tuple[bool, str]:
    topic = f"/c2/{robot_id}/laptop_xbox/robot_status"
    deadline = time.monotonic() + timeout_s
    last = "robot relay status unavailable"
    while time.monotonic() < deadline:
        try:
            result = ros2(
                f"timeout 6 ros2 topic echo --once {topic} --field data",
                timeout=8.0)
        except subprocess.TimeoutExpired:
            result = None
        if result and result.stdout.strip():
            last = result.stdout.strip().replace("\n", " ")
            if f'"command_source": "{expected_source}"' in result.stdout:
                return True, ""
            if '"state": "lease_denied"' in result.stdout:
                return False, "another command source owns the robot"
        time.sleep(0.2)
    return False, last


def joystick_ready() -> bool:
    try:
        from connect_joystick import bluetooth_info, field, find_valid_joystick
        info = bluetooth_info()
        path, _ = find_valid_joystick(2.0)
        return field(info, "Connected").lower() == "yes" and bool(path)
    except (ImportError, OSError):
        return False


def release_control(robot_id: str) -> tuple[bool, str]:
    changed, reason = set_parameter("manual_enabled", "false")
    if not changed:
        return False, reason
    return wait_status(robot_id, "NONE")


def select_command(robot_id: str) -> int:
    if robot_id not in configured_robots():
        print(f"ROBOT NOT CONFIGURED: {robot_id}")
        return 2
    current = selected_robot() or robot_id
    released, reason = release_control(current)
    if not released:
        print(f"ROBOT SELECTION FAILED: safe release not confirmed: {reason}")
        return 4
    changed, reason = set_parameter("selected_robot", robot_id)
    if not changed:
        print(f"ROBOT SELECTION FAILED: {reason}")
        return 3
    print(f"ROBOT SELECTED: {robot_id}")
    print("COMMAND_SOURCE=NONE")
    return 0


def take_command() -> int:
    robot_id = selected_robot()
    if not robot_id or robot_id not in configured_robots():
        print("TAKE CONTROL FAILED: select a configured robot first")
        return 2
    if not joystick_ready():
        print("TAKE CONTROL FAILED: joystick is not ready; run: connect joystick")
        return 3
    changed, reason = set_parameter("manual_enabled", "true")
    if not changed:
        print(f"TAKE CONTROL FAILED: {reason}")
        return 4
    acquired, reason = wait_status(robot_id, "LAPTOP_XBOX")
    if not acquired:
        set_parameter("manual_enabled", "false")
        print(f"TAKE CONTROL FAILED: {reason}")
        return 4
    print(f"CONTROL ACQUIRED: {robot_id}")
    print("COMMAND_SOURCE=LAPTOP_XBOX")
    print("Fresh operator authorization required; no Stand or motion was sent")
    return 0


def release_command() -> int:
    robot_id = selected_robot()
    if not robot_id:
        print("RELEASE CONTROL FAILED: no robot selected")
        return 2
    released, reason = release_control(robot_id)
    if not released:
        print(f"RELEASE CONTROL FAILED: {reason}")
        return 4
    print(f"CONTROL RELEASED: {robot_id}")
    print("COMMAND_SOURCE=NONE")
    return 0


def main() -> int:
    command = os.path.basename(sys.argv[0])
    if command == "c2":
        if len(sys.argv) == 4 and sys.argv[1:3] == ["select", "robot"]:
            return select_command(sys.argv[3])
        if sys.argv[1:] == ["take", "control"]:
            return take_command()
        if sys.argv[1:] == ["release", "control"]:
            return release_command()
        print("usage: c2 select robot <id> | c2 take control | c2 release control")
        return 2
    if command == "select":
        parser = argparse.ArgumentParser(prog="select robot")
        parser.add_argument("noun")
        parser.add_argument("robot_id")
        args = parser.parse_args()
        if args.noun != "robot":
            parser.error("usage: select robot <robot_id>")
        return select_command(args.robot_id)
    if command == "take":
        if sys.argv[1:] != ["control"]:
            print("usage: take control")
            return 2
        return take_command()
    if command == "release":
        if sys.argv[1:] != ["control"]:
            print("usage: release control")
            return 2
        return release_command()
    print("invoke as: select robot <id>, take control, or release control")
    return 2


if __name__ == "__main__":
    sys.exit(main())
