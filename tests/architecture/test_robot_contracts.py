import math
from pathlib import Path

import pytest

from bipolix_robot_interfaces.config import load_robot_platform_config
from bipolix_robot_interfaces.contracts import (
    Capability,
    MotionLimits,
    RobotCapabilities,
    VelocityCommand,
    validate_velocity,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "robots" / "lite3"


def test_lite3_configuration_loads_identity_capabilities_and_limits():
    config = load_robot_platform_config(CONFIG)
    assert config.identity.robot_id == "robot_01"
    assert config.identity.model == "Lite3 Venture"
    assert config.identity.adapter == "lite3"
    assert config.length_m == pytest.approx(0.610)
    assert config.width_m == pytest.approx(0.370)
    assert config.capabilities.has(Capability.MOTION_LATERAL)
    assert config.motion_limits.max_forward_mps == pytest.approx(0.10)
    assert config.motion_limits.max_lateral_mps == pytest.approx(0.05)
    assert config.topics.odometry == "/odom"
    assert config.safety["command_watchdog_s"] == pytest.approx(0.30)
    assert config.sensors["telemetry"]["single_receiver_required"] is True


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_velocity_rejects_non_finite_values(bad):
    config = load_robot_platform_config(CONFIG)
    with pytest.raises(ValueError, match="finite"):
        validate_velocity(
            VelocityCommand(linear_x=bad),
            config.motion_limits,
            config.capabilities,
        )


def test_velocity_rejects_limit_violation():
    config = load_robot_platform_config(CONFIG)
    with pytest.raises(ValueError, match="forward velocity"):
        validate_velocity(
            VelocityCommand(linear_x=0.101),
            config.motion_limits,
            config.capabilities,
        )


def test_velocity_rejects_unsupported_axis():
    limits = MotionLimits(0.1, 0.1, 0.05, 0.2)
    forward_only = RobotCapabilities(frozenset({Capability.MOTION_FORWARD}))
    with pytest.raises(ValueError, match="lateral motion"):
        validate_velocity(VelocityCommand(linear_y=0.01), limits, forward_only)


def test_valid_velocity_is_accepted():
    config = load_robot_platform_config(CONFIG)
    validate_velocity(
        VelocityCommand(linear_x=0.05, linear_y=-0.02, angular_z=0.1),
        config.motion_limits,
        config.capabilities,
    )


def test_generic_layer_has_no_robot_vendor_or_transport_dependency():
    generic = ROOT / "src" / "robot_interfaces"
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(generic.rglob("*.py"))
    )
    forbidden = (
        "DeepRobotics",
        "MotionSDK",
        "SIT_STAND",
        "43897",
        "bipolix_lite3_adapter",
    )
    for token in forbidden:
        assert token not in text
