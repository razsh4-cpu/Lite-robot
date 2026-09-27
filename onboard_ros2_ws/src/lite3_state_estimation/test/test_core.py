import math
from types import SimpleNamespace

import pytest

from lite3_state_estimation.core import (
    JOINT_NAMES,
    PlanarStartupOrigin,
    decode_joint_state,
    decode_robot_state,
    feedback_is_fresh,
)


def robot_state():
    return SimpleNamespace(
        robot_basic_state=6,
        battery_level=72.0,
        rpy=(1.0, -2.0, 90.0),
        rpy_vel=(0.1, 0.2, 0.3),
        xyz_acc=(0.0, 0.0, 9.81),
        pos_world=(1.25, -0.5, 1.57),
        vel_world=(0.4, 0.1, 0.2),
        vel_body=(0.3, -0.2, 0.1),
    )


def test_robot_state_conversion_is_finite_and_unit_correct():
    result = decode_robot_state(robot_state())
    assert result["basic_state"] == 6
    assert result["battery"] == 72.0
    assert result["rpy"][2] == pytest.approx(math.pi / 2)
    assert result["linear_acceleration"][2] == pytest.approx(9.81)
    assert sum(v * v for v in result["orientation"]) == pytest.approx(1.0)


def test_nonfinite_robot_state_is_rejected():
    state = robot_state()
    state.pos_world = (float("nan"), 0.0, 0.0)
    with pytest.raises(ValueError):
        decode_robot_state(state)


def test_joint_state_sign_and_missing_fields_are_honest():
    raw = SimpleNamespace(**{name: i / 10.0 for i, name in enumerate(JOINT_NAMES)})
    positions = decode_joint_state(raw)
    assert len(positions) == 12
    assert positions[7] == pytest.approx(-0.7)


def test_feedback_freshness_rejects_startup_stale_and_backward_time():
    assert not feedback_is_fresh(None, 10.0, 0.3)
    assert feedback_is_fresh(9.8, 10.0, 0.3)
    assert not feedback_is_fresh(9.6, 10.0, 0.3)
    assert not feedback_is_fresh(10.1, 10.0, 0.3)


def test_startup_origin_makes_first_nonzero_pose_identity():
    origin = PlanarStartupOrigin()
    assert origin.transform(2.0, -3.0, 1.2) == pytest.approx(
        (0.0, 0.0, 0.0, True))


def test_startup_origin_applies_inverse_se2_and_wraps_yaw():
    origin = PlanarStartupOrigin()
    origin.transform(1.0, 2.0, math.pi / 2)
    # At a 90-degree initial heading, world +Y is local +X.
    assert origin.transform(1.0, 3.0, -math.pi + 0.1) == pytest.approx(
        (1.0, 0.0, math.pi / 2 + 0.1, False))


def test_startup_origin_never_relatches_during_process_lifetime():
    origin = PlanarStartupOrigin()
    origin.transform(5.0, 6.0, 0.0)
    assert origin.transform(6.0, 6.0, 0.0) == pytest.approx(
        (1.0, 0.0, 0.0, False))
    assert origin.origin == (5.0, 6.0, 0.0)
