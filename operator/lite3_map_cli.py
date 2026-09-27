#!/usr/bin/env python3
"""Laptop operator commands: mapping, maps, and status."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROBOT = os.environ.get("LITE3_ROBOT_SSH", "abx@192.168.2.32")
REMOTE = os.environ.get("LITE3_MAP_MANAGER", "/home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/sensor_visualization/lite3_map_manager")
RVIZ_CONFIG = os.environ.get("LITE3_RVIZ_CONFIG", "/home/raz/ros-robot-cc/laptop_visualization/lite3_remote_lidar.rviz")
RVIZ_UNIT = "lite3-rviz-session.service"
ENV_MARKER = "LITE3_OPERATOR_ROS_ENV"


def ensure_ros_environment():
    """Make normal-terminal commands independent of shell startup files."""
    if os.environ.get(ENV_MARKER) == "1":
        return
    import shlex
    quoted = " ".join(shlex.quote(arg)
                      for arg in [str(Path(__file__).resolve()), *sys.argv[1:]])
    overlays = ["/opt/ros/jazzy/setup.bash",
                "/home/raz/ros-robot-cc/install/setup.bash"]
    sources = " && ".join(f"source {path}" for path in overlays if Path(path).is_file())
    invoked_as = Path(sys.argv[0]).name
    shell = (f"{sources} && export ROS_DOMAIN_ID=0 "
             "ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET FASTDDS_BUILTIN_TRANSPORTS=UDPv4 && "
             f"export {ENV_MARKER}=1 && "
             f"export LITE3_OPERATOR_COMMAND={shlex.quote(invoked_as)} && exec {quoted}")
    os.execv("/bin/bash", ["/bin/bash", "-lc", shell])


def execute(args, timeout=90):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)


def remote(*args, timeout=30):
    result = execute(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
                      "-o", "ConnectionAttempts=1", "-o", "ServerAliveInterval=2",
                      "-o", "ServerAliveCountMax=1",
                      ROBOT, REMOTE, *args], timeout=timeout)
    if result.returncode == 255:
        return 255, {"ok": False, "error": "MINI-PC OFFLINE",
                     "blocker": "MINI-PC OFFLINE"}
    payload = None
    for line in reversed(result.stdout.splitlines()):
        try:
            payload = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    return result.returncode, payload or {"ok": False, "error": result.stdout.strip() or "robot unreachable"}


def rviz_running():
    return execute(["systemctl", "--user", "is-active", "--quiet", RVIZ_UNIT], 5).returncode == 0


def open_rviz():
    execute(["systemctl", "--user", "stop", RVIZ_UNIT], 10)
    result = execute([
        "systemd-run", "--user", "--unit=lite3-rviz-session", "--collect",
        "--setenv=ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET",
        "--setenv=FASTDDS_BUILTIN_TRANSPORTS=UDPv4",
        "/home/raz/ros-robot-cc/laptop_visualization/lite3_nav2_rviz_session.sh"], 15)
    if result.returncode:
        raise RuntimeError(result.stdout.strip() or "RViz failed to start")


def error_text(data):
    return data.get("error") or data.get("localization", {}).get("reason") or "unknown error"


def print_failure(prefix, data):
    error = error_text(data)
    print(error if error in ("MINI-PC OFFLINE", "ROBOT OFFLINE")
          else f"{prefix}: {error}")


def mapping_command(argv):
    if argv == ["--cancel"]:
        code, data = remote("cancel")
        print("MAPPING CANCELLED; previous localization restored" if code == 0 else f"CANCEL FAILED: {error_text(data)}")
        if code == 0:
            open_rviz()
        return code
    code, data = remote("start")
    if code:
        print_failure("MAPPING START FAILED", data)
        if data.get("checks"):
            for key, value in data["checks"].items():
                print(f"  {key}: {'OK' if value else 'FAILED'}")
        return code
    open_rviz()
    print("MAPPING READY")
    print("Drive the robot manually. No robot motion was commanded by this tool.")
    answer = input("Press Enter when mapping is finished, or type cancel: ").strip().lower()
    if answer == "cancel":
        code, data = remote("cancel")
        print("MAPPING CANCELLED; nothing saved" if code == 0 else f"CANCEL FAILED: {error_text(data)}")
        if code == 0:
            open_rviz()
        return code
    print("Saving temporary map and validating localization...")
    code, data = remote("finish", timeout=120)
    loc = data.get("localization", {})
    score = 100.0 * float(loc.get("match_fraction", 0.0))
    if code or score < 80.0 or loc.get("state") != "LOCALIZED":
        print(f"UNLOCALIZED — validation failed ({score:.1f}%): {error_text(data)}")
        remote("cancel")
        open_rviz()
        return 4
    print(f"LOCALIZATION VALIDATED: {score:.1f}%")
    while True:
        name = input("Map name: ").strip()
        code, accepted = remote("accept", name)
        if code == 0:
            print(f"MAP READY: {name}")
            open_rviz()
            return 0
        print(f"MAP NOT SAVED: {error_text(accepted)}")
        if not sys.stdin.isatty():
            return code


def maps_command(argv):
    if argv:
        requested = argv[0]
    else:
        code, data = remote("list")
        if code:
            print_failure("MAP LIST FAILED", data)
            return code
        names = data.get("maps", [])
        print("AVAILABLE MAPS\n")
        for index, name in enumerate(names, 1):
            marker = " *" if name == data.get("selected") else ""
            print(f"{index}. {name}{marker}")
        if not names:
            print("No valid maps found")
            return 2
        requested = input("\nSelect map: ").strip()
        if requested.isdigit() and 1 <= int(requested) <= len(names):
            requested = names[int(requested) - 1]
    # Robot-side selection allows a full 60 s AMCL convergence/global-search
    # window after health checks and service restart. Leave enough transport
    # margin so the laptop does not abort a healthy localization attempt.
    code, data = remote("select", requested, timeout=120)
    loc = data.get("localization", {})
    score = 100.0 * float(loc.get("match_fraction", 0.0))
    if error_text(data) in ("MINI-PC OFFLINE", "ROBOT OFFLINE"):
        print(error_text(data))
        return code or 2
    open_rviz()
    if code or loc.get("state") != "LOCALIZED" or score < 80.0:
        print("UNLOCALIZED — SHORT MANUAL MOVEMENT REQUIRED")
        print(f"Map: {requested}; confidence: {score:.1f}% ({error_text(data)})")
        print("NAV2/AUTONOMY BLOCKED")
        if not sys.stdin.isatty():
            return 4
        approval = input(
            "Run bounded automatic relocalization motion? Type YES: ").strip()
        if approval != "YES":
            print("Relocalization motion not authorized; robot remains stopped.")
            return 4
        recovery_code, recovery = remote("relocalize", timeout=20)
        if recovery_code:
            print_failure("RELOCALIZATION START FAILED", recovery)
            return recovery_code
        print("RELOCALIZATION STARTED — maximum lateral excursion about 4.5 cm")
        print("Keep the area beside the robot clear; the action stops automatically.")
        last_score = score
        try:
            while True:
                time.sleep(2.0)
                poll_code, current = remote("status", timeout=12)
                current_loc = current.get("localization", {})
                last_score = 100.0 * float(current_loc.get("match_fraction", 0.0))
                if (poll_code == 0 and current_loc.get("state") == "LOCALIZED"
                        and last_score >= 80.0):
                    print(f"LOCALIZED — NAVIGATION READY ({last_score:.1f}%)")
                    return 0
        except KeyboardInterrupt:
            print(f"\nUNLOCALIZED — stopped waiting at {last_score:.1f}%")
            return 4
    print(f"MAP: {requested}")
    print(f"LOCALIZED — NAVIGATION READY ({score:.1f}%)")
    return 0


def status_command():
    code, data = remote("status")
    if code:
        print_failure("STATUS FAILED", data)
        return code
    if not data.get("robot"):
        print("ROBOT OFFLINE")
    loc = data.get("localization", {})
    score = 100.0 * float(loc.get("match_fraction", 0.0))
    state = loc.get("state", "UNLOCALIZED")
    if score < 80.0:
        state = "UNLOCALIZED"
    rows = [
        ("ROBOT", "READY" if data.get("robot") else "NOT READY"),
        ("LIDAR", "OK" if data.get("lidar") else "FAILED"),
        ("ODOMETRY", "OK" if data.get("odometry") else "FAILED"),
        ("TF", "OK" if data.get("tf") else "FAILED"),
        ("MODE", data.get("mode", "UNKNOWN")),
        ("MAP", data.get("map", "NONE")),
        ("STARTUP", data.get("localization_startup", "STARTING")),
        ("LOCALIZATION", f"{score:.1f}% {state}" if data.get("mode") == "LOCALIZATION" else "N/A"),
        ("RVIZ", "RUNNING" if rviz_running() else "STOPPED"),
    ]
    for label, value in rows:
        print(f"{label:.<18} {value}")
    if data.get("localization_startup") == "STARTUP_FAILED":
        print("ERROR: " + data.get("localization_startup_error", "localization startup failed"))
        return 4
    if data.get("conflict"):
        print("ERROR: conflicting SLAM and localization services")
        return 3
    return 0


def acceptance_command():
    code, data = remote("acceptance", timeout=45)
    if code:
        print(data.get("blocker") or error_text(data))
        return code
    open_rviz()
    if not rviz_running():
        print("RVIZ")
        return 6
    instances = execute(["pgrep", "-xc", "rviz2"], 5)
    if instances.returncode or instances.stdout.strip() != "1":
        print("RVIZ DUPLICATE INSTANCE")
        return 6
    print("DAY 1 COMPLETE — READY FOR DAY 2 / NAV2")
    return 0


def main():
    ensure_ros_environment()
    command = os.environ.get("LITE3_OPERATOR_COMMAND", Path(sys.argv[0]).name)
    try:
        if command == "mapping":
            return mapping_command(sys.argv[1:])
        if command == "maps":
            return maps_command(sys.argv[1:])
        if command == "status":
            return status_command()
        if command in ("day1-acceptance", "day1_acceptance"):
            return acceptance_command()
        print("invoke this tool as: mapping, maps, status, or day1-acceptance")
        return 2
    except (subprocess.TimeoutExpired, RuntimeError) as exc:
        print(f"FAILED: {exc}")
        return 5


if __name__ == "__main__":
    sys.exit(main())
