import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts/lite3_platform_status_exporter.py"


def load_module():
    spec = importlib.util.spec_from_file_location("platform_status_exporter", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def exporter():
    return load_module()


def complete(now=100.0):
    return {
        "robot_id": "robot_01",
        "high_level_active": True,
        "telemetry_fresh": True,
        "posture": "standing",
        "battery_percent": 72.0,
        "command_source": "NONE",
        "robot_side_owner": None,
        "watchdog_state": "OK",
        "localization_state": "LOCALIZED",
        "localization_confidence": 0.91,
        "localization_ready": True,
        "localization_reason": None,
        "active_map": "Home_Map",
        "nav2_available": True,
        "nav2_ready": True,
        "nav2_state": "IDLE",
        "nav2_reason": None,
        "rplidar_available": True,
        "rplidar_fresh": True,
        "d455_available": True,
        "d455_fresh": True,
        "odometry_available": True,
        "odometry_fresh": True,
        "tf_available": True,
        "tf_fresh": True,
        "observed_at": now,
        "source_observed_at": now,
    }


def test_complete_snapshot_is_contract_valid_and_read_only(exporter):
    value = exporter.build_snapshot(complete(), now=100.0, sequence=7)
    assert value["schema"] == "robot.platform_status"
    assert value["schema_version"] == 1
    assert value["sequence"] == 7
    assert value["connectivity"] == {
        "online": True, "gateway_health": "READY", "gateway_reason": None}
    assert value["robot_state"] == {
        "posture": "STANDING", "battery_percent": 72.0,
        "high_level_health": "READY"}
    assert value["localization"]["confidence"] == .91
    assert value["safety"]["command_source"] == "NONE"
    assert value["safety"]["motion_commands_supported"] is False


def test_missing_and_partial_sources_never_default_healthy(exporter):
    value = exporter.build_snapshot({"robot_id": "robot_01"}, now=100.0, sequence=0)
    assert value["connectivity"]["online"] is False
    assert value["robot_state"]["posture"] == "UNAVAILABLE"
    assert value["robot_state"]["battery_percent"] is None
    assert value["robot_state"]["high_level_health"] == "UNAVAILABLE"
    assert value["localization"]["state"] == "UNAVAILABLE"
    assert all(not sensor["ready"] for sensor in value["sensors"].values())
    assert value["safety"]["safety_ready"] is False


def test_stale_source_fails_closed_but_retains_last_values(exporter):
    source = complete(now=90.0)
    value = exporter.build_snapshot(source, now=100.0, sequence=2, stale_after=3.0)
    assert value["connectivity"]["online"] is False
    assert value["connectivity"]["gateway_health"] == "STALE"
    assert value["robot_state"]["posture"] == "STALE"
    assert value["robot_state"]["battery_percent"] == 72.0
    assert value["localization"]["state"] == "STALE"
    assert value["safety"]["command_source"] == "STALE"
    assert value["safety"]["safety_ready"] is False


@pytest.mark.parametrize("source", [None, [], "bad", {"robot_id": ""}])
def test_malformed_source_becomes_explicit_unavailable(exporter, source):
    value = exporter.build_snapshot(source, now=100.0, sequence=1)
    assert value["connectivity"]["gateway_health"] == "UNAVAILABLE"
    assert value["safety"]["refusal_reason"]


def test_offline_robot_is_explicit(exporter):
    source = complete()
    source.update(high_level_active=True, telemetry_fresh=False)
    value = exporter.build_snapshot(source, now=100.0, sequence=1)
    assert value["connectivity"]["online"] is False
    assert value["robot_state"]["posture"] == "OFFLINE"
    assert value["robot_state"]["high_level_health"] == "DEGRADED"
    assert value["safety"]["safety_ready"] is False


def test_unknown_posture_or_required_navigation_sensor_blocks_safety(exporter):
    source = complete()
    source["posture"] = "unknown"
    assert exporter.build_snapshot(source, now=100.0)["safety"]["safety_ready"] is False
    source["posture"] = "standing"
    source["rplidar_fresh"] = False
    assert exporter.build_snapshot(source, now=100.0)["safety"]["safety_ready"] is False


def test_recovery_is_deterministic_and_restart_sequence_is_safe(exporter):
    failed = exporter.build_snapshot({}, now=100.0, sequence=0)
    recovered = exporter.build_snapshot(complete(now=101.0), now=101.0, sequence=0)
    assert failed["connectivity"]["online"] is False
    assert recovered["connectivity"]["online"] is True
    assert recovered["sequence"] == 0


def test_atomic_write_replaces_complete_json(exporter, tmp_path):
    path = tmp_path / "platform_status.json"
    path.write_text("old", encoding="utf-8")
    payload = exporter.build_snapshot(complete(), now=100.0, sequence=1)
    exporter.atomic_write_json(path, payload)
    assert json.loads(path.read_text(encoding="utf-8")) == payload
    assert not list(tmp_path.glob(".platform_status.json.*"))


def test_schema_rejects_nonfinite_and_bad_command_source(exporter):
    bad = complete()
    bad["battery_percent"] = float("nan")
    bad["command_source"] = "SOMETHING_ELSE"
    value = exporter.build_snapshot(bad, now=100.0, sequence=1)
    assert value["robot_state"]["battery_percent"] is None
    assert value["safety"]["command_source"] == "UNKNOWN"
    assert value["safety"]["safety_ready"] is False


def test_source_contains_no_motion_surface():
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "paho.mqtt", "create_publisher", "ActionClient", "sendto(",
        "SOCK_DGRAM", "/cmd_vel", "owner.lock\", \"w", "COMMAND_SOURCE\", \"w",
        "SIT_STAND", "NavigateToPose")
    for token in forbidden:
        assert token not in text
