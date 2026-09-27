import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import time


STATE_PACKAGE = Path(__file__).parents[2] / "lite3_state_estimation"
sys.path.insert(0, str(STATE_PACKAGE))
SCRIPT = Path(__file__).parents[1] / "scripts" / "xbox_lite3_motion_host_bridge.py"
SPEC = importlib.util.spec_from_file_location("xbox_bridge_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
Bridge = MODULE.XboxLite3MotionHostBridge


def bridge_ready():
    bridge = Bridge.__new__(Bridge)
    bridge.get_logger = lambda: SimpleNamespace(
        info=lambda *_args: None, warn=lambda *_args: None)
    bridge.max_forward = 0.10
    bridge.max_lateral = 0.10
    bridge.max_yaw = 0.10
    bridge._last_joy_time = None
    bridge._last_values = (0.0, 0.0, 0.0)
    bridge._last_raw_axes = (0.0, 0.0, 0.0)
    bridge._last_a_pressed = False
    bridge._last_authorize_pressed = False
    bridge._manual_authorized = True
    bridge._command_source = 'LOCAL_XBOX'
    bridge._read_command_source = lambda: 'LOCAL_XBOX'
    bridge._lease_is_held = lambda: True
    bridge._operator_rearm_required = False
    bridge._zero_on_source_loss = False
    bridge._deadman_pressed = False
    bridge.require_deadman = True
    bridge._center_required = False
    bridge._stand_pending = False
    bridge._motion_locked_after_stand = False
    bridge._awaiting_standing = False
    bridge._drive_reactivation_pending = False
    bridge._drive_ready = True
    bridge._robot_basic_state = bridge.STANDING_BASIC_STATE
    bridge._last_robot_state_time = time.monotonic()
    bridge._invalid_joy = False
    return bridge


def joy(*, forward=0.0, lateral=0.0, yaw=0.0, a=0, rb=0):
    buttons = [0] * 11
    buttons[Bridge.BUTTON_STAND] = a
    buttons[Bridge.BUTTON_DEADMAN] = rb
    axes = [0.0] * 3
    axes[Bridge.AXIS_LATERAL] = lateral
    axes[Bridge.AXIS_FORWARD] = forward
    axes[Bridge.AXIS_YAW] = yaw
    return SimpleNamespace(axes=axes, buttons=buttons)


def test_rb_is_required_and_release_forces_zero():
    bridge = bridge_ready()
    bridge._on_joy(joy(forward=1.0, rb=0))
    assert bridge._state() == (False, 0.0, 0.0, 0.0)

    bridge._on_joy(joy(forward=1.0, rb=1))
    enabled, forward, lateral, yaw = bridge._state()
    assert enabled is True
    assert (forward, lateral, yaw) == (0.10, 0.0, 0.0)

    bridge._on_joy(joy(forward=1.0, rb=0))
    assert bridge._state() == (False, 0.0, 0.0, 0.0)


def test_invalid_joy_clears_deadman():
    bridge = bridge_ready()
    bridge._on_joy(joy(rb=1))
    assert bridge._deadman_pressed is True
    bridge._on_joy(SimpleNamespace(axes=[0.0, 0.0, 0.0], buttons=[0]))
    assert bridge._deadman_pressed is False
    assert bridge._state() == (False, 0.0, 0.0, 0.0)


def test_stand_toggle_requires_centered_sticks_and_released_deadman():
    bridge = bridge_ready()
    bridge._on_joy(joy(a=1, rb=1))
    assert bridge._stand_pending is False

    bridge._last_a_pressed = False
    bridge._on_joy(joy(forward=0.2, a=1, rb=0))
    assert bridge._stand_pending is False

    bridge._last_a_pressed = False
    bridge._on_joy(joy(a=1, rb=0))
    assert bridge._stand_pending is True
    assert bridge._motion_locked_after_stand is True
    assert bridge._drive_ready is False


def test_no_deadman_mode_requires_center_after_arm_and_after_stale_input():
    bridge = bridge_ready()
    bridge.require_deadman = False
    bridge._center_required = True

    bridge._on_joy(joy(forward=1.0, rb=0))
    assert bridge._state() == (False, 0.0, 0.0, 0.0)

    bridge._on_joy(joy(rb=0))
    assert bridge._state() == (True, 0.0, 0.0, 0.0)

    bridge._on_joy(joy(forward=1.0, rb=0))
    assert bridge._state() == (True, 0.10, 0.0, 0.0)

    bridge._last_joy_time = time.monotonic() - bridge.JOY_TIMEOUT_S - 0.1
    assert bridge._state() == (False, 0.0, 0.0, 0.0)
    assert bridge._center_required is True


def test_fresh_runtime_cannot_move_until_centered_rb_authorizes():
    bridge = bridge_ready()
    bridge.require_deadman = False
    bridge._manual_authorized = False
    bridge._drive_ready = False
    bridge._awaiting_standing = True

    bridge._on_joy(joy(forward=1.0))
    assert bridge._state() == (False, 0.0, 0.0, 0.0)

    bridge._on_joy(joy(rb=1))
    assert bridge._manual_authorized is True
    assert bridge._drive_reactivation_pending is True
    assert bridge._center_required is True


def test_recreated_runtime_does_not_restore_authorization_or_velocity():
    first = bridge_ready()
    first.require_deadman = False
    first._on_joy(joy(forward=1.0))
    assert first._state()[1] == 0.10

    restarted = bridge_ready()
    restarted.require_deadman = False
    restarted._manual_authorized = False
    restarted._drive_ready = False
    restarted._center_required = True
    restarted._last_values = (0.0, 0.0, 0.0)
    assert restarted._state() == (False, 0.0, 0.0, 0.0)


def test_left_stick_lateral_sign_matches_robot_frame():
    bridge = bridge_ready()
    bridge.require_deadman = False
    bridge._on_joy(joy())
    bridge._on_joy(joy(lateral=1.0))
    enabled, forward, lateral, yaw = bridge._state()
    assert enabled is True
    assert (forward, lateral, yaw) == (0.0, -0.10, 0.0)


def test_velocity_uses_hardware_validated_full_manual_axis_codes():
    bridge = Bridge.__new__(Bridge)
    calls = []
    bridge.zero_only = False
    bridge.transmit = False
    bridge.codecs = SimpleNamespace(
        encode_simple_cmd=lambda code, value, command_type: calls.append(
            (code, value, command_type)) or b"packet"
    )

    bridge._emit_velocity(0.10, 0.0, 0.10)

    assert calls == [
        (MODULE.FORWARD_CODE, 9174, MODULE.COMMAND_TYPE),
        (MODULE.LATERAL_CODE, 0, MODULE.COMMAND_TYPE),
        (MODULE.YAW_CODE, -9175, MODULE.COMMAND_TYPE),
    ]


def test_full_scale_matches_vendor_signed_axis_range():
    assert Bridge.MAX_FORWARD == 1.0
    assert Bridge.MAX_LATERAL == 1.0
    assert Bridge.MAX_YAW == 1.0
    assert MODULE.normalized_to_raw(1.0, 1.0) == 32767
    assert MODULE.normalized_to_raw(-1.0, 1.0) == -32768


def test_source_release_clears_authorization_and_requests_one_zero():
    bridge = bridge_ready()
    bridge._read_command_source = lambda: "NONE"
    bridge._refresh_command_source()
    assert bridge._command_source == "NONE"
    assert bridge._manual_authorized is False
    assert bridge._drive_ready is False
    assert bridge._last_values == (0.0, 0.0, 0.0)
    assert bridge._zero_on_source_loss is True


def test_none_source_keeps_heartbeat_path_but_emits_only_one_release_zero():
    bridge = bridge_ready()
    bridge._command_source = "NONE"
    bridge._read_command_source = lambda: "NONE"
    bridge._zero_on_source_loss = True
    emitted = []
    bridge._emit_velocity = lambda *values: emitted.append(values)
    bridge.diagnostic_capture = None
    bridge._command_tick()
    bridge._command_tick()
    assert emitted == [(0.0, 0.0, 0.0)]


def test_reconnect_requires_neutral_then_fresh_operator_edge():
    bridge = bridge_ready()
    bridge.require_deadman = False
    bridge._manual_authorized = False
    bridge._drive_ready = False
    bridge._awaiting_standing = True
    bridge._operator_rearm_required = True

    bridge._on_joy(joy(rb=1))
    assert bridge._manual_authorized is False
    bridge._on_joy(joy())
    assert bridge._operator_rearm_required is False
    bridge._on_joy(joy(rb=1))
    assert bridge._manual_authorized is True
    assert bridge._drive_reactivation_pending is True


def test_laptop_xbox_uses_same_manual_authorization_and_motion_gates():
    bridge = bridge_ready()
    bridge._command_source = "LAPTOP_XBOX"
    bridge._read_command_source = lambda: "LAPTOP_XBOX"
    bridge._on_joy(joy(forward=1.0, rb=1))
    enabled, forward, lateral, yaw = bridge._state()
    assert enabled is True
    assert (forward, lateral, yaw) == (0.10, 0.0, 0.0)
    bridge._lease_is_held = lambda: False
    assert bridge._state() == (False, 0.0, 0.0, 0.0)
