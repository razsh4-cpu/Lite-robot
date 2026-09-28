#!/usr/bin/env python3
"""Read-only go/no-go check for an explicitly approved Lite3 Nav2 run."""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lite3_nav_test_override import read as read_test_override


STATE_DIR = Path(os.environ.get("LITE3_STATE_DIR", "/run/lite3-control"))
ENV_MARKER = "LITE3_NAV2_PREFLIGHT_ENV"


def run(command: str, timeout: float = 8.0) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-lc", command], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout, check=False)


def service_active(name: str) -> bool:
    return subprocess.run(
        ["systemctl", "is-active", "--quiet", name],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False).returncode == 0


def topic_fresh(topic: str, reliability: str = "best_effort") -> bool:
    command = (f"timeout 4 ros2 topic echo {shlex.quote(topic)} --once "
               f"--qos-reliability {reliability} "
               "--qos-durability volatile >/dev/null 2>&1")
    return run(command, 7).returncode == 0


def topic_float(topic: str) -> float | None:
    command = (f"timeout 4 ros2 topic echo {shlex.quote(topic)} --once "
               "--field data --qos-reliability best_effort "
               "--qos-durability volatile")
    result = run(command, 7)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        try:
            return float(line.strip().strip("'"))
        except ValueError:
            continue
    return None


def tf_available(parent: str, child: str) -> bool:
    command = (f"timeout 4 ros2 run tf2_ros tf2_echo {shlex.quote(parent)} "
               f"{shlex.quote(child)} 2>/dev/null | grep -m1 -q 'Translation:'")
    return run(command, 7).returncode == 0


def lifecycle_active(node: str) -> bool:
    result = run(f"timeout 4 ros2 lifecycle get /{shlex.quote(node)}", 7)
    return result.returncode == 0 and "active [3]" in result.stdout.lower()


def localization_status() -> tuple[float, str]:
    result = run(
        "timeout 4 ros2 topic echo /localization/status --once --field data "
        "--qos-reliability reliable --qos-durability transient_local", 7)
    for line in result.stdout.splitlines():
        line = line.strip().strip("'")
        if line.startswith("{"):
            try:
                data = json.loads(line)
                return float(data.get("match_fraction", 0.0)), str(
                    data.get("state", "UNLOCALIZED"))
            except (ValueError, json.JSONDecodeError):
                pass
    return 0.0, "UNAVAILABLE"


def command_source() -> str:
    path = STATE_DIR / "COMMAND_SOURCE"
    if not path.is_file():
        return "UNKNOWN"
    value = path.read_text(encoding="utf-8").strip()
    return value if value else "UNKNOWN"


def lease_available() -> bool:
    lock_path = STATE_DIR / "owner.lock"
    if not lock_path.is_file():
        return False
    with lock_path.open("r", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return True


def udp_receiver_count() -> int:
    result = run("ss -H -lunp 'sport = :43897'", 4)
    return sum(1 for line in result.stdout.splitlines() if line.strip())


def action_available(name: str) -> bool:
    result = run("timeout 4 ros2 action list", 7)
    return result.returncode == 0 and name in result.stdout.splitlines()


def map_yaml() -> str | None:
    result = run("timeout 4 ros2 param get /map_server yaml_filename", 7)
    if result.returncode != 0:
        return None
    prefix = "String value is: "
    for line in result.stdout.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip() or None
    return None


def collect() -> dict:
    fraction, state = localization_status()
    battery = topic_float("/lite3/battery_percent")
    source = command_source()
    startup = ((STATE_DIR / "LOCALIZATION_STARTUP_STATE").read_text(encoding="utf-8").strip()
               if (STATE_DIR / "LOCALIZATION_STARTUP_STATE").is_file() else "UNKNOWN")
    override = read_test_override(STATE_DIR)
    minimum = float(override["threshold"]) if override else 0.80
    checks = {
        "high_level": service_active("lite3-high-level-runtime.service"),
        "telemetry_odom": topic_fresh("/odom"),
        "lidar_scan": topic_fresh("/scan"),
        "battery_safe": battery is not None and battery >= 25.0,
        "tf_map_base": tf_available("map", "base_link"),
        "tf_base_lidar": tf_available("base_link", "lidar_link"),
        "localization": state == "LOCALIZED" and fraction >= minimum,
        "navigation_ready": startup == "NAVIGATION_READY",
        "map_server": lifecycle_active("map_server"),
        "amcl": lifecycle_active("amcl"),
        "planner": lifecycle_active("planner_server"),
        "controller": lifecycle_active("controller_server"),
        "bt_navigator": lifecycle_active("bt_navigator"),
        "global_costmap": topic_fresh("/global_costmap/costmap", "reliable"),
        "local_costmap": topic_fresh("/local_costmap/costmap", "reliable"),
        "navigate_action": action_available("/navigate_to_pose"),
        "single_udp_receiver": udp_receiver_count() == 1,
        "command_source_none": source == "NONE",
        "autonomy_lease_available": source == "NONE" and lease_available(),
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "localization_percent": round(100.0 * fraction, 1),
        "localization_state": state,
        "command_source": source,
        "udp_43897_receivers": udp_receiver_count(),
        "battery_percent": battery,
        "map_yaml": map_yaml(),
        "nav2_service_active": service_active("lite3-nav2.service"),
        "localization_threshold": minimum,
        "test_override_active": override is not None,
        "test_override_session": override.get("session_id") if override else None,
        "motion_command_sent": False,
    }


def ensure_environment() -> None:
    if os.environ.get(ENV_MARKER) == "1":
        return
    args = " ".join(shlex.quote(value)
                    for value in [str(Path(__file__).resolve()), *sys.argv[1:]])
    shell = (
        "source /opt/ros/jazzy/setup.bash && "
        "source /home/abx/Desktop/robotdog_ws/install/setup.bash && "
        "export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET "
        "FASTDDS_BUILTIN_TRANSPORTS=UDPv4 "
        f"{ENV_MARKER}=1 && exec {args}")
    os.execv("/bin/bash", ["/bin/bash", "-lc", shell])


def main() -> int:
    ensure_environment()
    try:
        report = collect()
    except (OSError, subprocess.TimeoutExpired) as exc:
        report = {"ready": False, "blocker": str(exc),
                  "motion_command_sent": False}
    if "--json" in sys.argv:
        print(json.dumps(report, sort_keys=True))
    elif report.get("ready"):
        print("NAV2 READY — WAITING FOR EXPLICIT PHYSICAL-TEST APPROVAL")
        print(f"Localization: {report['localization_percent']:.1f}%")
        print(f"Battery: {report['battery_percent']:.0f}%")
        print("COMMAND_SOURCE=NONE; no motion command sent")
    else:
        failed = [name for name, ok in report.get("checks", {}).items() if not ok]
        print("NAV2 NOT READY")
        print("Blocker: " + (failed[0] if failed else report.get("blocker", "unknown")))
        print("No motion command sent")
    return 0 if report.get("ready") else 2


if __name__ == "__main__":
    raise SystemExit(main())
