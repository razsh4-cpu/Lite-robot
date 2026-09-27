#!/usr/bin/env python3
"""Connect and validate the laptop Xbox controller without touching robot control."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import select
import struct
import subprocess
import sys
import time
from pathlib import Path


XBOX_MAC = "78:86:2E:B6:8F:C3"
EXPECTED_NAMES = ("xbox", "x-box")
JS_EVENT = struct.Struct("IhBB")
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


def run(*args: str, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout, check=False)


def bluetooth_info() -> str:
    try:
        return run("bluetoothctl", "info", XBOX_MAC).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def field(info: str, name: str) -> str:
    match = re.search(rf"^\s*{re.escape(name)}:\s*(.+?)\s*$", info, re.MULTILINE)
    return match.group(1) if match else ""


def battery_text(info: str) -> str:
    value = field(info, "Battery Percentage")
    match = re.search(r"\((\d+)\)", value)
    return f"Battery: {match.group(1)}%" if match else "Battery: unavailable"


def joystick_name(path: str) -> str:
    base = os.path.basename(path)
    sys_name = f"/sys/class/input/{base}/device/name"
    try:
        return open(sys_name, encoding="utf-8").read().strip()
    except OSError:
        return ""


def validate_device(path: str, event_timeout: float = 2.0) -> tuple[bool, str]:
    name = joystick_name(path)
    if not any(token in name.lower() for token in EXPECTED_NAMES):
        return False, f"unexpected input device: {name or path}"
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except OSError as error:
        return False, f"cannot open {path}: {error.strerror}"
    try:
        deadline = time.monotonic() + event_timeout
        while time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [], max(0.0, deadline - time.monotonic()))
            if not ready:
                break
            data = os.read(fd, JS_EVENT.size)
            if len(data) == JS_EVENT.size:
                return True, name
        return False, f"{name}: no joystick events received"
    except OSError as error:
        return False, f"{name}: event read failed: {error.strerror}"
    finally:
        os.close(fd)


def find_valid_joystick(wait_seconds: float) -> tuple[str, str]:
    deadline = time.monotonic() + wait_seconds
    last_reason = "input device not present"
    while True:
        for path in sorted(glob.glob("/dev/input/js*")):
            valid, reason = validate_device(path)
            if valid:
                return path, reason
            last_reason = reason
        if time.monotonic() >= deadline:
            return "", last_reason
        time.sleep(0.5)


def reconnect() -> str:
    run("bluetoothctl", "disconnect", XBOX_MAC, timeout=6.0)
    time.sleep(1.0)
    try:
        result = run("bluetoothctl", "--timeout", "15", "connect", XBOX_MAC,
                     timeout=18.0)
    except subprocess.TimeoutExpired:
        return "Bluetooth connect timed out"
    return result.stdout.strip()




def configured_robot_address(control, robot_id: str) -> str:
    data = json.loads(control.REGISTRY.read_text(encoding="utf-8"))
    for entry in data.get("robots", []):
        if entry.get("robot_id") == robot_id:
            return str(entry.get("address", ""))
    return ""


def robot_reachable(address: str) -> bool:
    if not address:
        return False
    try:
        probe = run("ping", "-c", "1", "-W", "1", address, timeout=3.0)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return probe.returncode == 0


def ensure_c2_service(control, timeout_s: float = 10.0) -> tuple[bool, str]:
    result = run("systemctl", "--user", "start",
                 "lite3-c2-xbox.service", timeout=8.0)
    if result.returncode != 0:
        detail = result.stdout.strip().splitlines()
        return False, (detail[-1] if detail else "could not start laptop C2 service")
    deadline = time.monotonic() + timeout_s
    last = "laptop C2 node not ready"
    while time.monotonic() < deadline:
        try:
            probe = control.ros2(
                f"ros2 param get {control.NODE} selected_robot", timeout=4.0)
        except subprocess.TimeoutExpired:
            probe = None
        if probe and probe.returncode == 0 and "String value is:" in probe.stdout:
            return True, ""
        if probe and probe.stdout.strip():
            last = probe.stdout.strip().splitlines()[-1]
        time.sleep(0.2)
    return False, last


def select_and_take(robot_id: str) -> tuple[bool, str]:
    import c2_control_cli as control
    if robot_id not in control.configured_robots():
        return False, f"robot is not configured: {robot_id}"
    address = configured_robot_address(control, robot_id)
    if not robot_reachable(address):
        return False, f"ROBOT OFFLINE: {robot_id} ({address or 'unknown address'})"
    service_ready, reason = ensure_c2_service(control)
    if not service_ready:
        return False, reason
    disabled, reason = control.set_parameter("manual_enabled", "false")
    if not disabled:
        return False, reason
    selected, reason = control.set_parameter("selected_robot", robot_id)
    if not selected:
        return False, reason
    enabled, reason = control.set_parameter("manual_enabled", "true")
    if not enabled:
        return False, reason
    acquired, reason = control.wait_status(robot_id, "LAPTOP_XBOX")
    if not acquired:
        control.set_parameter("manual_enabled", "false")
        return False, reason
    return True, ""


def choose_robot(requested: str | None) -> tuple[str, str]:
    import c2_control_cli as control

    robots = sorted(control.configured_robots())
    if not robots:
        return "", "no robots are configured"
    if requested:
        if requested not in robots:
            return "", f"robot is not configured: {requested}"
        return requested, ""
    if not sys.stdin.isatty():
        return "", "interactive robot selection requires a terminal"
    print("Available robots:")
    for robot_id in robots:
        print(f"  - {robot_id}")
    selected = input("Robot name: ").strip()
    if selected not in robots:
        return "", f"robot is not configured: {selected or '<empty>'}"
    return selected, ""


def main() -> int:
    parser = argparse.ArgumentParser(prog="connect joystick")
    parser.add_argument("target", nargs="?", default="joystick")
    parser.add_argument("robot_id", nargs="?", default=None)
    args = parser.parse_args()
    if args.target != "joystick":
        parser.error("the supported command is: connect joystick")

    info = bluetooth_info()
    if not info or field(info, "Name") != "Xbox Wireless Controller":
        print("JOYSTICK NOT FOUND")
        print("Battery: unavailable")
        return 2

    path, name = find_valid_joystick(2.0)
    if not path:
        connect_output = reconnect()
        path, name = find_valid_joystick(15.0)
        info = bluetooth_info()
        if not path:
            connected = field(info, "Connected").lower() == "yes"
            if connected:
                print("BLUETOOTH CONNECTED BUT INPUT NOT AVAILABLE")
            else:
                reason = connect_output.splitlines()[-1] if connect_output else "Xbox unavailable"
                print(f"CONNECTION FAILED: {reason}")
            print(battery_text(info))
            return 3

    info = bluetooth_info()
    print("JOYSTICK READY")
    print(f"Device: {path} ({name})")
    print(battery_text(info))
    robot_id, reason = choose_robot(args.robot_id)
    if not robot_id:
        print(f"ROBOT SELECTION FAILED: {reason}")
        return 4
    ready, reason = select_and_take(robot_id)
    if not ready:
        print(reason if reason.startswith("ROBOT OFFLINE:") else f"ROBOT CONNECTION FAILED: {reason}")
        return 4
    print(f"ROBOT READY: {robot_id}")
    print("COMMAND_SOURCE=LAPTOP_XBOX")
    print("Fresh authorization required: with centered sticks, use A only for the "
          "SIT/STAND toggle; if already standing, press RB once. No motion was sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
