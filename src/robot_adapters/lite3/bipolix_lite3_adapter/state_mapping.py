"""Normalize the deployed Lite3 HIGH-LEVEL state at the adapter boundary."""

from __future__ import annotations

from dataclasses import dataclass
import math

from bipolix_robot_interfaces.contracts import (
    Capability,
    Health,
    Posture,
    RobotCapabilities,
    RobotState,
)


# The deployed Motion Host bridge confirms basic state 6 as standing.
LITE3_STANDING_BASIC_STATE = 6

LITE3_CAPABILITIES = RobotCapabilities(frozenset({
    Capability.MOTION_FORWARD,
    Capability.MOTION_BACKWARD,
    Capability.MOTION_LATERAL,
    Capability.MOTION_YAW,
    Capability.POSTURE_STAND,
    Capability.POSTURE_DOWN,
    Capability.ODOMETRY,
    Capability.BATTERY,
    Capability.TELEMETRY,
}))


@dataclass(frozen=True)
class Lite3TelemetrySample:
    """Vendor-derived values already decoded by the existing runtime."""

    connected: bool
    telemetry_fresh: bool
    high_level_ready: bool
    basic_state: int | None = None
    posture_status: str | None = None
    forward_mps: float = 0.0
    lateral_mps: float = 0.0
    yaw_rps: float = 0.0
    battery_percent: float | None = None
    fault: str | None = None


def map_posture(basic_state: int | None, status: str | None) -> Posture:
    normalized = (status or "").strip().lower()
    if basic_state == LITE3_STANDING_BASIC_STATE or normalized == "standing":
        return Posture.STANDING
    if normalized in {"sitting", "down", "lying", "damping"}:
        return Posture.SITTING
    if normalized in {
        "standing_up", "standingup", "sitting_down", "transitioning",
        "stand_requested", "down_requested",
    }:
        return Posture.TRANSITIONING
    return Posture.UNKNOWN


def map_lite3_state(
    sample: Lite3TelemetrySample,
    moving_tolerance: float = 0.01,
) -> RobotState:
    values = (sample.forward_mps, sample.lateral_mps, sample.yaw_rps)
    moving = all(math.isfinite(value) for value in values) and any(
        abs(value) > moving_tolerance for value in values)

    if not sample.connected:
        health = Health.OFFLINE
    elif sample.fault:
        health = Health.FAULT
    elif not sample.telemetry_fresh or not sample.high_level_ready:
        health = Health.DEGRADED
    else:
        health = Health.READY

    battery = sample.battery_percent
    if battery is not None and (not math.isfinite(battery) or not 0.0 <= battery <= 100.0):
        battery = None

    return RobotState(
        connected=sample.connected,
        posture=map_posture(sample.basic_state, sample.posture_status),
        moving=moving,
        telemetry_fresh=sample.telemetry_fresh,
        battery_percent=battery,
        fault=sample.fault,
        high_level_ready=sample.high_level_ready,
        health=health,
    )
