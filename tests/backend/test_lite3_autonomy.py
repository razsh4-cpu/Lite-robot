"""Offline orchestration against a recording navigation port; never ROS."""
import math
from dataclasses import replace
from pathlib import Path

import pytest

from backend.lite3.autonomy import (
    AutonomyBackend, Readiness, RecordingNavigation, SavedGoals, StopConfirmation,
)


def setup_backend(tmp_path):
    registry = tmp_path / "goals.yaml"
    registry.write_text("map: Home_Map\nframe_id: map\nlocations:\n"
                        "  gate: {configured: true, x: 1, y: 2, yaw: 0.5}\n"
                        "  entrance: {configured: true, x: 0, y: 0, yaw: 0}\n"
                        "  parking: {configured: false, x: null, y: null, yaw: null}\n")
    goals = SavedGoals.load(registry, "sha256:fixture-map")
    port = RecordingNavigation()
    ready = Readiness("sha256:fixture-map", (0.9, 0.91, 0.92), True, "NONE")
    backend = AutonomyBackend(goals, port, {"gate_alert": "gate"})
    return backend, port, ready


def test_saved_goal_reuses_registry_and_generates_map_pose(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.goto("gate", ready)
    goal = port.requests[-1][1]
    assert goal["frame_id"] == "map"
    assert goal["position"] == {"x": 1.0, "y": 2.0, "z": 0.0}
    assert goal["orientation"]["z"] == pytest.approx(math.sin(0.25))
    assert backend.status()["current_goal"] == "gate"


@pytest.mark.parametrize("change", [
    {"map_identity": "other"}, {"map_identity": ""},
    {"localization_samples": (0.9, 0.79, 0.9)},
    {"localization_samples": (0.9, 0.9)},
    {"localization_samples": (0.9, float("nan"), 0.9)},
    {"prerequisites_verified": False}, {"command_source": "LAPTOP_XBOX"},
])
def test_unready_or_wrong_map_never_dispatches(tmp_path, change):
    backend, port, ready = setup_backend(tmp_path)
    with pytest.raises(ValueError):
        backend.goto("gate", replace(ready, **change))
    assert port.requests == []


def test_unknown_and_disabled_goals_never_dispatch(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    for name in ("missing", "parking"):
        with pytest.raises(ValueError):
            backend.goto(name, ready)
    assert port.requests == []


def test_patrol_validates_entire_route_before_first_goal(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    with pytest.raises(ValueError):
        backend.start_patrol("bad", ["gate", "parking"], ready)
    assert port.requests == []


def test_patrol_sequences_waypoints_and_stops_on_completion(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.start_patrol("route", ["entrance", "gate"], ready)
    first = backend.request_id
    backend.navigation_result(first, "SUCCEEDED", ready)
    assert [goal[1]["position"]["x"] for goal in port.requests] == [0, 1]
    assert backend.status()["current_waypoint"] == 1
    backend.navigation_result(backend.request_id, "SUCCEEDED", ready)
    assert backend.patrol_state == "COMPLETED"
    assert backend.navigation_state == "ARRIVED"
    assert port.stop_calls == 2


def test_pause_resume_and_idempotent_cancel(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.start_patrol("route", ["entrance", "gate"], ready)
    old = backend.request_id
    backend.pause_patrol()
    assert backend.patrol_state == "PAUSED"
    assert not backend.navigation_result(old, "SUCCEEDED", ready)
    backend.resume_patrol(ready)
    assert backend.request_id != old
    assert len(port.requests) == 2
    backend.cancel_patrol()
    count = port.stop_calls
    backend.cancel_patrol()
    assert port.stop_calls == count
    assert backend.patrol_state == "CANCELLED"


def test_navigation_failure_never_advances_patrol(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.start_patrol("route", ["entrance", "gate"], ready)
    backend.navigation_result(backend.request_id, "ABORTED", ready)
    assert backend.patrol_state == "FAILED"
    assert backend.navigation_state == "FAILED"
    assert len(port.requests) == 1


def test_alert_suspends_patrol_and_never_automatically_resumes(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.start_patrol("route", ["entrance", "gate"], ready)
    backend.handle_alert("gate_alert", ready)
    assert backend.patrol_state == "PAUSED"
    assert backend.alert_state == "NAVIGATING"
    backend.navigation_result(backend.request_id, "SUCCEEDED", ready)
    assert backend.alert_state == "AWAITING_DECISION"
    assert len(port.requests) == 2
    backend.resume_patrol(ready)
    assert backend.current_goal == "entrance"


def test_unknown_alert_does_not_interrupt_patrol(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.start_patrol("route", ["entrance", "gate"], ready)
    with pytest.raises(ValueError):
        backend.handle_alert("missing", ready)
    assert port.stop_calls == 0
    assert backend.patrol_state == "RUNNING"


def test_takeover_requires_confirmed_cancel_zero_release(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.goto("gate", ready)
    assert backend.prepare_manual_takeover() is True
    assert backend.command_source == "NONE"
    assert backend.navigation_state == "CANCELLED"
    assert port.stop_calls == 1


def test_failed_release_blocks_resume_and_takeover(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.goto("gate", ready)
    port.stop_confirmation = StopConfirmation(False, True, False, "AUTONOMY")
    assert backend.prepare_manual_takeover() is False
    assert backend.navigation_state == "STOPPING"
    with pytest.raises(ValueError):
        backend.goto("gate", ready)
    assert len(port.requests) == 1


def test_dispatch_exception_cleans_up_and_reports_failure(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    port.start_error = RuntimeError("transport unavailable")
    with pytest.raises(RuntimeError):
        backend.goto("gate", ready)
    assert backend.navigation_state == "FAILED"
    assert backend.command_source == "NONE"
    assert port.stop_calls == 1


def test_stale_readiness_aborts_current_navigation(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.goto("gate", ready)
    backend.check_readiness(replace(ready, prerequisites_verified=False))
    assert backend.navigation_state == "FAILED"
    assert port.stop_calls == 1


def test_backend_has_no_direct_velocity_vendor_or_frontend_path():
    root = Path(__file__).parents[2] / "backend/lite3"
    for path in (root / "autonomy.py",):
        source = path.read_text()
        for forbidden in ("create_publisher", "ActionClient", "socket.socket",
                          "owner.lock", "SIT_STAND", "import rclpy"):
            assert forbidden not in source


def test_live_binding_does_not_add_velocity_vendor_or_frontend_writers():
    root = Path(__file__).parents[2] / "backend/lite3"
    for path in root.glob("*.py"):
        source = path.read_text()
        for forbidden in ("create_publisher", "socket.socket", "SIT_STAND",
                          "geometry_msgs.msg import Twist", "import paho",
                          "import sable", "import nomad"):
            assert forbidden not in source, (path, forbidden)


def test_external_site_changes_invalidate_saved_goals(tmp_path):
    registry = tmp_path / "goals.yaml"
    registry.write_text("map: TestSite\nframe_id: map\nlocations:\n"
                        "  gate: {configured: true, x: 1, y: 2, yaw: 0}\n")
    image = tmp_path / "map.pgm"
    image.write_bytes(b"P5\n1 1\n255\n\xff")
    metadata = tmp_path / "map.yaml"
    metadata.write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n")
    goals = SavedGoals.for_site(registry, metadata)
    first = goals.goals["gate"].map_identity
    image.write_bytes(b"P5\n1 1\n255\n\x00")
    changed = SavedGoals.for_site(registry, metadata).goals["gate"].map_identity
    assert first != changed
    with pytest.raises(ValueError, match="incompatible"):
        goals.resolve("gate", changed)


def test_expired_readiness_never_dispatches(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    with pytest.raises(ValueError, match="stale"):
        backend.goto("gate", replace(ready, observed_monotonic=ready.observed_monotonic - 3))
    assert not port.requests


def test_takeover_cancels_paused_patrol(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.start_patrol("route", ["gate"], ready)
    backend.pause_patrol()
    assert backend.prepare_manual_takeover()
    assert backend.patrol_state == "CANCELLED"
    with pytest.raises(ValueError):
        backend.resume_patrol(ready)


def test_stop_exception_is_retryable_and_blocks_new_goal(tmp_path):
    backend, port, ready = setup_backend(tmp_path)
    backend.goto("gate", ready)
    original = port.stop
    def fail_stop(_request):
        raise RuntimeError("stop transport lost")
    port.stop = fail_stop
    assert not backend.prepare_manual_takeover()
    assert backend.command_source == "UNKNOWN"
    with pytest.raises(ValueError):
        backend.goto("gate", ready)
    port.stop = original
    assert backend.prepare_manual_takeover()
