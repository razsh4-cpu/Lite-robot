import importlib.util
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace


SCRIPT_DIR = Path(__file__).parents[1] / "scripts"
AUTONOMY_SCRIPT = SCRIPT_DIR / "lite3_autonomy_command_source.py"
SPEC = importlib.util.spec_from_file_location("autonomy_source", AUTONOMY_SCRIPT)
AUTONOMY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUTONOMY
SPEC.loader.exec_module(AUTONOMY)

STATE_PACKAGE = Path(__file__).parents[2] / "lite3_state_estimation"
sys.path.insert(0, str(STATE_PACKAGE))
BRIDGE_SCRIPT = SCRIPT_DIR / "xbox_lite3_motion_host_bridge.py"
BRIDGE_SPEC = importlib.util.spec_from_file_location("autonomy_bridge", BRIDGE_SCRIPT)
BRIDGE_MODULE = importlib.util.module_from_spec(BRIDGE_SPEC)
sys.modules[BRIDGE_SPEC.name] = BRIDGE_MODULE
BRIDGE_SPEC.loader.exec_module(BRIDGE_MODULE)
Bridge = BRIDGE_MODULE.XboxLite3MotionHostBridge


def test_cmd_vel_limits_and_axes_are_preserved():
    core = AUTONOMY.AutonomyCommandCore(
        timeout_s=0.30, max_forward=0.10, max_lateral=0.05, max_yaw=0.20)
    core.update(1.0, -1.0, 2.0, 10.0)
    output = core.output(10.1)
    assert output.enabled
    assert (output.forward, output.lateral, output.yaw) == (0.10, -0.05, 0.20)


def test_stale_or_invalid_cmd_vel_fails_zero():
    core = AUTONOMY.AutonomyCommandCore(timeout_s=0.30)
    core.update(0.08, 0.01, -0.10, 1.0)
    assert core.output(1.299).enabled
    stale = core.output(1.301)
    assert not stale.enabled and stale.reason == "stale"
    assert (stale.forward, stale.lateral, stale.yaw) == (0.0, 0.0, 0.0)
    core.update(math.nan, 0.0, 0.0, 2.0)
    invalid = core.output(2.0)
    assert not invalid.enabled and invalid.reason == "invalid"


