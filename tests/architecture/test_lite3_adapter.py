import pytest

from bipolix_lite3_adapter import (
    LITE3_CAPABILITIES,
    Lite3TelemetrySample,
    map_lite3_state,
    map_posture,
)
from bipolix_robot_interfaces.contracts import Capability, Health, Posture


@pytest.mark.parametrize(
    ("basic_state", "status", "expected"),
    [
        (6, None, Posture.STANDING),
        (None, "standing", Posture.STANDING),
        (None, "sitting", Posture.SITTING),
        (None, "lying", Posture.SITTING),
        (None, "damping", Posture.SITTING),
        (None, "standing_up", Posture.TRANSITIONING),
        (999, "unrecognized", Posture.UNKNOWN),
    ],
)
def test_posture_mapping(basic_state, status, expected):
    assert map_posture(basic_state, status) is expected


def test_ready_lite3_state_maps_to_generic_state():
    state = map_lite3_state(Lite3TelemetrySample(
        connected=True,
        telemetry_fresh=True,
        high_level_ready=True,
        basic_state=6,
        forward_mps=0.02,
        battery_percent=82.0,
    ))
    assert state.health is Health.READY
    assert state.posture is Posture.STANDING
    assert state.moving is True
    assert state.battery_percent == pytest.approx(82.0)


def test_offline_fault_and_stale_health_precedence():
    offline = map_lite3_state(Lite3TelemetrySample(False, False, False, fault="x"))
    fault = map_lite3_state(Lite3TelemetrySample(True, True, True, fault="x"))
    stale = map_lite3_state(Lite3TelemetrySample(True, False, True))
    assert offline.health is Health.OFFLINE
    assert fault.health is Health.FAULT
    assert stale.health is Health.DEGRADED


def test_invalid_battery_becomes_unknown_and_invalid_velocity_not_moving():
    state = map_lite3_state(Lite3TelemetrySample(
        connected=True,
        telemetry_fresh=True,
        high_level_ready=True,
        forward_mps=float("nan"),
        battery_percent=120.0,
    ))
    assert state.battery_percent is None
    assert state.moving is False


def test_lite3_reports_proven_planar_motion_and_state_capabilities():
    for capability in (
        Capability.MOTION_FORWARD,
        Capability.MOTION_BACKWARD,
        Capability.MOTION_LATERAL,
        Capability.MOTION_YAW,
        Capability.POSTURE_STAND,
        Capability.POSTURE_DOWN,
        Capability.ODOMETRY,
        Capability.BATTERY,
        Capability.TELEMETRY,
    ):
        assert LITE3_CAPABILITIES.has(capability)
