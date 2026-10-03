import json
import time
from types import SimpleNamespace
import pytest
from backend.lite3.autonomy_service import SystemdAutonomy


def test_unapproved_service_cannot_start(tmp_path):
    calls = []
    service = SystemdAutonomy(tmp_path, motion_approved=False,
                             run=lambda args, **kwargs: calls.append(args))
    with pytest.raises(RuntimeError, match="approval"):
        service.acquire()
    assert not calls


def test_service_reuses_existing_owner_and_checks_zero(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE")
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        if "start" in args:
            (tmp_path / "COMMAND_SOURCE").write_text("AUTONOMY")
        if "stop" in args:
            (tmp_path / "COMMAND_SOURCE").write_text("NONE")
        if args[0] == "journalctl":
            return SimpleNamespace(returncode=0, stdout=json.dumps({
                "__REALTIME_TIMESTAMP": str(int(time.time() * 1e6)),
                "MESSAGE": "enabled=false forward=0.00 lateral=0.00 yaw=0.00 telemetry_fresh=true command_source=NONE"}))
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            "high_level_healthy": True, "telemetry_fresh": True,
            "velocities_zero": True, "motion_enabled": False}))
    service = SystemdAutonomy(tmp_path, True, guard=tmp_path / "guard.py", run=run)
    service.acquire()
    assert service.source() == "AUTONOMY"
    service.release()
    assert service.stopped() == (True, "NONE")
    assert all("lite3-autonomy-command-source.service" in c for c in calls[:2])


@pytest.mark.parametrize("source", ["AUTONOMY", "OTHER", "UNKNOWN"])
def test_existing_owner_refuses_without_service_changes(tmp_path, source):
    (tmp_path / "COMMAND_SOURCE").write_text(source)
    calls = []
    service = SystemdAutonomy(tmp_path, True, run=lambda *a, **k: calls.append(a))
    with pytest.raises(RuntimeError):
        service.acquire()
    assert not calls


def test_missing_or_failed_zero_confirmation_is_not_safe(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE")
    service = SystemdAutonomy(tmp_path, True, run=lambda *a, **k:
                              SimpleNamespace(returncode=0, stdout="{}"))
    assert service.stopped() == (False, "NONE")


def test_old_zero_log_does_not_confirm_current_stop(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE")
    def run(args, **kwargs):
        if args[0] == "journalctl":
            value = {"__REALTIME_TIMESTAMP": "1", "MESSAGE":
                     "enabled=false forward=0 lateral=0 yaw=0 telemetry_fresh=true command_source=NONE"}
        else:
            value = {"high_level_healthy": True, "telemetry_fresh": True,
                     "velocities_zero": True, "motion_enabled": False}
        return SimpleNamespace(returncode=0, stdout=json.dumps(value))
    service = SystemdAutonomy(tmp_path, True, run=run)
    service.stop_requested_at = time.time()
    assert service.stopped() == (False, "NONE")


def test_parallel_backend_cannot_share_one_adapter_start(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE")
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        if "start" in args:
            # Model the second process observing NONE during the first startup.
            other = SystemdAutonomy(tmp_path, True, run=lambda *a, **k:
                                    SimpleNamespace(returncode=0, stdout=""))
            with pytest.raises(RuntimeError, match="backend"):
                other.acquire()
            (tmp_path / "COMMAND_SOURCE").write_text("AUTONOMY")
        if "stop" in args:
            (tmp_path / "COMMAND_SOURCE").write_text("NONE")
        return SimpleNamespace(returncode=0, stdout="{}")
    first = SystemdAutonomy(tmp_path, True, run=run)
    first.acquire()
    first.release()
    first.complete()