def test_autonomy_lease_is_exclusive_and_releases_to_none(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE\n")
    first = AUTONOMY.CommandSourceLease(tmp_path)
    second = AUTONOMY.CommandSourceLease(tmp_path)
    assert first.acquire_autonomy()
    assert (tmp_path / "COMMAND_SOURCE").read_text().strip() == "AUTONOMY"
    assert not second.acquire_autonomy()
    first.release()
    assert (tmp_path / "COMMAND_SOURCE").read_text().strip() == "NONE"
    assert second.acquire_autonomy()
    second.release()


def test_autonomy_requires_fresh_localization_above_80_percent(tmp_path):
    state = tmp_path / "LOCALIZATION_STATE"
    score = tmp_path / "LOCALIZATION_SCORE"
    state.write_text("LOCALIZED\n")
    (tmp_path / "LOCALIZATION_STARTUP_STATE").write_text("NAVIGATION_READY\n")
    score.write_text("0.80\n")
    now = time.time()
    assert AUTONOMY.localization_ready(tmp_path, now=now)
    score.write_text("0.799\n")
    assert not AUTONOMY.localization_ready(tmp_path, now=now)
    score.write_text("0.95\n")
    state.write_text("UNLOCALIZED\n")
    assert not AUTONOMY.localization_ready(tmp_path, now=now)


def test_autonomy_rejects_stale_or_missing_localization(tmp_path):
    assert not AUTONOMY.localization_ready(tmp_path)
    state = tmp_path / "LOCALIZATION_STATE"
    score = tmp_path / "LOCALIZATION_SCORE"
    state.write_text("LOCALIZED\n")
    score.write_text("0.95\n")
    (tmp_path / "LOCALIZATION_STARTUP_STATE").write_text("NAVIGATION_READY\n")
    old = time.time() - 5.0
    for path in (state, score):
        path.touch()
        import os
        os.utime(path, (old, old))
    assert not AUTONOMY.localization_ready(tmp_path, max_age=2.5)


def autonomy_bridge():
    bridge = Bridge.__new__(Bridge)
    bridge.get_logger = lambda: SimpleNamespace(
        info=lambda *_args: None, warn=lambda *_args: None)
    bridge._command_source = "AUTONOMY"
    bridge._read_command_source = lambda: "AUTONOMY"
    bridge._lease_is_held = lambda: True
    bridge._last_autonomy_time = time.monotonic()
    bridge._last_autonomy_values = (0.10, -0.05, 0.20)
    bridge._autonomy_invalid = False
    bridge._autonomy_mode_ready = True
    bridge._autonomy_was_enabled = False
    bridge.autonomy_command_timeout_s = 0.30
    bridge._last_robot_state_time = time.monotonic()
    bridge._robot_basic_state = bridge.STANDING_BASIC_STATE
    bridge._zero_on_source_loss = False
    bridge._last_joy_time = None
    bridge._last_values = (0.0, 0.0, 0.0)
    bridge._last_raw_axes = (0.0, 0.0, 0.0)
    bridge._last_a_pressed = False
    bridge._last_authorize_pressed = False
    bridge._manual_authorized = False
    bridge._deadman_pressed = False
    bridge._center_required = True
    bridge._stand_pending = False
    bridge._motion_locked_after_stand = False
    bridge._awaiting_standing = True
    bridge._drive_reactivation_pending = False
    bridge._drive_ready = False
    bridge._operator_rearm_required = True
    bridge._invalid_joy = False
    bridge._was_enabled = False
    bridge.diagnostic_capture = None
    return bridge


def test_runtime_accepts_autonomy_only_with_source_lease_and_fresh_state():
    bridge = autonomy_bridge()
    assert bridge._autonomy_state() == (True, 0.10, -0.05, 0.20)
    bridge._lease_is_held = lambda: False
    assert bridge._autonomy_state() == (False, 0.0, 0.0, 0.0)


def test_runtime_rejects_stale_autonomy_command_and_stale_telemetry():
    bridge = autonomy_bridge()
    bridge._last_autonomy_time = time.monotonic() - 0.31
    assert bridge._autonomy_state() == (False, 0.0, 0.0, 0.0)
    bridge = autonomy_bridge()
    bridge._last_robot_state_time = time.monotonic() - bridge.TELEMETRY_TIMEOUT_S - 0.1
    assert bridge._autonomy_state() == (False, 0.0, 0.0, 0.0)


def test_source_transition_crosses_one_zero_and_never_restores_motion():
    bridge = autonomy_bridge()
    bridge._read_command_source = lambda: "NONE"
    emitted = []
    bridge._emit_velocity = lambda *values: emitted.append(values)
    bridge._refresh_command_source()
    bridge._command_tick()
    bridge._command_tick()
    assert emitted == [(0.0, 0.0, 0.0)]
    assert bridge._command_source == "NONE"
    assert bridge._last_autonomy_time is None
    assert bridge._last_autonomy_values == (0.0, 0.0, 0.0)


def test_xbox_source_cannot_replace_held_autonomy_lease(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE\n")
    autonomy = AUTONOMY.CommandSourceLease(tmp_path)
    xbox = AUTONOMY.CommandSourceLease(tmp_path)
    assert autonomy.acquire_autonomy()
    assert not xbox.acquire_autonomy()
    assert (tmp_path / "COMMAND_SOURCE").read_text().strip() == "AUTONOMY"
    autonomy.release()


def test_autonomy_adapter_owns_no_robot_udp_socket():
    text = AUTONOMY_SCRIPT.read_text(encoding="utf-8")
    assert "43897" not in text
    assert "sendto(" not in text
    assert "socket.socket" not in text


def test_autonomy_service_requires_explicit_start():
    unit = (Path(__file__).parents[1] / "systemd" /
            "lite3-autonomy-command-source.service").read_text(encoding="utf-8")
    assert "lite3-high-level-runtime.service" in unit
    assert "[Install]" not in unit
    assert "Restart=no" in unit


def test_autonomy_velocity_links_use_best_effort_sensor_qos():
    bridge_text = BRIDGE_SCRIPT.read_text(encoding="utf-8")
    source_text = AUTONOMY_SCRIPT.read_text(encoding="utf-8")
    assert "qos_profile_sensor_data" in bridge_text
    assert source_text.count("qos_profile_sensor_data") >= 3


def test_telemetry_tick_coalesces_udp_burst_to_latest_sample():
    class BurstSocket:
        def __init__(self):
            self.frames = [b"old", b"middle", b"latest"]

        def recvfrom(self, _size):
            if not self.frames:
                raise BlockingIOError
            return self.frames.pop(0), ("192.0.2.1", 43897)

    bridge = Bridge.__new__(Bridge)
    bridge._telemetry_socket = BurstSocket()
    bridge.codecs = SimpleNamespace(parse_robot_state=lambda raw: raw.decode())
    observed = []
    bridge._observe_robot_state = observed.append

    bridge._telemetry_tick()

    assert observed == ["latest"]


def test_telemetry_tick_keeps_latest_valid_state_when_burst_ends_in_noise():
    class BurstSocket:
        def __init__(self):
            self.frames = [b"valid", b"noise"]

        def recvfrom(self, _size):
            if not self.frames:
                raise BlockingIOError
            return self.frames.pop(0), ("192.0.2.1", 43897)

    bridge = Bridge.__new__(Bridge)
    bridge._telemetry_socket = BurstSocket()
    bridge.codecs = SimpleNamespace(
        parse_robot_state=lambda raw: "state" if raw == b"valid" else None)
    observed = []
    bridge._observe_robot_state = observed.append

    bridge._telemetry_tick()

    assert observed == ["state"]


def test_relocalization_mode_accepts_only_fresh_measured_status(tmp_path):
    now = 1000.0
    (tmp_path / "LOCALIZATION_STATE").write_text("UNLOCALIZED\n")
    (tmp_path / "LOCALIZATION_SCORE").write_text("0.55\n")
    import os
    os.utime(tmp_path / "LOCALIZATION_STATE", (now, now))
    os.utime(tmp_path / "LOCALIZATION_SCORE", (now, now))
    assert AUTONOMY.relocalization_inputs_ready(tmp_path, now=now)
    assert not AUTONOMY.relocalization_inputs_ready(tmp_path, now=now + 3.0)


def test_relocalization_is_explicit_and_does_not_weaken_normal_gate():
    text = AUTONOMY_SCRIPT.read_text(encoding="utf-8")
    assert "LITE3_RELOCALIZATION_APPROVED" in text
    assert "relocalization_mode" in text
    assert "elif not localization_ready" in text
