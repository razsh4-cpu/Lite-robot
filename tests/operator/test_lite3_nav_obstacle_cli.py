import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OPERATOR = ROOT / "operator"
sys.path.insert(0, str(OPERATOR))


def load(name):
    spec = importlib.util.spec_from_file_location(name, OPERATOR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CORE = load("lite3_nav_obstacle_core")
CLI = load("lite3_nav_cli")


def ready_nav():
    names = (
        "high_level", "telemetry_odom", "lidar_scan", "battery_safe",
        "tf_map_base", "tf_base_lidar", "localization", "navigation_ready",
        "map_server", "amcl", "planner", "controller", "bt_navigator", "global_costmap",
        "local_costmap", "navigate_action", "single_udp_receiver",
        "command_source_none", "autonomy_lease_available",
    )
    return {"ready": True, "checks": {name: True for name in names},
            "localization_percent": 91.2, "localization_state": "LOCALIZED",
            "command_source": "NONE"}


def ready_robot():
    return {"connected": True, "high_level_healthy": True,
            "telemetry_fresh": True, "posture": "standing",
            "velocities_zero": True, "motion_enabled": False}


def fake_session(tmp_path):
    session = tmp_path / "session"
    session.mkdir()
    (session / "selected_goal.json").write_text(json.dumps({
        "x": 1.0, "y": 2.0, "z": 0.0,
        "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0}))
    obstacle = {"base_x": 0.8, "base_y": 0.0}
    selection = {"side": "LEFT", "path_length": 1.2,
                 "minimum_padded_clearance": 0.12}
    return session, obstacle, selection


class FakeProcess:
    def poll(self): return None
    def terminate(self): pass
    def wait(self, timeout=None): return 0
    def kill(self): pass


def configure_no_motion(monkeypatch, tmp_path):
    monkeypatch.setattr(CLI, "CURRENT", tmp_path / "state/current.json")
    monkeypatch.setattr(CLI, "STATE_ROOT", tmp_path / "state")
    monkeypatch.setattr(CLI, "sample_localization", lambda: [0.75, 0.76, 0.77])
    monkeypatch.setattr(CLI, "live_preflight",
                        lambda **_kwargs: (ready_nav(), ready_robot(), []))
    monkeypatch.setattr(CLI, "snapshot_and_plan", lambda: fake_session(tmp_path))
    monkeypatch.setattr(CLI, "start_plan_display", lambda _session: FakeProcess())
    monkeypatch.setattr(CLI, "stop_plan_display", lambda _process: None)


def test_preflight_requires_every_safety_condition():
    assert CORE.preflight_blockers(ready_nav(), ready_robot(), False) == []
    nav = ready_nav()
    nav["checks"]["navigation_ready"] = False
    assert "3 consecutive" in CORE.preflight_blockers(nav, ready_robot(), False)[0]
    robot = ready_robot()
    robot["posture"] = "sitting"
    assert any("posture" in item for item in CORE.preflight_blockers(
        ready_nav(), robot, False))
    assert "active Nav2 mission" in CORE.preflight_blockers(
        ready_nav(), ready_robot(), True)


def test_default_no_never_calls_remote_or_acquires_autonomy(monkeypatch, tmp_path):
    configure_no_motion(monkeypatch, tmp_path)
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(CLI, "remote", lambda *_a, **_k:
                        (_ for _ in ()).throw(AssertionError("remote mutation called")))
    assert CLI.test_command() == 0
    state = json.loads(CLI.CURRENT.read_text())
    assert state["state"] == "READY_NOT_APPROVED"
    assert state["motion_approved"] is False
    assert state["command_source_initial"] == "NONE"


def test_only_literal_y_reaches_autonomy_start(monkeypatch, tmp_path):
    configure_no_motion(monkeypatch, tmp_path)
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    calls = []
    monkeypatch.setattr(CLI, "set_test_override", lambda *_a, **_k:
                        ({"active": True}, None))
    monkeypatch.setattr(CLI, "clear_test_override", lambda: None)
    monkeypatch.setattr(CLI, "remote", lambda *args, **_kwargs:
                        (calls.append(args) or subprocess.CompletedProcess(args, 1, "denied")))
    assert CLI.test_command() == 4
    assert any(AUTONOMY in call for call in calls for AUTONOMY in
               (CLI.AUTONOMY_UNIT,))
    state = json.loads(CLI.CURRENT.read_text())
    assert state["motion_approved"] is True


def test_cancel_is_idempotent_when_idle(monkeypatch, tmp_path):
    monkeypatch.setattr(CLI, "CURRENT", tmp_path / "current.json")
    cleared = []
    monkeypatch.setattr(CLI, "clear_test_override", lambda: cleared.append(True))
    assert CLI.cancel_command() == 0
    assert cleared == [True]


def test_cancel_active_requests_nav_cancel_and_releases(monkeypatch, tmp_path):
    monkeypatch.setattr(CLI, "CURRENT", tmp_path / "current.json")
    CLI.save_state({"state": "ACTIVE", "session_id": "fixture", "executor_pid": 999999})
    calls = []
    monkeypatch.setattr(CLI, "run", lambda *args, **kwargs:
                        (calls.append(args[0]) or subprocess.CompletedProcess(args[0], 0, "ok")))
    monkeypatch.setattr(CLI, "cleanup_autonomy", lambda: "NONE")
    assert CLI.cancel_command() == 0
    assert any("lite3_nav_obstacle_cancel.py" in " ".join(call) for call in calls)
    state = json.loads(CLI.CURRENT.read_text())
    assert state["state"] == "CANCELLED"
    assert state["command_source_final"] == "NONE"



def candidate_nav():
    nav = ready_nav()
    nav["ready"] = False
    nav["localization_percent"] = 75.0
    nav["localization_state"] = "UNLOCALIZED"
    nav["checks"]["localization"] = False
    nav["checks"]["navigation_ready"] = False
    return nav


def test_70_override_default_no_creates_no_token_or_motion(monkeypatch, tmp_path):
    monkeypatch.setattr(CLI, "CURRENT", tmp_path / "state/current.json")
    monkeypatch.setattr(CLI, "sample_localization", lambda: [0.75, 0.76, 0.77])
    monkeypatch.setattr(CLI, "active_nav_goal", lambda: False)
    monkeypatch.setattr(
        CLI, "live_preflight",
        lambda test_samples=None: (
            candidate_nav(), ready_robot(),
            CORE.preflight_blockers(candidate_nav(), ready_robot(), False,
                                    test_samples=test_samples)))
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(CLI, "set_test_override", lambda *_a, **_k:
                        (_ for _ in ()).throw(AssertionError("override enabled")))
    monkeypatch.setattr(CLI, "snapshot_and_plan", lambda:
                        (_ for _ in ()).throw(AssertionError("planning started")))
    assert CLI.test_command() == 0
    state = json.loads(CLI.CURRENT.read_text())
    assert state["state"] == "OVERRIDE_NOT_APPROVED"
    assert state["test_override_active"] is False


def test_explicit_override_still_requires_separate_motion_approval(monkeypatch, tmp_path):
    monkeypatch.setattr(CLI, "CURRENT", tmp_path / "state/current.json")
    monkeypatch.setattr(CLI, "sample_localization", lambda: [0.75, 0.76, 0.77])
    calls = {"preflight": 0, "override": 0}
    def preflight(test_samples=None):
        calls["preflight"] += 1
        if calls["preflight"] <= 2:
            nav = candidate_nav()
            return nav, ready_robot(), CORE.preflight_blockers(
                nav, ready_robot(), False, test_samples=test_samples)
        return ready_nav(), ready_robot(), []
    monkeypatch.setattr(CLI, "live_preflight", preflight)
    monkeypatch.setattr(CLI, "set_test_override", lambda *_a, **_k:
                        (calls.__setitem__("override", calls["override"] + 1)
                         or ({"active": True}, None)))
    monkeypatch.setattr(CLI, "clear_test_override", lambda: None)
    monkeypatch.setattr(CLI.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(CLI, "snapshot_and_plan", lambda: fake_session(tmp_path))
    monkeypatch.setattr(CLI, "start_plan_display", lambda _session: FakeProcess())
    monkeypatch.setattr(CLI, "stop_plan_display", lambda _process: None)
    answers = iter(["y", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(CLI, "remote", lambda *_a, **_k:
                        (_ for _ in ()).throw(AssertionError("AUTONOMY called")))
    assert CLI.test_command() == 0
    assert calls["override"] == 1
    state = json.loads(CLI.CURRENT.read_text())
    assert state["state"] == "READY_NOT_APPROVED"
    assert state["motion_approved"] is False


def test_existing_nav2_layer_starts_only_when_other_gates_pass(monkeypatch, tmp_path):
    configure_no_motion(monkeypatch, tmp_path)
    missing = ready_nav()
    for name in CLI.NAV2_CHECKS:
        missing["checks"][name] = False
    sequence = iter([(missing, ready_robot(), ["Nav2 planner unavailable"]),
                     (ready_nav(), ready_robot(), []),
                     (ready_nav(), ready_robot(), []),
                     (ready_nav(), ready_robot(), [])])
    monkeypatch.setattr(CLI, "live_preflight", lambda **_kwargs: next(sequence))
    monkeypatch.setattr(CLI, "active_nav_goal", lambda: False)
    starts = []
    monkeypatch.setattr(CLI, "start_nav2_layer", lambda: starts.append(True))
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    assert CLI.test_command() == 0
    assert starts == [True]

def test_status_is_read_only_by_construction():
    source = (OPERATOR / "lite3_nav_cli.py").read_text()
    body = source.split("def status_command():", 1)[1].split("def cancel_command():", 1)[0]
    for forbidden in ("cleanup_autonomy", "systemctl", "NavigateToPose", "Popen"):
        assert forbidden not in body


def test_executor_reuses_nav2_and_never_publishes_velocity():
    source = (OPERATOR / "lite3_nav_obstacle_execute.py").read_text()
    assert "NavigateToPose" in source
    assert "create_subscription(Twist, \"/cmd_vel\"" in source
    assert "create_publisher(Twist" not in source
    assert 'command_source() != \"AUTONOMY\"' in source
    assert '"local_costmap"' in source and '"global_costmap"' in source
    assert "300" not in source  # the authoritative 300 ms watchdog remains onboard


def test_planning_snapshot_is_inert_and_records_required_evidence():
    source = (OPERATOR / "lite3_chair_dryrun_snapshot.py").read_text()
    assert "ComputePathToPose" in source
    assert "from nav2_msgs.action import NavigateToPose" not in source
    assert "cmd_vel_at_snapshot" in source
    assert '"odom"' in source
    assert '"motion_sent": False' in source


def test_status_never_starts_nav2_or_autonomy():
    source = (OPERATOR / "lite3_nav_cli.py").read_text()
    body = source.split("def status_command():", 1)[1].split(
        "def cancel_command():", 1)[0]
    assert "start_nav2_layer" not in body
    assert "AUTONOMY_UNIT" not in body


def test_nav2_start_helper_only_starts_existing_nav2_unit():
    source = (OPERATOR / "lite3_nav_cli.py").read_text()
    body = source.split("def start_nav2_layer():", 1)[1].split(
        "def snapshot_and_plan():", 1)[0]
    assert "NAV2_UNIT" in body
    assert "AUTONOMY_UNIT" not in body
    assert "cmd_vel" not in body


def test_override_module_is_installed_as_executable_and_importable_python():
    cmake = (ROOT / "onboard_ros2_ws/src/sensor_visualization/CMakeLists.txt").read_text()
    assert "RENAME lite3_nav_test_override" in cmake
    assert "install(FILES scripts/lite3_nav_test_override.py" in cmake


def test_release_helper_always_removes_test_override():
    helper = (ROOT / "onboard_ros2_ws/src/sensor_visualization/scripts/lite3_release_autonomy.sh").read_text()
    assert "NAV_TEST_OVERRIDE.json" in helper
    assert 'rm -f -- "$test_override"' in helper


def test_deploy_script_never_starts_navigation_or_motion():
    deploy = (OPERATOR / "deploy_nav_obstacle_test.sh").read_text()
    assert "abx-fit-001" in deploy
    assert "COMMAND_SOURCE" in deploy and "NONE" in deploy
    assert "colcon build" in deploy
    assert "lite3-localization.service" in deploy
    assert "lite3-nav2-safety-monitor.service" in deploy
    assert "systemctl start lite3-nav2.service" not in deploy
    assert "systemctl start lite3-autonomy-command-source.service" not in deploy
    assert "cmd_vel" not in deploy
