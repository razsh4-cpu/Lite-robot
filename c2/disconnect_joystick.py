#!/usr/bin/env python3
"""Safely release LAPTOP_XBOX, then disconnect the laptop Xbox controller."""

from __future__ import annotations

import argparse
import glob
import re
import subprocess
import sys
import time


XBOX_MAC = "78:86:2E:B6:8F:C3"
ROS_SETUP = "/opt/ros/jazzy/setup.bash"
ROBOT_ID = "robot_01"


def run(*args: str, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout, check=False)


def ros2(command: str, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    return run("bash", "-lc", f"source {ROS_SETUP} && {command}", timeout=timeout)


def release_manual() -> tuple[bool, str]:
    try:
        result = ros2(
            "ros2 param set /lite3_c2_xbox manual_enabled false", timeout=8.0)
    except subprocess.TimeoutExpired:
        return False, "C2 release request timed out"
    if result.returncode != 0 or "successful" not in result.stdout.lower():
        reason = result.stdout.strip().splitlines()
        return False, reason[-1] if reason else "C2 Xbox node unavailable"
    return True, ""


def wait_for_release(timeout_s: float = 5.0) -> tuple[bool, str]:
    topic = f"/c2/{ROBOT_ID}/laptop_xbox/robot_status"
    deadline = time.monotonic() + timeout_s
    last_status = "robot relay status unavailable"
    while time.monotonic() < deadline:
        try:
            result = ros2(
                f"timeout 3 ros2 topic echo --once {topic} --field data",
                timeout=5.0)
        except subprocess.TimeoutExpired:
            result = None
        if result and result.stdout.strip():
            last_status = result.stdout.strip().replace("\n", " ")
            if '"command_source": "NONE"' in result.stdout:
                return True, ""
        time.sleep(0.2)
    return False, last_status


def bluetooth_connected() -> bool:
    try:
        result = run("bluetoothctl", "info", XBOX_MAC)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return bool(re.search(r"^\s*Connected:\s*yes\s*$", result.stdout, re.MULTILINE))


def disconnect_bluetooth() -> tuple[bool, str]:
    if not bluetooth_connected() and not glob.glob("/dev/input/js*"):
        return True, ""
    try:
        result = run("bluetoothctl", "disconnect", XBOX_MAC, timeout=8.0)
    except subprocess.TimeoutExpired:
        return False, "Bluetooth disconnect timed out"
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        if not bluetooth_connected() and not glob.glob("/dev/input/js*"):
            return True, ""
        time.sleep(0.25)
    reason = result.stdout.strip().splitlines()
    return False, reason[-1] if reason else "Xbox input device remained available"


def main() -> int:
    parser = argparse.ArgumentParser(prog="disconnect joystick")
    parser.add_argument("target", nargs="?", default="joystick")
    args = parser.parse_args()
    if args.target != "joystick":
        parser.error("the supported command is: disconnect joystick")

    released, release_reason = release_manual()
    confirmed, confirm_reason = wait_for_release() if released else (False, release_reason)
    disconnected, reason = disconnect_bluetooth()
    if not disconnected:
        print(f"BLUETOOTH DISCONNECT FAILED: {reason}")
        return 3
    print("JOYSTICK DISCONNECTED")
    print("MANUAL_CONTROL_AVAILABLE=false")
    if confirmed:
        print("COMMAND_SOURCE=NONE")
    else:
        # Bluetooth loss stops /joy; the 300 ms C2 watchdog then publishes
        # neutral/false and the robot relay releases LAPTOP_XBOX.
        print(f"COMMAND_SOURCE release requested; remote confirmation unavailable: {confirm_reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
