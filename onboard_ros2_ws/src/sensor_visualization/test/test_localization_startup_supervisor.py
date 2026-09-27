import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
STATE_ESTIMATION = ROOT.parent / "lite3_state_estimation"


def test_localization_service_uses_bounded_supervisor_not_execstartpre():
    unit = (ROOT / "systemd/lite3-localization.service").read_text(
        encoding="utf-8")
    assert "lite3_localization_supervisor" in unit
    assert "ExecStartPre=" not in unit
    assert "Restart=no" in unit


def test_supervisor_retries_clean_stack_and_never_commands_motion():
    text = (ROOT / "scripts/lite3_localization_supervisor.sh").read_text(
        encoding="utf-8")
    assert "LITE3_LOCALIZATION_ATTEMPTS:-3" in text
    assert "LITE3_DDS_CLEANUP_SECONDS:-10" in text
    assert "stop_child" in text
    assert "LOCALIZATION_STARTUP_STATE" in text
    assert "STARTUP_FAILED" in text
    assert "/cmd_vel" not in text
    assert "AUTONOMY" not in text


def test_lifecycle_helper_has_bounded_transitions_and_exact_stages():
    text = (ROOT / "scripts/lite3_localization_lifecycle_ready.py").read_text(
        encoding="utf-8")
    for state in ("WAITING_FOR_MAP_SERVER", "WAITING_FOR_AMCL",
                  "UNLOCALIZED", "STARTUP_FAILED"):
        assert state in text
    assert "for attempt in range(1, 4)" in text
    assert '"map", "odom"' in text
    assert '"/amcl_pose"' in text
    assert "/cmd_vel" not in text


def test_input_gate_reports_scan_and_odom_wait_states():
    text = (ROOT / "scripts/lite3_ros_inputs_ready.py").read_text(
        encoding="utf-8")
    assert "WAITING_FOR_ODOM" in text
    assert "WAITING_FOR_SCAN" in text
    assert "STARTUP_FAILED" in text


def test_launch_has_one_external_lifecycle_owner():
    launch = (STATE_ESTIMATION / "launch/day1_localization.launch.py").read_text(
        encoding="utf-8")
    assert 'executable="map_server"' in launch
    assert 'executable="amcl"' in launch
    assert "nav2_lifecycle_manager" not in launch


def test_three_good_cycles_publish_navigation_ready():
    guard = (STATE_ESTIMATION / "lite3_state_estimation/localization_guard.py").read_text(
        encoding="utf-8")
    assert "self._good_cycles >= 3" in guard
    assert '"NAVIGATION_READY"' in guard


def test_operator_status_exposes_startup_stage_and_error():
    manager = (ROOT / "scripts/lite3_map_manager.py").read_text(
        encoding="utf-8")
    cli = (ROOT.parents[2] / "operator/lite3_map_cli.py").read_text(
        encoding="utf-8")
    assert '"localization_startup"' in manager
    assert '"localization_startup_error"' in manager
    assert '("STARTUP",' in cli
    assert '== "STARTUP_FAILED"' in cli


def test_nav2_and_autonomy_require_navigation_ready():
    preflight = (ROOT / "scripts/lite3_nav2_preflight.py").read_text(
        encoding="utf-8")
    autonomy = (ROOT / "scripts/lite3_autonomy_command_source.py").read_text(
        encoding="utf-8")
    gate = (ROOT / "scripts/lite3_localization_gate.py").read_text(
        encoding="utf-8")
    assert 'startup == "NAVIGATION_READY"' in preflight
    assert "startup == 'NAVIGATION_READY'" in autonomy
    assert 'startup != "NAVIGATION_READY"' in gate


def test_supervisor_runtime_records_bounded_input_failure(tmp_path):
    gate = tmp_path / "gate"
    gate.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    gate.chmod(0o755)
    state = tmp_path / "state"
    env = os.environ.copy()
    env.update({
        "LITE3_STATE_DIR": str(state),
        "LITE3_INPUT_GATE": str(gate),
        "LITE3_LOCALIZATION_ATTEMPTS": "1",
        "LITE3_DDS_CLEANUP_SECONDS": "0",
        "LITE3_SKIP_ROS_ENV": "true",
    })
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/lite3_localization_supervisor.sh")],
        env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=5, check=False)
    assert result.returncode == 1
    assert (state / "LOCALIZATION_STARTUP_STATE").read_text().strip() == "STARTUP_FAILED"
    assert "input readiness failed" in (state / "LOCALIZATION_STARTUP_ERROR").read_text()


def test_status_falls_back_to_atomic_guard_state_when_dds_sample_is_missed(monkeypatch):
    import importlib.util
    import sys
    from types import SimpleNamespace
    path = ROOT / "scripts/lite3_map_manager.py"
    spec = importlib.util.spec_from_file_location("lite3_map_manager_test", path)
    manager = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = manager
    spec.loader.exec_module(manager)
    monkeypatch.setattr(manager, "ros", lambda *_a, **_k: SimpleNamespace(stdout=""))
    values = {
        "LOCALIZATION_STATE": "UNLOCALIZED",
        "LOCALIZATION_SCORE": "0.734",
        "LOCALIZATION_STARTUP_ERROR": "confidence gate pending",
    }
    monkeypatch.setattr(manager, "runtime_state", lambda name, default="UNKNOWN": values.get(name, default))
    assert manager.parse_status(1) == {
        "state": "UNLOCALIZED", "match_fraction": 0.734,
        "reason": "confidence gate pending"}
