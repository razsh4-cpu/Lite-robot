"""Generic Bipolix robot contracts with no hardware-vendor dependency."""

from .config import RobotPlatformConfig, load_robot_platform_config
from .contracts import (
    Capability,
    Health,
    MotionLimits,
    Posture,
    PostureRequest,
    RobotCapabilities,
    RobotIdentity,
    RobotInterface,
    RobotState,
    RobotTopics,
    VelocityCommand,
    validate_velocity,
)

__all__ = [
    "Capability",
    "Health",
    "MotionLimits",
    "Posture",
    "PostureRequest",
    "RobotCapabilities",
    "RobotIdentity",
    "RobotInterface",
    "RobotPlatformConfig",
    "RobotState",
    "RobotTopics",
    "VelocityCommand",
    "load_robot_platform_config",
    "validate_velocity",
]
