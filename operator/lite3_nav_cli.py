#!/usr/bin/env python3
"""Laptop operator CLI for the built-in Lite3 Nav2 obstacle test."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

ROBOT = os.environ.get("LITE3_ROBOT_SSH", "abx@192.168.2.32")
REMOTE_PREFLIGHT = os.environ.get(
    "LITE3_NAV2_PREFLIGHT",
    "/home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_nav2_preflight")
REMOTE_GUARD = os.environ.get(
    "LITE3_POSTURE_GUARD",
    "/home/abx/ros2_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_posture_guard")
REMOTE_RELEASE = os.environ.get(
    "LITE3_RELEASE_AUTONOMY",
    "/home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_release_autonomy")
REMOTE_TEST_OVERRIDE = os.environ.get(
    "LITE3_NAV_TEST_OVERRIDE",
    "/home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/"
    "sensor_visualization/lite3_nav_test_override")
NORMAL_THRESHOLD = 0.80
TEST_THRESHOLD = 0.70
AUTONOMY_UNIT = "lite3-autonomy-command-source.service"
NAV2_UNIT = "lite3-nav2.service"
NAV2_CHECKS = {"planner", "controller", "bt_navigator", "global_costmap",
               "local_costmap", "navigate_action"}
SOURCE_FILE = "/run/lite3-control/COMMAND_SOURCE"
HERE = Path(__file__).resolve().parent
STATE_ROOT = Path(os.environ.get(
    "LITE3_OBSTACLE_TEST_STATE", Path.home() / ".local/state/lite3-obstacle-test"))
CURRENT = STATE_ROOT / "current.json"
SESSION_ROOT = Path(os.environ.get(
    "LITE3_OBSTACLE_TEST_SESSIONS", Path.home() / "lite3_diagnostics/obstacle"))
ENV_MARKER = "LITE3_NAV_CLI_ROS_ENV"
SSH = ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
       "-o", "ConnectionAttempts=1", "-o", "ServerAliveInterval=2",
       "-o", "ServerAliveCountMax=1", ROBOT]


def ensure_ros_environment():
    if os.environ.get(ENV_MARKER) == "1":
        return
    quoted = " ".join(shlex.quote(arg)
                      for arg in [str(Path(__file__).resolve()), *sys.argv[1:]])
    overlays = ["/opt/ros/jazzy/setup.bash",
                "/home/raz/ros-robot-cc/install/setup.bash"]
    sources = " && ".join(f"source {item}" for item in overlays if Path(item).is_file())
    shell = (f"{sources} && export ROS_DOMAIN_ID=0 "
             "ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET "
             "FASTDDS_BUILTIN_TRANSPORTS=UDPv4 && "
             f"export {ENV_MARKER}=1 && exec {quoted}")
    os.execv("/bin/bash", ["/bin/bash", "-lc", shell])


def run(command, timeout=30, input_text=None):
    try:
        return subprocess.run(command, text=True, input=input_text,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        return subprocess.CompletedProcess(command, 124, output + "TIMEOUT\n")


def remote(*args, timeout=12):
    return run([*SSH, *args], timeout=timeout)


def last_json(output):
    for line in reversed(output.splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def remote_json(*args, timeout=15):
    result = remote(*args, timeout=timeout)
    if result.returncode == 255:
        return None, "robot offline"
    data = last_json(result.stdout)
    if data is None:
        return None, result.stdout.strip() or "invalid remote response"
    return data, None


def source():
    result = remote("cat", SOURCE_FILE, timeout=5)
    return result.stdout.strip().splitlines()[-1] if result.returncode == 0 and result.stdout.strip() else "UNKNOWN"


def load_state():
    try:
        return json.loads(CURRENT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"state": "IDLE"}


def save_state(value):
    from lite3_nav_obstacle_core import atomic_json
    value["updated_unix"] = time.time()
    atomic_json(CURRENT, value)


def active_nav_goal():
    """Read the latched action status; this function has no control output."""
    import rclpy
    from action_msgs.msg import GoalStatus, GoalStatusArray
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
    rclpy.init()
    node = Node("lite3_obstacle_test_goal_probe")
    statuses = []
    qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(GoalStatusArray, "/navigate_to_pose/_action/status",
                             lambda msg: statuses.extend(item.status for item in msg.status_list), qos)
    try:
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        return any(value in (GoalStatus.STATUS_ACCEPTED,
                             GoalStatus.STATUS_EXECUTING,
                             GoalStatus.STATUS_CANCELING) for value in statuses)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def live_preflight(test_samples=None):
    from lite3_nav_obstacle_core import preflight_blockers
    nav, nav_error = remote_json(REMOTE_PREFLIGHT, "--json", timeout=35)
    robot, robot_error = remote_json(REMOTE_GUARD, "status", timeout=12)
    if nav is None:
        return None, None, [nav_error]
    if robot is None:
        return nav, None, [robot_error]
    mission = active_nav_goal()
    return nav, robot, preflight_blockers(
        nav, robot, mission, test_samples=test_samples)


def sample_localization():
    command = (
        "for i in 1 2 3; do cat /run/lite3-control/LOCALIZATION_SCORE "
        "|| exit 2; test $i = 3 || sleep 1.05; done")
    result = remote("bash", "-lc", command, timeout=8)
    try:
        values = [float(line) for line in result.stdout.splitlines() if line.strip()]
    except ValueError:
        return []
    return values[-3:] if result.returncode == 0 else []


def set_test_override(command, session_id=None):
    args = [REMOTE_TEST_OVERRIDE, command]
    if session_id is not None:
        args += ["--session", session_id, "--ttl", "600"]
    return remote_json(*args, timeout=12)


def clear_test_override():
    remote(REMOTE_TEST_OVERRIDE, "clear", timeout=6)


def nav2_missing(nav):
    checks = (nav or {}).get("checks", {})
    return any(not checks.get(name, False) for name in NAV2_CHECKS)


def blockers_ignoring_nav2(nav, robot, test_samples=None):
    from lite3_nav_obstacle_core import preflight_blockers
    patched = json.loads(json.dumps(nav))
    for name in NAV2_CHECKS:
        patched.setdefault("checks", {})[name] = True
    return preflight_blockers(
        patched, robot, active_nav_goal(), test_samples=test_samples)


def start_nav2_layer():
    """Start only the existing navigation layer; never starts AUTONOMY."""
    result = remote("sudo", "-n", "/usr/bin/systemctl", "start",
                    NAV2_UNIT, timeout=20)
    if result.returncode:
        return result.stdout.strip() or "Nav2 service start failed"
    return None


def snapshot_and_plan():
    snapshot = run([
        sys.executable, str(HERE / "lite3_chair_dryrun_snapshot.py"),
        "--output-root", str(SESSION_ROOT), "--max-candidates", "80"], timeout=100)
    payload = last_json(snapshot.stdout)
    if snapshot.returncode or not payload:
        raise RuntimeError(snapshot.stdout.strip() or "snapshot failed")
    session = Path(payload["snapshot"])
    analyzed = run([sys.executable, str(HERE / "lite3_chair_snapshot_analyze.py"),
                    str(session)], timeout=90)
    if analyzed.returncode:
        raise RuntimeError(analyzed.stdout.strip() or "clearance analysis failed")
    from lite3_nav_obstacle_core import (atomic_json, relevant_obstacle,
                                         select_candidate, side)
    obstacle = relevant_obstacle(session)
    if obstacle is None:
        return session, None, None
    selected = select_candidate(session, obstacle)
    if selected is None:
        return session, obstacle, None
    path_payload = json.loads((session / selected["file"]).read_text(encoding="utf-8"))
    path_data = path_payload["path"] if "path" in path_payload else path_payload
    goal = path_data["poses"][-1]
    atomic_json(session / "planned_path.json", path_payload)
    atomic_json(session / "selected_goal.json", goal)
    selection = {key: value for key, value in selected.items() if key != "path"}
    selection.update({"side": side(selected), "obstacle": obstacle})
    atomic_json(session / "selection.json", selection)
    return session, obstacle, selection


def start_plan_display(session):
    return subprocess.Popen([sys.executable, str(HERE / "lite3_publish_obstacle_plan.py"),
                             str(session)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)


def stop_plan_display(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def cleanup_autonomy():
    remote("sudo", "-n", "/usr/bin/systemctl", "stop", AUTONOMY_UNIT, timeout=12)
    remote(REMOTE_RELEASE, timeout=8)
    final_source = source()
    clear_test_override()
    return final_source


def status_command():
    current = load_state()
    nav, robot, blockers = live_preflight()
    print(f"OBSTACLE TEST .... {current.get('state', 'IDLE')}")
    print(f"SESSION .......... {current.get('session_id', 'NONE')}")
    if robot:
        print(f"ROBOT ............ {'CONNECTED' if robot.get('connected') else 'OFFLINE'}")
        print(f"POSTURE .......... {str(robot.get('posture', 'UNKNOWN')).upper()}")
        print(f"HIGH-LEVEL ....... {'HEALTHY' if robot.get('high_level_healthy') else 'UNHEALTHY'}")
    if nav:
        print(f"LOCALIZATION ..... {nav.get('localization_percent', 0.0):.1f}% {nav.get('localization_state', 'UNKNOWN')}")
        print(f"MAP ............... {nav.get('map_yaml') or 'UNKNOWN'}")
        print(f"NAV2 SERVICE ...... {'ACTIVE' if nav.get('nav2_service_active') else 'INACTIVE'}")
        print(f"COMMAND_SOURCE ... {nav.get('command_source', 'UNKNOWN')}")
        if nav.get("test_override_active"):
            print("TEST OVERRIDE ..... ACTIVE (70% ×3, obstacle session only)")
    else:
        print("LIVE STATE ....... UNAVAILABLE")
    print("PREFLIGHT ........ " + ("READY" if not blockers else "BLOCKED — " + blockers[0]))
    print("READ ONLY — no ownership or motion command")
    return 0 if not blockers else 2


def cancel_command():
    current = load_state()
    active = current.get("state") in {"ACQUIRING_AUTONOMY", "ACTIVE", "CANCELLING"}
    if not active:
        clear_test_override()
        print("OBSTACLE TEST ALREADY IDLE")
        return 0
    save_state({**current, "state": "CANCELLING"})
    pid = current.get("executor_pid")
    if isinstance(pid, int):
        try:
            os.kill(pid, signal.SIGINT)
        except ProcessLookupError:
            pass
    run([sys.executable, str(HERE / "lite3_nav_obstacle_cancel.py")], timeout=8)
    final_source = cleanup_autonomy()
    state = "CANCELLED" if final_source == "NONE" else "CANCEL_FAILED"
    save_state({**current, "state": state, "command_source_final": final_source,
                "executor_pid": None})
    if final_source != "NONE":
        print(f"OBSTACLE TEST CANCEL FAILED — COMMAND_SOURCE={final_source}")
        return 4
    print("OBSTACLE TEST CANCELLED — COMMAND_SOURCE=NONE")
    return 0


def test_command():
    samples = sample_localization()
    nav, robot, normal_blockers = live_preflight()
    if (normal_blockers and nav and robot and nav2_missing(nav) and
            not blockers_ignoring_nav2(nav, robot)):
        error = start_nav2_layer()
        if error:
            print("OBSTACLE TEST BLOCKED — " + error)
            return 3
        nav, robot, normal_blockers = live_preflight()
    override_active = False
    session_id = None
    if normal_blockers:
        nav, robot, candidate_blockers = live_preflight(test_samples=samples)
        if (candidate_blockers and nav and robot and nav2_missing(nav)):
            candidate_blockers = blockers_ignoring_nav2(
                nav, robot, test_samples=samples)
        if candidate_blockers:
            print("OBSTACLE TEST BLOCKED — " + candidate_blockers[0])
            return 3
        current = float(nav.get("localization_percent", 0.0))
        print("LOCALIZATION TEST OVERRIDE REQUEST")
        print("NORMAL GATE ........ 80% ×3")
        print("TEST GATE .......... 70% ×3")
        print(f"CURRENT ............ {current:.1f}%")
        print("SAMPLES ............ " + ", ".join(f"{100*v:.1f}%" for v in samples))
        save_state({"state": "OVERRIDE_NOT_APPROVED",
                    "localization_percent": current,
                    "localization_samples": samples,
                    "command_source_initial": nav.get("command_source", "UNKNOWN"),
                    "motion_approved": False,
                    "test_override_active": False})
        try:
            approved = input(
                "Enable one-session 70% localization TEST override? [y/N] "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            approved = ""
            print()
        if approved != "y":
            print("TEST OVERRIDE NOT ENABLED — no ownership or motion command")
            return 0
        session_id = "obstacle-" + time.strftime("%Y%m%d-%H%M%S")
        payload, error = set_test_override("enable", session_id)
        if error or not payload or not payload.get("active"):
            clear_test_override()
            detail = error or (payload or {}).get("error", "override rejected")
            print("TEST BLOCKED — " + detail)
            return 3
        override_active = True
    else:
        print("NORMAL LOCALIZATION GATE ACTIVE — 80% ×3")

    publisher = None
    autonomy_acquired = False
    try:
        if override_active:
            print("LOCALIZATION TEST OVERRIDE ACTIVE")
            # Give the guard three timer cycles to publish LOCALIZED / READY.
            time.sleep(3.2)
        nav, robot, _ = live_preflight()
        if nav2_missing(nav):
            remaining = blockers_ignoring_nav2(
                nav, robot, test_samples=(samples if override_active else None))
            if remaining:
                print("OBSTACLE TEST BLOCKED — " + remaining[0])
                return 3
            error = start_nav2_layer()
            if error:
                print("OBSTACLE TEST BLOCKED — " + error)
                return 3
        deadline = time.monotonic() + 25.0
        while True:
            nav, robot, blockers = live_preflight()
            if not blockers:
                break
            if time.monotonic() >= deadline:
                print("OBSTACLE TEST BLOCKED — " + blockers[0])
                return 3
            time.sleep(0.5)
        try:
            session, obstacle, selection = snapshot_and_plan()
        except RuntimeError as exc:
            print(f"OBSTACLE TEST BLOCKED — {exc}")
            return 3
        base_state = {
            "session_id": session.name, "test_override_session": session_id,
            "session": str(session), "command_source_initial": nav["command_source"],
            "localization_percent": nav["localization_percent"],
            "normal_threshold": NORMAL_THRESHOLD,
            "test_threshold": TEST_THRESHOLD if override_active else None,
            "test_override_active": override_active, "motion_approved": False,
            "command_source_transitions": [
                {"t": time.time(), "source": nav["command_source"]}],
        }
        if obstacle is None:
            save_state({**base_state, "state": "NO_OBSTACLE"})
            print("NO TEST OBSTACLE DETECTED")
            return 4
        if selection is None:
            save_state({**base_state, "state": "NO_SAFE_PATH", "obstacle": obstacle})
            print("OBSTACLE TEST BLOCKED — NO SAFE PATH")
            return 4
        publisher = start_plan_display(session)
        goal = json.loads((session / "selected_goal.json").read_text(encoding="utf-8"))
        ready = {**base_state, "state": "READY_NOT_APPROVED",
                 "obstacle": obstacle, "selection": selection}
        save_state(ready)
        print("READY FOR CONTROLLED 70% CHAIR AVOIDANCE TEST"
              if override_active else "OBSTACLE TEST READY")
        print(f"Localization: {nav['localization_percent']:.1f}% — 3/3 stable")
        print("Obstacle detected: YES")
        print(f"Selected side: {selection['side']}")
        print(f"Path length: {selection['path_length']:.2f} m")
        print(f"Minimum padded-footprint clearance: "
              f"{selection['minimum_padded_clearance']:.3f} m")
        print(f"Goal: x={goal['x']:.3f}, y={goal['y']:.3f}")
        print("Velocity limits: vx=0.10 m/s, vy=0.05 m/s, wz=0.20 rad/s")
        print("Local/global costmaps: HEALTHY")
        print(f"COMMAND_SOURCE: {nav['command_source']}")
        print(f"Diagnostic session: {session}")
        if override_active:
            print("70% LOCALIZATION TEST OVERRIDE ACTIVE")
        try:
            answer = input(
                "Physical autonomous motion will occur. Continue? [y/N] "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
            print()
        if answer != "y":
            print("OBSTACLE TEST NOT STARTED — no ownership or motion command")
            return 0

        nav2, robot2, blockers2 = live_preflight()
        if blockers2:
            save_state({**ready, "state": "BLOCKED_AFTER_APPROVAL"})
            print("OBSTACLE TEST BLOCKED — " + blockers2[0])
            return 3
        state = {**ready, "state": "ACQUIRING_AUTONOMY", "motion_approved": True}
        save_state(state)
        started = remote("sudo", "-n", "/usr/bin/systemctl", "start",
                         AUTONOMY_UNIT, timeout=15)
        if started.returncode:
            final_source = cleanup_autonomy()
            override_active = False
            save_state({**state, "state": "FAIL", "reason": started.stdout.strip(),
                        "command_source_final": final_source})
            print("CONTROLLED 70% CHAIR AVOIDANCE: FAIL — AUTONOMY acquisition failed")
            return 4
        deadline = time.monotonic() + 8.0
        selected_source = source()
        while selected_source != "AUTONOMY" and time.monotonic() < deadline:
            time.sleep(0.2)
            selected_source = source()
        state["command_source_transitions"].append(
            {"t": time.time(), "source": selected_source})
        if selected_source != "AUTONOMY":
            cleanup_autonomy(); override_active = False
            save_state({**state, "state": "FAIL",
                        "reason": "AUTONOMY lease not acquired"})
            print("CONTROLLED 70% CHAIR AVOIDANCE: FAIL — AUTONOMY lease not acquired")
            return 4
        autonomy_acquired = True
        executor = subprocess.Popen([sys.executable,
            str(HERE / "lite3_nav_obstacle_execute.py"), str(session),
            "--localization-threshold",
            str(TEST_THRESHOLD if override_active else NORMAL_THRESHOLD)])
        save_state({**state, "state": "ACTIVE", "executor_pid": executor.pid})
        code = executor.wait()
        execution = json.loads((session / "execution.json").read_text(encoding="utf-8"))
        final_source = cleanup_autonomy(); override_active = False
        autonomy_acquired = final_source != "NONE"
        final_robot, final_error = remote_json(REMOTE_GUARD, "status", timeout=12)
        no_contact = False
        if code == 0 and sys.stdin.isatty():
            no_contact = input(
                "Confirm obstacle cleared without contact? [y/N] "
            ).strip().lower() == "y"
        passed = (code == 0 and execution.get("success") and no_contact and
                  final_source == "NONE" and final_robot and
                  final_robot.get("velocities_zero", False))
        final = {**state, "state": "PASS" if passed else "FAIL",
                 "test_override_active": False, "executor_pid": None,
                 "execution": execution, "final_robot_state": final_robot,
                 "final_robot_error": final_error,
                 "obstacle_contact_confirmed_absent": no_contact,
                 "command_source_final": final_source}
        final["command_source_transitions"].append(
            {"t": time.time(), "source": final_source})
        save_state(final)
        (session / "result.json").write_text(
            json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        label = "PASS" if passed else "FAIL"
        print(f"CONTROLLED 70% CHAIR AVOIDANCE: {label}")
        if passed:
            return 0
        print("Reason: " + (execution.get("reason") or "final safety condition failed"))
        return 4
    finally:
        if autonomy_acquired:
            cleanup_autonomy()
            override_active = False
        if override_active:
            clear_test_override()
        stop_plan_display(publisher)


def main():
    ensure_ros_environment()
    if len(sys.argv) < 3 or sys.argv[1:3] != ["test", "obstacle"]:
        print("Usage: nav test obstacle [status|cancel]")
        return 2
    tail = sys.argv[3:]
    if not tail:
        return test_command()
    if tail == ["status"]:
        return status_command()
    if tail == ["cancel"]:
        return cancel_command()
    print("Usage: nav test obstacle [status|cancel]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
