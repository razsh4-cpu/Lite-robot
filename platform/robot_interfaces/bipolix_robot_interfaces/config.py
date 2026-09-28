"""Load the four-file, vendor-neutral robot platform configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .contracts import (
    Capability,
    MotionLimits,
    RobotCapabilities,
    RobotIdentity,
    RobotTopics,
)


@dataclass(frozen=True)
class RobotPlatformConfig:
    identity: RobotIdentity
    capabilities: RobotCapabilities
    motion_limits: MotionLimits
    topics: RobotTopics
    length_m: float
    width_m: float
    motion: Mapping[str, Any]
    safety: Mapping[str, Any]
    sensors: Mapping[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing robot configuration: {path.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a YAML mapping")
    return payload


def _mapping(parent: Mapping[str, Any], key: str, source: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{source}: {key} must be a mapping")
    return value


def _positive(parent: Mapping[str, Any], key: str, source: str) -> float:
    try:
        value = float(parent[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{source}: {key} must be numeric") from exc
    if value <= 0.0:
        raise ValueError(f"{source}: {key} must be positive")
    return value


def load_robot_platform_config(directory: str | Path) -> RobotPlatformConfig:
    root = Path(directory)
    robot = _read_yaml(root / "robot.yaml")
    motion = _read_yaml(root / "motion.yaml")
    safety = _read_yaml(root / "safety.yaml")
    sensors = _read_yaml(root / "sensors.yaml")

    identity_data = _mapping(robot, "identity", "robot.yaml")
    identity_values = {}
    for key in ("robot_id", "manufacturer", "model", "adapter"):
        value = identity_data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"robot.yaml: identity.{key} is required")
        identity_values[key] = value.strip()
    identity = RobotIdentity(**identity_values)

    raw_capabilities = robot.get("capabilities")
    if not isinstance(raw_capabilities, list) or not raw_capabilities:
        raise ValueError("robot.yaml: capabilities must be a non-empty list")
    try:
        capabilities = RobotCapabilities(
            frozenset(Capability(str(value)) for value in raw_capabilities))
    except ValueError as exc:
        raise ValueError(f"robot.yaml: unknown capability: {exc}") from exc

    dimensions = _mapping(robot, "dimensions", "robot.yaml")
    limits = _mapping(motion, "limits", "motion.yaml")
    motion_limits = MotionLimits(
        max_forward_mps=_positive(limits, "forward_mps", "motion.yaml"),
        max_backward_mps=_positive(limits, "backward_mps", "motion.yaml"),
        max_lateral_mps=_positive(limits, "lateral_mps", "motion.yaml"),
        max_yaw_rps=_positive(limits, "yaw_rps", "motion.yaml"),
    )

    if float(safety.get("command_watchdog_s", 0.0)) <= 0.0:
        raise ValueError("safety.yaml: command_watchdog_s must be positive")
    for key in ("odometry", "laser_scan", "battery", "telemetry"):
        if key not in sensors:
            raise ValueError(f"sensors.yaml: {key} is required")
    odometry = _mapping(sensors, "odometry", "sensors.yaml")
    odometry_topic = odometry.get("topic")
    if not isinstance(odometry_topic, str):
        raise ValueError("sensors.yaml: odometry.topic is required")

    return RobotPlatformConfig(
        identity=identity,
        capabilities=capabilities,
        motion_limits=motion_limits,
        topics=RobotTopics(odometry=odometry_topic),
        length_m=_positive(dimensions, "length_m", "robot.yaml"),
        width_m=_positive(dimensions, "width_m", "robot.yaml"),
        motion=motion,
        safety=safety,
        sensors=sensors,
    )
