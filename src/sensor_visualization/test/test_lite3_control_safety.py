"""Offline-only tests for every Lite3 ROS command safety gate."""

import importlib.util
import math
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


manual = load("lite3_manual_axis_control")
adapter = load("lite3_cmd_vel_adapter")
xbox = load("lite3_xbox_cmd_vel_teleop")
arbiter = load("lite3_cmd_vel_arbiter")


def ready_manual(now=1.0):
    core = manual.SafetyCore(0.3, 0.10, 0.25, 25.0)
    core.update_robot_state(6, 50.0, now)
    core.update_command(0.10, now)
    core.update_yaw(0.25, now)
    core.update_deadman(True, now)
    return core


def test_manual_all_gates_fail_closed():
    core = ready_manual()
    assert core.output(1.0)[:3] == (True, 0.10, 0.25)
    core.update_robot_state(1, 50.0, 1.1)
    assert core.output(1.1)[1:3] == (0.0, 0.0)
    core = ready_manual()
    core.update_robot_state(6, 24.9, 1.1)
    assert core.output(1.1)[1:3] == (0.0, 0.0)
    core = ready_manual()
    core.update_deadman(False, 1.1)
    assert core.output(1.1)[1:3] == (0.0, 0.0)
    assert ready_manual().output(1.301)[1:3] == (0.0, 0.0)


def test_nonfinite_and_limits():
    core = ready_manual()
    core.update_command(math.nan, 1.0)
    core.update_yaw(math.inf, 1.0)
    assert core.output(1.0)[1:3] == (0.0, 0.0)
    core = ready_manual()
    core.update_command(100.0, 1.0)
    core.update_yaw(-100.0, 1.0)
    assert core.output(1.0)[1:3] == (0.10, -0.25)


def test_cmd_vel_adapter_deadman_timeout_and_lateral_rejection():
    core = adapter.CmdVelCore(0.3, 1.0, 1.0, 0.10, 0.25)
    core.update_command(0.08, 999.0, 0.20, 1.0)
    core.update_deadman(True, 1.0)
    assert core.output(1.0) == (True, 0.08, 0.20, "enabled")
    assert core.output(1.301)[1:3] == (0.0, 0.0)


def test_xbox_malformed_release_timeout_and_scaling():
    core = xbox.XboxTeleopCore()
    core.update([], [], 1.0)
    assert core.output(1.0).reason == "joy_invalid"
    axes = [0.0, 1.0, -1.0]
    buttons = [0] * 15
    core.update(axes, buttons, 2.0)
    assert core.output(2.0).reason == "rb_released"
    buttons[10] = 1
    core.update(axes, buttons, 3.0)
    value = core.output(3.0)
    assert (value.forward, value.yaw) == (0.10, -0.25)
    assert core.output(3.301).reason == "joy_stale"


def test_wire_mapping_is_fixed_and_finite():
    assert manual.normalized_to_raw(0.10) == 9174
    assert manual.normalized_to_raw(-0.10) == -9175
    assert manual.normalized_to_raw(-0.25, manual.HARD_MAX_YAW) == -13107


def test_arbiter_exclusive_source_and_switch_zero():
    core = arbiter.ArbiterCore(0.3, "xbox")
    core.update_command("xbox", 0.1, 0.0, 0.2, 1.0)
    core.update_deadman("xbox", True, 1.0)
    core.update_command("nav2", -0.1, 0.0, -0.2, 1.0)
    core.update_deadman("nav2", True, 1.0)
    assert core.output(1.0).source == "xbox"
    assert core.output(1.0).forward == 0.1
    assert core.select("none")
    assert not core.output(1.0).enabled
    assert not core.select("invalid")
    assert core.selected == "none"
