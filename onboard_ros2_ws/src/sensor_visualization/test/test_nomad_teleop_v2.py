import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CORE = load("lite3_nomad_teleop_core", "lite3_nomad_teleop_core.py")
LEASE = load("lite3_command_source_lease", "lite3_command_source_lease.py")


class Clock:
    def __init__(self, value=100.0):
        self.value = value

    def __call__(self):
        return self.value


def platform(now=100.0, source="NONE", owner=None, posture="STANDING"):
    return {
        "schema": "robot.platform_status", "schema_version": 1,
        "robot_id": "robodog_01", "observed_at": now,
        "connectivity": {"online": True, "gateway_health": "READY"},
        "robot_state": {"posture": posture, "battery_percent": 62.0,
                        "high_level_health": "READY"},
        "safety": {"command_source": source, "robot_side_owner": owner,
                   "safety_ready": True, "watchdog_state": "OK",
                   "motion_commands_supported": False},
    }


def authority(now=100.0, state="RESERVED"):
    return {
        "schema": "robot.control_authority", "schema_version": 1,
        "robot_id": "robodog_01", "state": state,
        "session_id": "session-a", "operator_lease_id": "lease-a",
        "lease_generation": 4, "authority_id": "authority-a",
        "control_epoch": 7, "expires_at": now + 3.0,
        "published_at": now, "requested_source": "LAPTOP_XBOX",
        "command_source": "NONE", "motion_commands_supported": False,
    }


def intent(sequence, action="ZERO", now=100.0, **changes):
    value = {
        "schema": "robot.teleop_intent", "schema_version": 2,
        "robot_id": "robodog_01", "intent_id": f"intent-{sequence}",
        "session_id": "session-a", "operator_lease_id": "lease-a",
        "lease_generation": 4, "authority_id": "authority-a",
        "control_epoch": 7, "sequence": sequence, "action": action,
        "vx": 0.0, "vy": 0.0, "wz": 0.0,
        "deadman_active": False, "issued_at": now,
        "expires_at": now + 0.25, "execution_mode": "PHYSICAL_MANUAL",
    }
    if action == "DRIVE":
        value.update(vx=0.05, deadman_active=True)
    value.update(changes)
    return value


def test_v2_requires_neutral_then_fresh_continuous_deadman_but_output_is_blocked():
    clock = Clock()
    machine = CORE.PhysicalTeleopMachine("robodog_01", clock=clock,
                                         physical_output_enabled=False)
    rejected = machine.handle(intent(0, "DRIVE"), platform(), authority())
    assert rejected.status["reason"] == "NEUTRAL_REQUIRED"
    armed = machine.handle(intent(1), platform(), authority())
    assert armed.status["state"] == "ARMED"
    drive = machine.handle(intent(2, "DRIVE"), platform(), authority())
    assert drive.acquire is True
    assert drive.joy.axes == [0.0] * 8
    assert drive.joy.buttons == [0] * 15
    assert drive.status["state"] == "OUTPUT_DISABLED"
    assert drive.status["physical_output_enabled"] is False
    assert drive.status["physical_output_performed"] is False
    released = machine.handle(intent(3), platform(), authority())
    assert released.release is True
    assert released.status["result"] == "ZEROED"


def test_enabled_conversion_uses_strict_limits_and_rb_button():
    machine = CORE.PhysicalTeleopMachine(
        "robodog_01", clock=Clock(), physical_output_enabled=True)
    machine.handle(intent(0), platform(), authority())
    decision = machine.handle(intent(1, "DRIVE", vx=.10, vy=-.05, wz=.20),
                              platform(), authority())
    assert decision.status["state"] == "ACTIVE"
    assert decision.joy.buttons[10] == 1
    shaped = CORE.joy_to_velocity(decision.joy)
    assert shaped == (.10, -.05, .20)


def test_watchdog_zeroes_releases_and_requires_new_neutral():
    clock = Clock()
    machine = CORE.PhysicalTeleopMachine(
        "robodog_01", clock=clock, physical_output_enabled=True)
    machine.handle(intent(0), platform(), authority())
    machine.handle(intent(1, "DRIVE"), platform(), authority())
    clock.value += .301
    stopped = machine.tick(platform(clock.value), authority(clock.value))
    assert stopped.release is True
    assert stopped.joy.axes == [0.0] * 8
    assert stopped.status["state"] == "WATCHDOG_STOPPED"
    blocked = machine.handle(intent(2, "DRIVE", now=clock.value),
                             platform(clock.value), authority(clock.value))
    assert blocked.status["reason"] == "NEUTRAL_REQUIRED"


def test_identity_sequence_freshness_bounds_and_posture_fail_closed():
    for request, reason in (
        (intent(0, control_epoch=8), "AUTHORITY_MISMATCH"),
        (intent(0, authority_id="other"), "AUTHORITY_MISMATCH"),
        (intent(0, vx=float("nan")), "MALFORMED_REQUEST"),
        (intent(0, "DRIVE", vx=.11), "VELOCITY_OUT_OF_RANGE"),
        (intent(0, expires_at=99.0), "REQUEST_EXPIRED"),
    ):
        result = CORE.PhysicalTeleopMachine("robodog_01", clock=Clock()).handle(
            request, platform(), authority())
        assert result.status["reason"] == reason
    bad_posture = CORE.PhysicalTeleopMachine("robodog_01", clock=Clock()).handle(
        intent(0), platform(posture="SITTING"), authority())
    assert bad_posture.status["reason"] == "POSTURE_NOT_STANDING"


def test_replay_and_epoch_change_clear_authorization():
    machine = CORE.PhysicalTeleopMachine("robodog_01", clock=Clock())
    first = machine.handle(intent(0), platform(), authority())
    assert first.status["state"] == "ARMED"
    machine.handle(intent(1, "DRIVE"), platform(), authority())
    replay = machine.handle(intent(1, "DRIVE"), platform(), authority())
    assert replay.status["reason"] == "SEQUENCE_REPLAY"
    assert replay.release is True
    next_authority = authority(); next_authority["control_epoch"] = 8
    changed = machine.tick(platform(), next_authority)
    assert changed.status["state"] == "WAITING_FOR_NEUTRAL"
    assert changed.release is False


def test_laptop_lease_records_and_clears_matching_remote_owner(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE\n")
    lease = LEASE.LaptopXboxLease(tmp_path)
    owner = {"authority_id": "authority-a", "control_epoch": 7,
             "lease_generation": 4, "session_id": "session-a"}
    assert lease.acquire(owner)
    assert lease.owner() == "LAPTOP_XBOX"
    assert lease.remote_owner()["authority_id"] == "authority-a"
    lease.release()
    assert lease.owner() == "NONE"
    assert lease.remote_owner() is None


def test_service_is_exclusive_and_output_disabled_by_default():
    unit = (ROOT / "systemd/lite3-nomad-teleop-adapter.service").read_text()
    assert "Conflicts=lite3-laptop-xbox-source.service" in unit
    assert "Conflicts=nomad-bipolix-teleop-validator.service" in unit
    assert "physical-output-enabled false" in unit
    assert "require_deadman:=true" not in unit  # HIGH-LEVEL owns this parameter.


def test_adapter_has_no_vendor_udp_cmd_vel_nav2_or_posture_surface():
    text = (SCRIPTS / "lite3_nomad_teleop_adapter.py").read_text()
    for forbidden in (
        "sendto(", "SOCK_DGRAM", "/cmd_vel", "NavigateToPose",
        "SIT_STAND", "VEL_FORWARD", "43893", "COMMAND_SOURCE.write_text",
        "owner.lock",
    ):
        assert forbidden not in text
