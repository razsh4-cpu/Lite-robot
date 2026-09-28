"""Pure Day-3 mission model; intentionally contains no execution path.

Mission code decides *what* outcome is requested. A future runtime may resolve
these targets into a Nav2 goal, but it must never publish velocity, acquire a
hardware transport, or bypass AUTONOMY/arbitration.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
import math
import re

class MissionState(str, Enum):
    IDLE = "IDLE"
    VALIDATING = "VALIDATING"
    NAVIGATING = "NAVIGATING"
    ARRIVED = "ARRIVED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

_LOCATION_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")

@dataclass(frozen=True)
class SavedLocationTarget:
    name: str
    def __post_init__(self) -> None:
        if not _LOCATION_NAME.fullmatch(self.name):
            raise ValueError("invalid saved-location name")

@dataclass(frozen=True)
class AdHocTarget:
    x: float
    y: float
    yaw: float
    frame_id: str = "map"
    def __post_init__(self) -> None:
        if self.frame_id != "map":
            raise ValueError("Day-3 navigation targets must use frame_id=map")
        if not all(math.isfinite(value) for value in (self.x, self.y, self.yaw)):
            raise ValueError("target pose must contain finite values")

MissionTarget = SavedLocationTarget | AdHocTarget
_ALLOWED_TRANSITIONS = {
    MissionState.IDLE: {MissionState.VALIDATING},
    MissionState.VALIDATING: {MissionState.NAVIGATING, MissionState.FAILED, MissionState.CANCELLED},
    MissionState.NAVIGATING: {MissionState.ARRIVED, MissionState.FAILED, MissionState.CANCELLED},
    MissionState.ARRIVED: set(),
    MissionState.FAILED: set(),
    MissionState.CANCELLED: set(),
}

@dataclass(frozen=True)
class Mission:
    """One immutable mission lifecycle record, not a Nav2 client."""
    mission_id: str
    robot_id: str
    target: MissionTarget
    state: MissionState = MissionState.IDLE
    detail: str | None = None
    def __post_init__(self) -> None:
        if not self.mission_id.strip():
            raise ValueError("mission_id is required")
        if not self.robot_id.strip():
            raise ValueError("robot_id is required")
    def transition(self, state: MissionState, detail: str | None = None) -> "Mission":
        if state not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid mission transition: {self.state.value}->{state.value}")
        return replace(self, state=state, detail=detail)
