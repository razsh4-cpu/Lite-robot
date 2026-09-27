#!/usr/bin/env python3
"""Laptop operator wrapper for the existing bounded relocalization service."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

ROBOT = os.environ.get("LITE3_ROBOT_SSH", "abx@192.168.2.32")
GUARD = os.environ.get(
    "LITE3_POSTURE_GUARD",
    "/home/abx/ros2_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_posture_guard")
MAP_MANAGER = os.environ.get(
    "LITE3_MAP_MANAGER",
    "/home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_map_manager")
RELEASE_AUTONOMY = os.environ.get(
    "LITE3_RELEASE_AUTONOMY",
    "/home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_release_autonomy")
SERVICE = "lite3-relocalization-motion.service"
MARKER = "/run/lite3-control/RELOCALIZATION_ACTIVE"
SSH = [
    "ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
    "-o", "ConnectionAttempts=1", "-o", "ServerAliveInterval=2",
    "-o", "ServerAliveCountMax=1", ROBOT,
]


def run_remote(*command, timeout=10):
    try:
        return subprocess.run(
            [*SSH, *command], text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 124, "ROBOT CONNECTION TIMEOUT\n")


def robot_snapshot():
    result = run_remote(GUARD, "status")
    if result.returncode == 255:
        return None, "ROBOT OFFLINE"
    for line in reversed(result.stdout.splitlines()):
        try:
            return json.loads(line), None
        except json.JSONDecodeError:
            continue
    return None, result.stdout.strip() or "ROBOT STATUS UNAVAILABLE"


def map_snapshot():
    result = run_remote(MAP_MANAGER, "status", timeout=15)
    if result.returncode == 255:
        return None, "ROBOT OFFLINE"
    for line in reversed(result.stdout.splitlines()):
        try:
            return json.loads(line), None
        except json.JSONDecodeError:
            continue
    return None, result.stdout.strip() or "MAP STATUS UNAVAILABLE"


def service_state():
    result = run_remote("systemctl", "is-active", SERVICE)
    state = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "unknown"
    return state


def marker_active():
    return run_remote("test", "-e", MARKER).returncode == 0


def stop_and_cleanup():
    """Stop the lease owner, then clear only an unlocked stale AUTONOMY marker."""
    stopped = run_remote(
        "sudo", "-n", "/usr/bin/systemctl", "stop", SERVICE, timeout=15)
    released = run_remote(RELEASE_AUTONOMY, timeout=8)
    cleared = run_remote("rm", "-f", MARKER, timeout=5)
    return stopped.returncode == released.returncode == cleared.returncode == 0


def print_status():
    snapshot, error = robot_snapshot()
    if snapshot is None:
        print(error)
        return 2
    system, system_error = map_snapshot()
    if system is None:
        system = {}
    confidence = 100.0 * float(snapshot.get("localization_confidence", 0.0))
    localization = snapshot.get("localization_state", "UNAVAILABLE")
    if confidence < 80.0:
        localization = "UNLOCALIZED"
    state = service_state()
    mode = "RUNNING" if state in {"active", "activating"} else "IDLE"
    print(f"RELOCALIZATION .... {mode}")
    print(f"MAP ............... {system.get('map', 'UNAVAILABLE')}")
    print(f"CONNECTION ........ {'CONNECTED' if snapshot.get('connected') else 'OFFLINE'}")
    print(f"POSTURE ........... {str(snapshot.get('posture', 'unknown')).upper()}")
    print(f"HIGH-LEVEL ........ {'HEALTHY' if snapshot.get('high_level_healthy') else 'UNHEALTHY'}")
    print(f"COMMAND SOURCE .... {snapshot.get('command_source', 'UNKNOWN')}")
    print(f"LOCALIZATION ...... {confidence:.1f}% {localization}")
    print(f"/scan ............. {'OK' if system.get('lidar') else 'UNAVAILABLE'}")
    print(f"/odom ............. {'OK' if system.get('odometry') else 'UNAVAILABLE'}")
    print(f"TF ................ {'OK' if system.get('tf') else 'UNAVAILABLE'}")
    print("CLEARANCE ......... NOT MEASURED (rechecked live before motion; minimum 0.55 m)")
    if system_error:
        print(f"STATUS NOTE ....... {system_error}")
    return 0


def safe_to_start(snapshot, system=None):
    if not snapshot.get("connected") or not snapshot.get("high_level_healthy"):
        return False, "RELOCALIZATION BLOCKED: HIGH-LEVEL UNHEALTHY"
    if not snapshot.get("telemetry_fresh"):
        return False, "RELOCALIZATION BLOCKED: ROBOT STATE STALE"
    if snapshot.get("posture") != "standing":
        return False, "RELOCALIZATION BLOCKED: ROBOT NOT STANDING"
    if snapshot.get("command_source") != "NONE":
        return False, ("RELOCALIZATION BLOCKED: COMMAND_SOURCE="
                       + str(snapshot.get("command_source")))
    if snapshot.get("motion_enabled") or not snapshot.get("velocities_zero"):
        return False, "RELOCALIZATION BLOCKED: NON-ZERO OR ACTIVE MOTION"
    if system is not None and not all(
            system.get(key) for key in ("robot", "lidar", "odometry", "tf")):
        return False, "RELOCALIZATION BLOCKED: scan/odom/TF preflight failed"
    return True, "READY"


def start():
    snapshot, error = robot_snapshot()
    if snapshot is None:
        print(error)
        return 2
    system, system_error = map_snapshot()
    if system is None:
        print(system_error)
        return 2
    allowed, reason = safe_to_start(snapshot, system)
    if not allowed:
        print(reason)
        return 3
    if service_state() in {"active", "activating"}:
        print("RELOCALIZATION ALREADY RUNNING")
        return 0
    confidence = 100.0 * float(snapshot.get("localization_confidence", 0.0))
    print("RELOCALIZATION PREFLIGHT")
    print(f"  map: {system.get('map', 'UNAVAILABLE')}")
    print(f"  localization: {confidence:.1f}% "
          f"{snapshot.get('localization_state', 'UNAVAILABLE')}")
    print(f"  posture: {str(snapshot.get('posture', 'unknown')).upper()}")
    print(f"  HIGH-LEVEL: {'HEALTHY' if snapshot.get('high_level_healthy') else 'UNHEALTHY'}")
    print(f"  command source: {snapshot.get('command_source', 'UNKNOWN')}")
    print(f"  /scan: {'OK' if system.get('lidar') else 'UNAVAILABLE'}")
    print(f"  /odom: {'OK' if system.get('odometry') else 'UNAVAILABLE'}")
    print(f"  TF: {'OK' if system.get('tf') else 'UNAVAILABLE'}")
    print("  lateral clearance will be measured from the live scan before movement")
    print("PROPOSED BOUNDED MANEUVER")
    print("  lateral-only alternating motion at up to 0.03 m/s")
    print("  approximately 4.5 cm maximum excursion per side; returns toward origin")
    print("  zero forward velocity and zero yaw; automatic safety/timeout stop")
    try:
        approval = input("Physical robot movement will occur. Continue? [y/N] ")
    except (EOFError, KeyboardInterrupt):
        print()
        approval = ""
    if approval.strip().lower() != "y":
        print("RELOCALIZATION CANCELLED — no ownership acquired; no motion sent")
        return 0
    result = run_remote(
        "sudo", "-n", "/usr/bin/systemctl", "start", SERVICE, timeout=15)
    if result.returncode:
        stop_and_cleanup()
        print("RELOCALIZATION START FAILED: " + result.stdout.strip())
        return result.returncode
    print("RELOCALIZATION STARTED — bounded safety-controlled motion")
    return 0


def cancel():
    state = service_state()
    marker = marker_active()
    snapshot, _ = robot_snapshot()
    source = snapshot.get("command_source") if snapshot else "UNKNOWN"
    if state not in {"active", "activating", "deactivating"} and not marker:
        print("RELOCALIZATION ALREADY IDLE")
        return 0
    if not stop_and_cleanup():
        print("RELOCALIZATION CANCEL FAILED: cleanup path failed")
        return 4
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        snapshot, _ = robot_snapshot()
        if snapshot and snapshot.get("command_source") == "NONE":
            print("RELOCALIZATION CANCELLED — COMMAND_SOURCE=NONE")
            return 0
        time.sleep(0.2)
    print("RELOCALIZATION CANCELLED — ownership release not yet confirmed "
          f"(previous source={source})")
    return 4


def main():
    arguments = sys.argv[1:]
    if arguments == ["status"]:
        return print_status()
    if arguments == ["cancel"]:
        return cancel()
    if not arguments:
        return start()
    print("Usage: relocalize [status|cancel]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
