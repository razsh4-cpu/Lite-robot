"""Real port logic tested against an in-memory Nav2 action boundary."""
import pytest
from backend.lite3.live_navigation import LiveNavigationPort


class Transport:
    def __init__(self):
        self.accepted = True
        self.outcome = None
        self.cancelled = False
        self.cancel_ok = True
        self.pending = False
        self.sent = []
    def send(self, goal):
        self.sent.append(goal)
        self.outcome = None
        return "future"
    def accepted_handle(self, future, timeout):
        if self.pending:
            raise TimeoutError("goal acceptance unknown")
        return "handle" if self.accepted else None
    def result(self, handle):
        return self.outcome
    def cancel(self, handle, timeout):
        self.cancelled = True
        if self.cancel_ok:
            self.outcome = "CANCELLED"
        return self.cancel_ok


class Authority:
    def __init__(self):
        self.source = "NONE"
        self.zero = True
        self.releases = 0
        self.approved = True
    def acquire(self):
        if not self.approved or self.source != "NONE":
            raise RuntimeError("authority conflict or approval absent")
        self.source = "AUTONOMY"
    def release(self):
        self.releases += 1
        self.source = "NONE"
    def stopped(self):
        return self.zero, self.source


def setup():
    transport, authority = Transport(), Authority()
    return LiveNavigationPort(transport, authority), transport, authority


def test_submit_observe_success_and_confirm_release():
    port, transport, authority = setup()
    port.start("r1", {"frame_id": "map"})
    assert port.status()["state"] == "RUNNING"
    transport.outcome = "SUCCEEDED"
    assert port.poll() == ("r1", "SUCCEEDED")
    assert port.stop("r1").safe
    assert authority.source == "NONE"


def test_rejected_goal_releases_without_claiming_success():
    port, transport, authority = setup()
    transport.accepted = False
    with pytest.raises(RuntimeError, match="rejected"):
        port.start("r1", {})
    assert port.stop("r1").safe
    assert authority.source == "NONE"


@pytest.mark.parametrize("outcome", ["FAILED", "CANCELLED"])
def test_terminal_results_exposed(outcome):
    port, transport, _ = setup()
    port.start("r1", {})
    transport.outcome = outcome
    assert port.poll() == ("r1", outcome)
    assert port.stop("r1").safe


def test_cancel_requires_terminal_and_zero_confirmation():
    port, transport, authority = setup()
    port.start("r1", {})
    transport.cancel_ok = False
    stopped = port.stop("r1")
    assert not stopped.safe
    assert authority.source == "NONE"  # suppress output even if cancel stalls
    with pytest.raises(RuntimeError):
        port.start("r2", {})
    transport.outcome = "CANCELLED"
    assert port.stop("r1").safe


def test_nonzero_confirmation_blocks_new_goals():
    port, _, authority = setup()
    port.start("r1", {})
    authority.zero = False
    assert not port.stop("r1").safe
    with pytest.raises(RuntimeError):
        port.start("r2", {})
    authority.zero = True
    assert port.stop("r1").safe


def test_late_acceptance_is_cancelled_not_forgotten():
    port, transport, authority = setup()
    transport.pending = True
    with pytest.raises(TimeoutError):
        port.start("r1", {})
    assert not port.stop("r1").safe
    assert authority.source == "NONE"
    transport.pending = False
    assert port.stop("r1").safe
    assert transport.cancelled


def test_foreign_source_is_never_released():
    port, transport, authority = setup()
    authority.source = "OTHER"
    with pytest.raises(RuntimeError):
        port.start("r1", {})
    assert authority.releases == 0
    assert transport.sent == []


def test_wrong_request_cannot_cancel_current_mission():
    port, transport, authority = setup()
    port.start("r1", {})
    assert not port.stop("different").safe
    assert not transport.cancelled
    assert authority.source == "AUTONOMY"


def test_physical_adapter_stops_before_waiting_for_cancel():
    port, transport, authority = setup()
    port.start("r1", {})
    original = transport.cancel
    def cancel(handle, timeout):
        assert authority.source == "NONE"
        return original(handle, timeout)
    transport.cancel = cancel
    assert port.stop("r1").safe


def test_send_exception_is_not_treated_as_confirmed_cancellation():
    port, transport, authority = setup()
    def broken_send(goal):
        raise RuntimeError("send outcome unknown")
    transport.send = broken_send
    with pytest.raises(RuntimeError):
        port.start("r1", {})
    assert not port.stop("r1").safe
    assert authority.source == "NONE"


@pytest.mark.parametrize("status,code,expected", [(4, 0, "SUCCEEDED"),
    (4, 2, "FAILED"), (4, None, "FAILED"), (5, 0, "CANCELLED"), (6, 0, "FAILED"), (2, 0, None)])
def test_ros_terminal_result_mapping(status, code, expected):
    from types import SimpleNamespace
    from backend.lite3.live_navigation import RosNav2Transport
    transport = RosNav2Transport.__new__(RosNav2Transport)
    handle = object()
    wrapped = SimpleNamespace(status=status, result=SimpleNamespace(error_code=code))
    if code is None:
        wrapped.result = SimpleNamespace()
    transport.results = {id(handle): SimpleNamespace(done=lambda: True, result=lambda: wrapped)}
    assert transport.result(handle) == expected


def test_partial_acquisition_cleanup_can_be_retried():
    port, transport, authority = setup()
    authority.started = False
    def acquire():
        authority.started = True
        authority.source = "AUTONOMY"
        raise RuntimeError("start and first cleanup failed")
    authority.acquire = acquire
    with pytest.raises(RuntimeError):
        port.start("r1", {})
    authority.zero = False
    assert not port.stop("r1").safe
    authority.zero = True
    assert port.stop("r1").safe
    assert authority.source == "NONE"
    assert not transport.sent


def test_rejection_proof_survives_delayed_zero_retry():
    port, transport, authority = setup()
    transport.accepted = False
    with pytest.raises(RuntimeError):
        port.start("r1", {})
    authority.zero = False
    assert not port.stop("r1").safe
    authority.zero = True
    assert port.stop("r1").safe
