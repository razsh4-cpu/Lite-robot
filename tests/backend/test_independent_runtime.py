from dataclasses import replace
import pytest
from backend.lite3.runtime import IndependentRuntime
from backend.lite3.live_navigation import LiveNavigationPort
from test_lite3_autonomy import setup_backend
from test_live_navigation import Transport, Authority


def make_runtime(tmp_path):
    backend, _, ready = setup_backend(tmp_path)
    transport, authority = Transport(), Authority()
    class Observation:
        tracker = type("Tracker", (), {"pose": None})()
        def readiness(self, expected_source="NONE"):
            value = replace(ready, command_source=authority.source)
            value.validate(expected_source)
            return value
    port = LiveNavigationPort(transport, authority)
    runtime = IndependentRuntime(backend.goals, port, Observation(),
                                 lambda: None, {"gate_alert": "gate"})
    return runtime, transport, authority


def test_runtime_sequences_after_real_release_not_old_owner(tmp_path):
    runtime, transport, authority = make_runtime(tmp_path)
    runtime.start_patrol("short", ["entrance", "gate"])
    assert authority.source == "AUTONOMY"
    transport.outcome = "SUCCEEDED"
    runtime.step()
    assert len(transport.sent) == 2
    assert runtime.status()["patrol_state"] == "RUNNING"


def test_alert_interrupt_waits_for_stop_and_has_no_auto_resume(tmp_path):
    runtime, transport, authority = make_runtime(tmp_path)
    runtime.start_patrol("short", ["entrance", "gate"])
    runtime.handle_alert("gate_alert")
    assert runtime.status()["patrol_state"] == "PAUSED"
    transport.outcome = "SUCCEEDED"
    runtime.step()
    assert runtime.status()["alert_state"] == "AWAITING_DECISION"
    assert authority.source == "NONE"
    assert len(transport.sent) == 2


def test_unhealthy_active_runtime_stops_and_releases(tmp_path):
    runtime, _, authority = make_runtime(tmp_path)
    runtime.goto("gate")
    def unavailable(*a, **k): raise ValueError("scan stale")
    runtime.observation.readiness = unavailable
    runtime.step()
    assert authority.source == "NONE"
    assert runtime.status()["navigation_state"] == "FAILED"


def test_status_is_read_only(tmp_path):
    runtime, transport, authority = make_runtime(tmp_path)
    assert runtime.status()["navigation_state"] == "IDLE"
    assert not transport.sent
    assert authority.source == "NONE"


def test_delayed_zero_confirmation_does_not_lose_success_result(tmp_path):
    runtime, transport, authority = make_runtime(tmp_path)
    runtime.start_patrol("short", ["entrance", "gate"])
    transport.outcome = "SUCCEEDED"
    authority.zero = False
    runtime.step()
    assert runtime.backend.navigation_state == "STOPPING"
    assert len(transport.sent) == 1
    authority.zero = True
    runtime.step()
    assert runtime.backend.patrol_state == "RUNNING"
    assert len(transport.sent) == 2
