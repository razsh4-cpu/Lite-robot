"""Pure conversion and watchdog logic for a future Lite3 /cmd_vel bridge.

This module deliberately has no MotionSDK, socket, or robot dependency.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VelocityCommand:
    forward: float = 0.0
    lateral: float = 0.0
    yaw: float = 0.0


@dataclass(frozen=True)
class VelocityMappingConfig:
    # A non-positive physical maximum is an explicit uncalibrated/safe state.
    max_forward_mps: float = 0.0
    max_lateral_mps: float = 0.0
    max_yaw_radps: float = 0.0
    normalized_limit: float = 1.0
    command_timeout_sec: float = 0.3


def _clamp(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


class VelocityMapper:
    """Maps physical Twist components to the RL policy's normalized command space."""

    def __init__(self, config: VelocityMappingConfig):
        if config.normalized_limit <= 0.0 or config.normalized_limit > 1.0:
            raise ValueError('normalized_limit must be in (0, 1]')
        if config.command_timeout_sec <= 0.0:
            raise ValueError('command_timeout_sec must be positive')
        self.config = config

    def map_physical(self, linear_x: float, linear_y: float, angular_z: float) -> VelocityCommand:
        def scale(value: float, maximum: float) -> float:
            # Calibration is deliberately fail-safe: no measured max means zero.
            if maximum <= 0.0:
                return 0.0
            return _clamp(value / maximum, self.config.normalized_limit)

        return VelocityCommand(
            forward=scale(linear_x, self.config.max_forward_mps),
            lateral=scale(linear_y, self.config.max_lateral_mps),
            yaw=scale(angular_z, self.config.max_yaw_radps),
        )


class CommandWatchdog:
    """Returns zero after the caller has stopped providing fresh commands."""

    def __init__(self, timeout_sec: float):
        if timeout_sec <= 0.0:
            raise ValueError('timeout_sec must be positive')
        self.timeout_sec = timeout_sec
        self._last_command: Optional[VelocityCommand] = None
        self._last_time: Optional[float] = None

    def update(self, command: VelocityCommand, now: float) -> None:
        self._last_command = command
        self._last_time = now

    def current(self, now: float) -> VelocityCommand:
        if self._last_command is None or self._last_time is None:
            return VelocityCommand()
        if now - self._last_time > self.timeout_sec:
            return VelocityCommand()
        return self._last_command
