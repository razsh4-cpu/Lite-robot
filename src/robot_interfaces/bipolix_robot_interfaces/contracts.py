"""Small, vendor-neutral contracts for robot-facing product software.

These types describe intent and normalized state.  An implementation MUST route
requests through the deployed command-source lease, arbiter, watchdogs and
HIGH-LEVEL safety runtime.  Implementing this protocol is not permission to
open a hardware socket or bypass those controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Protocol, runtime_checkable


class Posture(str, Enum):
    SITTING = "SITTING"
    STANDING = "STANDING"
    TRANSITIONING = "TRANSITIONING"
    UNKNOWN = "UNKNOWN"


class PostureRequest(str, Enum):
    STAND = "stand"
    DOWN = "down"


class Health(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAULT = "FAULT"
    OFFLINE = "OFFLINE"


class Capability(str, Enum):
    MOTION_FORWARD = "motion.forward"
    MOTION_BACKWARD = "motion.backward"
    MOTION_LATERAL = "motion.lateral"
    MOTION_YAW = "motion.yaw"
    POSTURE_STAND = "posture.stand"
    POSTURE_DOWN = "posture.down"
    ODOMETRY = "odometry"
    BATTERY = "battery"
    TELEMETRY = "telemetry"


@dataclass(frozen=True)
class RobotIdentity:
    """Identity of one configured instance and its adapter type."""

    robot_id: str
    manufacturer: str
    model: str
    adapter: str


@dataclass(frozen=True)
class MotionLimits:
    max_forward_mps: float
    max_backward_mps: float
    max_lateral_mps: float
    max_yaw_rps: float

    def __post_init__(self) -> None:
        values = (
            self.max_forward_mps,
            self.max_backward_mps,
            self.max_lateral_mps,
            self.max_yaw_rps,
        )
        if not all(math.isfinite(value) and value >= 0.0 for value in values):
            raise ValueError("motion limits must be finite and non-negative")


@dataclass(frozen=True)
class VelocityCommand:
    """ROS-compatible planar velocity intent, independent of transport."""

    linear_x: float = 0.0
    linear_y: float = 0.0
    angular_z: float = 0.0


@dataclass(frozen=True)
class RobotCapabilities:
    supported: frozenset[Capability]

    def has(self, capability: Capability) -> bool:
        return capability in self.supported


@dataclass(frozen=True)
class RobotTopics:
    """Standard robot-facing ROS topics exposed to higher layers."""

    odometry: str = "/odom"

    def __post_init__(self) -> None:
        if not self.odometry.startswith("/"):
            raise ValueError("odometry must be an absolute ROS topic")


@dataclass(frozen=True)
class RobotState:
    connected: bool
    posture: Posture
    moving: bool
    telemetry_fresh: bool
    battery_percent: float | None
    fault: str | None
    high_level_ready: bool
    health: Health


def validate_velocity(
    command: VelocityCommand,
    limits: MotionLimits,
    capabilities: RobotCapabilities,
) -> None:
    """Reject malformed, over-limit or unsupported motion intent.

    This is input validation, not a substitute for runtime safety enforcement.
    """

    values = (command.linear_x, command.linear_y, command.angular_z)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("velocity values must be finite")
    if command.linear_x > limits.max_forward_mps:
        raise ValueError("forward velocity exceeds configured limit")
    if command.linear_x < -limits.max_backward_mps:
        raise ValueError("backward velocity exceeds configured limit")
    if abs(command.linear_y) > limits.max_lateral_mps:
        raise ValueError("lateral velocity exceeds configured limit")
    if abs(command.angular_z) > limits.max_yaw_rps:
        raise ValueError("yaw velocity exceeds configured limit")
    if command.linear_x > 0.0 and not capabilities.has(Capability.MOTION_FORWARD):
        raise ValueError("forward motion is unsupported")
    if command.linear_x < 0.0 and not capabilities.has(Capability.MOTION_BACKWARD):
        raise ValueError("backward motion is unsupported")
    if command.linear_y != 0.0 and not capabilities.has(Capability.MOTION_LATERAL):
        raise ValueError("lateral motion is unsupported")
    if command.angular_z != 0.0 and not capabilities.has(Capability.MOTION_YAW):
        raise ValueError("yaw motion is unsupported")


@runtime_checkable
class RobotInterface(Protocol):
    """Contract implemented by a safety-preserving robot adapter.

    Calls express intent only.  Implementations must use the approved command
    interface and must not bypass ownership, permits, watchdogs or safe-zero.
    """

    @property
    def identity(self) -> RobotIdentity: ...

    @property
    def capabilities(self) -> RobotCapabilities: ...

    @property
    def motion_limits(self) -> MotionLimits: ...

    @property
    def topics(self) -> RobotTopics: ...

    def state(self) -> RobotState: ...

    def request_velocity(self, command: VelocityCommand) -> None: ...

    def request_posture(self, request: PostureRequest) -> None: ...
