#!/usr/bin/env python3
"""Safe map-mode manager for the onboard Lite3 computer.

This tool never publishes velocity, Stand, ownership, or navigation goals.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import time

CONFIG = Path(os.environ.get("LITE3_CONFIG_DIR", "/home/abx/.config/lite3"))
MAPS = Path(os.environ.get("LITE3_MAPS_DIR", "/home/abx/ros2_ws/maps"))
STATE = Path(os.environ.get("LITE3_MAP_STATE_DIR", "/home/abx/.local/state/lite3-maps"))
PENDING = STATE / "pending"
ACTIVE = CONFIG / "active_map_yaml"
DEFAULT = CONFIG / "default_map"
MODE = Path("/run/lite3-control/MAP_MODE")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
ROS_PREFIX = ("source /opt/ros/jazzy/setup.bash && "
              "source /home/abx/Desktop/robotdog_ws/install/setup.bash && "
              "export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET "
              "FASTDDS_BUILTIN_TRANSPORTS=UDPv4 && ")


def run(args, timeout=15, check=False):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=check)


def ros(command, timeout=15):
    return run(["bash", "-lc", ROS_PREFIX + command], timeout=timeout)


def systemctl(action, unit, no_block=False):
    command = ["sudo", "-n", "/usr/bin/systemctl"]
    if no_block:
        command.append("--no-block")
    result = run([*command, action, unit], timeout=25)
    if result.returncode:
        raise RuntimeError(result.stdout.strip() or f"systemctl {action} {unit} failed")


def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def runtime_state(name, default="UNKNOWN"):
    try:
        value = (Path("/run/lite3-control") / name).read_text(encoding="utf-8").strip()
        return value or default
    except OSError:
        return default


def service_active(name):
    return run(["systemctl", "is-active", "--quiet", name]).returncode == 0


def topic_fresh(topic, timeout=5):
    command = (f"timeout {timeout} ros2 topic echo {topic} --once "
               "--qos-durability volatile --qos-reliability best_effort >/dev/null 2>&1")
    return ros(command, timeout=timeout + 12).returncode == 0


def tf_fresh(parent, child, timeout=5):
    command = (f"timeout {timeout} ros2 run tf2_ros tf2_echo "
               f"{parent} {child} 2>/dev/null | grep -m1 -q 'Translation:'")
    return ros(command, timeout=timeout + 12).returncode == 0


def validate_map(directory: Path):
    yaml_path = directory / "map.yaml"
    if not yaml_path.is_file() or yaml_path.stat().st_size < 20:
        return False, "map.yaml missing or empty"
    text = yaml_path.read_text(encoding="utf-8", errors="replace")
    image_match = re.search(r"^image:\s*(\S+)\s*$", text, re.MULTILINE)
    resolution = re.search(r"^resolution:\s*([0-9.eE+-]+)\s*$", text, re.MULTILINE)
    origin = re.search(r"^origin:\s*\[[^]]+\]\s*$", text, re.MULTILINE)
    if not image_match or not resolution or not origin:
        return False, "map yaml is missing image/resolution/origin"
    try:
        if float(resolution.group(1)) <= 0:
            return False, "map resolution is invalid"
    except ValueError:
        return False, "map resolution is invalid"
    image = (directory / image_match.group(1)).resolve()
    try:
        image.relative_to(directory.resolve())
    except ValueError:
        return False, "map image escapes its directory"
    if not image.is_file() or image.stat().st_size < 16:
        return False, "map image missing or empty"
    with image.open("rb") as stream:
        magic = stream.read(2)
    if magic not in (b"P2", b"P5"):
        return False, "map image is not a valid PGM"
    return True, "valid"


def available_maps():
    result = []
    if not MAPS.is_dir():
        return result
    for directory in sorted(MAPS.iterdir(), key=lambda p: p.name.casefold()):
        if directory.is_dir() and NAME_RE.fullmatch(directory.name):
            valid, _ = validate_map(directory)
            if valid:
                result.append(directory.name)
    return result


def selected_map():
    if ACTIVE.is_file():
        value = ACTIVE.read_text(encoding="utf-8").strip()
        try:
            path = Path(value).resolve()
            if path.parent.parent == MAPS.resolve():
                return path.parent.name
            if path.parent == PENDING.resolve():
                return "TEMP_VALIDATION"
        except OSError:
            pass
    return DEFAULT.read_text(encoding="utf-8").strip() if DEFAULT.is_file() else "NONE"


def parse_status(timeout=6):
    result = ros(
        f"timeout {timeout} ros2 topic echo /localization/status --once --field data "
        "--qos-durability transient_local --qos-reliability reliable",
        timeout=timeout + 12)
    text = result.stdout.strip()
    for line in text.splitlines():
        line = line.strip().strip("'")
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    # DDS discovery can occasionally miss the transient status sample even
    # while the guard is healthy. The guard atomically mirrors the same
    # measured state under /run; use that as a read-only reporting fallback.
    state = runtime_state("LOCALIZATION_STATE", "UNLOCALIZED")
    try:
        score = float(runtime_state("LOCALIZATION_SCORE", "0.0"))
    except ValueError:
        score = 0.0
    reason = runtime_state(
        "LOCALIZATION_STARTUP_ERROR", "localization status unavailable")
    return {"state": state, "match_fraction": score, "reason": reason}


def capture_mapping_pose():
    result = ros("timeout 6 ros2 run tf2_ros tf2_echo map base_link", timeout=9)
    translation = re.search(r"Translation:\s*\[\s*([-0-9.eE]+),\s*([-0-9.eE]+),", result.stdout)
    quaternion = re.search(r"Quaternion \(xyzw\) \[[^,]+,[^,]+,\s*([-0-9.eE]+),\s*([-0-9.eE]+)\]", result.stdout)
    if not translation or not quaternion:
        raise RuntimeError("could not capture live map -> base_link pose")
    z, w = float(quaternion.group(1)), float(quaternion.group(2))
    return {"x": float(translation.group(1)), "y": float(translation.group(2)),
            "yaw": 2.0 * math.atan2(z, w)}


def probe_live(timeout=6.0):
    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.duration import Duration
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan
    from tf2_ros import Buffer, TransformException, TransformListener

    rclpy.init(args=None)
    node = rclpy.create_node("lite3_map_health_probe")
    seen = {"odom": False, "scan": False}
    node.create_subscription(Odometry, "/odom", lambda _m: seen.__setitem__("odom", True), qos_profile_sensor_data)
    node.create_subscription(LaserScan, "/scan", lambda _m: seen.__setitem__("scan", True), qos_profile_sensor_data)
    buffer = Buffer()
    listener = TransformListener(buffer, node)
    transforms = {"tf_odom_base": False, "tf_base_lidar": False}
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline and not (all(seen.values()) and all(transforms.values())):
            rclpy.spin_once(node, timeout_sec=0.2)
            for key, parent, child in (("tf_odom_base", "odom", "base_link"),
                                       ("tf_base_lidar", "base_link", "lidar_link")):
                try:
                    buffer.lookup_transform(parent, child, rclpy.time.Time(), timeout=Duration(seconds=0.05))
                    transforms[key] = True
                except TransformException:
                    pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return {**seen, **transforms}


def preflight():
    live = probe_live()
    return {
        "robot": service_active("lite3-high-level-runtime.service") and live["odom"],
        "lidar": service_active("lite3-lidar.service") and live["scan"],
        "odom": live["odom"],
        "tf_odom_base": live["tf_odom_base"],
        "tf_base_lidar": live["tf_base_lidar"],
    }


def restore_localization():
    name = DEFAULT.read_text(encoding="utf-8").strip() if DEFAULT.is_file() else ""
    if not NAME_RE.fullmatch(name) or not validate_map(MAPS / name)[0]:
        raise RuntimeError("no valid default map to restore")
    atomic_write(ACTIVE, str(MAPS / name / "map.yaml") + "\n")
    systemctl("stop", "lite3-mapping.service")
    # Queue the input-gated service without waiting for live robot data. This
    # keeps cancellation fast and safe when the physical robot is powered off.
    systemctl("restart", "lite3-localization.service", no_block=True)
    atomic_write(MODE, "LOCALIZATION\n")


def cmd_preflight(_args):
    checks = preflight()
    print(json.dumps(checks, sort_keys=True))
    return 0 if all(checks.values()) else 2


def cmd_start(_args):
    checks = preflight()
    if not all(checks.values()):
        print(json.dumps({"ok": False, "checks": checks}))
        return 2
    systemctl("stop", "lite3-localization.service")
    systemctl("restart", "lite3-mapping.service")
    atomic_write(MODE, "MAPPING\n")
    time.sleep(3)
    conflict = service_active("lite3-localization.service")
    ok = service_active("lite3-mapping.service") and not conflict and topic_fresh("/map", 8)
    print(json.dumps({"ok": ok, "checks": checks, "slam": ok, "conflict": conflict}))
    return 0 if ok else 3


def cmd_cancel(_args):
    systemctl("stop", "lite3-mapping.service")
    if PENDING.exists():
        shutil.rmtree(PENDING)
    restore_localization()
    print(json.dumps({"ok": True, "mode": "LOCALIZATION", "map": selected_map()}))
    return 0


def cmd_finish(_args):
    if not service_active("lite3-mapping.service"):
        raise RuntimeError("mapping service is not active")
    pose = capture_mapping_pose()
    if PENDING.exists():
        shutil.rmtree(PENDING)
    PENDING.mkdir(parents=True)
    result = ros(f"ros2 run nav2_map_server map_saver_cli -t /map -f {PENDING / 'map'} --ros-args -p save_map_timeout:=10.0", timeout=40)
    if result.returncode:
        raise RuntimeError(result.stdout.strip() or "map saver failed")
    valid, reason = validate_map(PENDING)
    if not valid:
        raise RuntimeError(reason)
    atomic_write(PENDING / "initial_pose.json", json.dumps(pose) + "\n")
    systemctl("stop", "lite3-mapping.service")
    atomic_write(ACTIVE, str(PENDING / "map.yaml") + "\n")
    systemctl("restart", "lite3-localization.service")
    atomic_write(MODE, "LOCALIZATION_VALIDATION\n")
    deadline = time.monotonic() + 60
    status = {"state": "UNLOCALIZED", "match_fraction": 0.0, "reason": "timeout"}
    while time.monotonic() < deadline:
        status = parse_status(5)
        if status.get("state") == "LOCALIZED" or float(status.get("match_fraction", 0)) >= 0.80:
            break
        time.sleep(1)
    accepted = status.get("state") == "LOCALIZED" and float(status.get("match_fraction", 0)) >= 0.80
    atomic_write(PENDING / "validation.json", json.dumps(status, sort_keys=True) + "\n")
    print(json.dumps({"ok": accepted, "map_files": "valid", "localization": status}))
    return 0 if accepted else 4


def cmd_accept(args):
    name = args.name
    if not NAME_RE.fullmatch(name):
        raise RuntimeError("invalid map name; use letters, digits, '_' or '-', starting with a letter or digit")
    target = MAPS / name
    if target.exists():
        raise RuntimeError(f"map already exists: {name}")
    valid, reason = validate_map(PENDING)
    if not valid:
        raise RuntimeError(f"pending map invalid: {reason}")
    validation_file = PENDING / "validation.json"
    if not validation_file.is_file():
        raise RuntimeError("pending map has not passed localization validation")
    validation = json.loads(validation_file.read_text(encoding="utf-8"))
    if validation.get("state") != "LOCALIZED" or float(validation.get("match_fraction", 0)) < 0.80:
        raise RuntimeError("pending map localization confidence is below 80%")
    metadata = {"name": name, "validated": True,
                "minimum_match_fraction": 0.80,
                "validation": validation, "saved_at": int(time.time())}
    atomic_write(PENDING / "metadata.json", json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    MAPS.mkdir(parents=True, exist_ok=True)
    PENDING.rename(target)
    atomic_write(DEFAULT, name + "\n")
    atomic_write(ACTIVE, str(target / "map.yaml") + "\n")
    systemctl("restart", "lite3-localization.service")
    atomic_write(MODE, "LOCALIZATION\n")
    print(json.dumps({"ok": True, "map": name}))
    return 0


def cmd_list(_args):
    print(json.dumps({"maps": available_maps(), "selected": selected_map()}))
    return 0


def cmd_select(args):
    name = args.name
    if name not in available_maps():
        raise RuntimeError(f"map not found or invalid: {name}")
    checks = preflight()
    if not all(checks.values()):
        print(json.dumps({"ok": False, "error": "ROBOT OFFLINE", "checks": checks}))
        return 2
    systemctl("stop", "lite3-mapping.service")
    atomic_write(DEFAULT, name + "\n")
    atomic_write(ACTIVE, str(MAPS / name / "map.yaml") + "\n")
    systemctl("restart", "lite3-localization.service")
    atomic_write(MODE, "LOCALIZATION\n")
    deadline = time.monotonic() + 60
    status = parse_status()
    while time.monotonic() < deadline and status.get("state") != "LOCALIZED":
        time.sleep(1)
        status = parse_status()
    ok = status.get("state") == "LOCALIZED" and float(status.get("match_fraction", 0)) >= 0.80
    print(json.dumps({
        "ok": ok,
        "map": name,
        "localization": status,
        "navigation_ready": ok,
        "operator_action": (None if ok else
                            "SHORT MANUAL MOVEMENT REQUIRED"),
    }))
    return 0 if ok else 4


def cmd_relocalize(_args):
    if runtime_state("COMMAND_SOURCE", "UNKNOWN") != "NONE":
        raise RuntimeError("command source is not NONE")
    if not service_active("lite3-localization.service"):
        raise RuntimeError("localization service is not active")
    checks = preflight()
    if not all(checks.values()):
        raise RuntimeError("robot/LiDAR/odometry/TF preflight failed")
    status = parse_status(3)
    if (status.get("state") == "LOCALIZED" and
            float(status.get("match_fraction", 0.0)) >= 0.80):
        print(json.dumps({"ok": True, "needed": False,
                          "localization": status}))
        return 0
    systemctl("start", "lite3-relocalization-motion.service")
    print(json.dumps({"ok": True, "needed": True,
                      "motion": "bounded lateral recovery",
                      "maximum_lateral_excursion_m": 0.045}))
    return 0


def cmd_status(_args):
    mapping = service_active("lite3-mapping.service")
    localization = service_active("lite3-localization.service")
    checks = preflight()
    loc = (parse_status(3) if localization and checks["robot"] and checks["lidar"]
           else {"state": "UNAVAILABLE", "match_fraction": 0.0,
                 "reason": "ROBOT OFFLINE"})
    result = {
        "robot": checks["robot"],
        "lidar": checks["lidar"],
        "odometry": checks["odom"],
        "tf": checks["tf_odom_base"] and checks["tf_base_lidar"],
        "mode": "MAPPING" if mapping else "LOCALIZATION" if localization else "STOPPED",
        "map": selected_map(), "localization": loc,
        "localization_startup": runtime_state("LOCALIZATION_STARTUP_STATE", "STARTING"),
        "localization_startup_error": runtime_state("LOCALIZATION_STARTUP_ERROR", ""),
        "conflict": mapping and localization,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


def acceptance_failure(blocker):
    print(json.dumps({"ok": False, "blocker": blocker, "error": blocker}))
    return 2


def cmd_acceptance(_args):
    """One short, read-only Day-1 live acceptance chain."""
    if not service_active("lite3-high-level-runtime.service"):
        return acceptance_failure("HIGH-LEVEL RUNTIME")
    heartbeat = ros("timeout 4 ros2 param get /lite3_high_level_runtime heartbeat_enabled", timeout=7)
    if heartbeat.returncode or "True" not in heartbeat.stdout:
        return acceptance_failure("HEARTBEAT")
    if not topic_fresh("/odom", 4):
        return acceptance_failure("TELEMETRY / ODOM")
    if not topic_fresh("/scan", 4):
        return acceptance_failure("LIDAR / SCAN")
    if not tf_fresh("odom", "base_link", 4) or not tf_fresh("base_link", "lidar_link", 4):
        return acceptance_failure("TF")
    if selected_map() != "Home_Map" or not validate_map(MAPS / "Home_Map")[0]:
        return acceptance_failure("HOME_MAP")
    if not service_active("lite3-localization.service") or not topic_fresh("/map", 4):
        return acceptance_failure("MAP SERVER / AMCL")
    if not tf_fresh("map", "base_link", 4):
        return acceptance_failure("LOCALIZATION TF")
    status = parse_status(4)
    if status.get("state") != "LOCALIZED" or float(status.get("match_fraction", 0.0)) < 0.80:
        return acceptance_failure("LOCALIZATION <80%")
    print(json.dumps({"ok": True, "map": "Home_Map", "localization": status}))
    return 0


def main():
    if os.environ.get("LITE3_MANAGER_ROS_ENV") != "1":
        command = " ".join(shlex.quote(arg) for arg in [str(Path(__file__).resolve()), *sys.argv[1:]])
        shell = ("source /opt/ros/jazzy/setup.bash && "
                 "source /home/abx/Desktop/robotdog_ws/install/setup.bash && "
                 "export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET "
                 "FASTDDS_BUILTIN_TRANSPORTS=UDPv4 && "
                 "export LITE3_MANAGER_ROS_ENV=1 && exec " + command)
        os.execv("/bin/bash", ["/bin/bash", "-lc", shell])
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in (("preflight", cmd_preflight), ("start", cmd_start),
                       ("cancel", cmd_cancel), ("finish", cmd_finish),
                       ("list", cmd_list), ("status", cmd_status),
                       ("relocalize", cmd_relocalize),
                       ("acceptance", cmd_acceptance)):
        p = sub.add_parser(name); p.set_defaults(func=func)
    p = sub.add_parser("accept"); p.add_argument("name"); p.set_defaults(func=cmd_accept)
    p = sub.add_parser("select"); p.add_argument("name"); p.set_defaults(func=cmd_select)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (RuntimeError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 5


if __name__ == "__main__":
    sys.exit(main())
