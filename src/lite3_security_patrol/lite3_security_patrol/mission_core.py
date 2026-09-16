"""Pure, mock-testable patrol/mission decisions. No ROS or locomotion calls."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class MissionState(str, Enum):
    IDLE = 'IDLE'
    PATROL = 'PATROL'
    NAVIGATING = 'NAVIGATING'
    OBSERVING = 'OBSERVING'
    CAPTURING = 'CAPTURING'
    WAITING = 'WAITING'
    RECOVERY = 'RECOVERY'
    RETURNING = 'RETURNING'
    STOPPED = 'STOPPED'
    ERROR = 'ERROR'


@dataclass(frozen=True)
class Waypoint:
    name: str
    x: float
    y: float
    yaw: float


@dataclass(frozen=True)
class PersonDetected:
    timestamp: float
    confidence: float
    image_reference: Optional[str] = None
    depth_m: Optional[float] = None
    robot_pose: Optional[tuple] = None
    bounding_box_xyxy: Optional[tuple] = None
    source_frame: Optional[str] = None
    pose_is_fresh: bool = False


@dataclass(frozen=True)
class SecurityEvent:
    event_id: str
    timestamp: float
    event_type: str
    confidence: float
    image_reference: Optional[str]
    robot_pose: Optional[tuple]
    robot_status: str


@dataclass
class PatrolManager:
    waypoints: List[Waypoint] = field(default_factory=list)
    repeat: bool = False
    index: int = 0
    paused: bool = False
    active: bool = False

    def start(self) -> None:
        if not self.waypoints:
            raise ValueError('cannot start patrol without waypoints')
        self.active, self.paused, self.index = True, False, 0

    def pause(self) -> None:
        if self.active:
            self.paused = True

    def resume(self) -> None:
        if self.active:
            self.paused = False

    def stop(self) -> None:
        self.active, self.paused = False, False

    def current_waypoint(self) -> Optional[Waypoint]:
        if not self.active or self.paused or not self.waypoints:
            return None
        return self.waypoints[self.index]

    def goal_succeeded(self) -> bool:
        if not self.active:
            return False
        self.index += 1
        if self.index < len(self.waypoints):
            return True
        if self.repeat:
            self.index = 0
            return True
        self.stop()
        return False


class MissionManager:
    """Owns decisions only; callers execute navigation/capture/alerts externally."""
    def __init__(self) -> None:
        self.state = MissionState.IDLE
        self.events: List[SecurityEvent] = []
        self._sequence = 0

    def start_patrol(self) -> None:
        self.state = MissionState.PATROL

    def navigation_started(self) -> None:
        if self.state == MissionState.PATROL:
            self.state = MissionState.NAVIGATING

    def person_detected(self, detection: PersonDetected, robot_status: str) -> SecurityEvent:
        self._sequence += 1
        self.state = MissionState.OBSERVING
        event = SecurityEvent(
            event_id=f'person-{self._sequence:06d}', timestamp=detection.timestamp,
            event_type='PERSON_DETECTED', confidence=detection.confidence,
            image_reference=detection.image_reference, robot_pose=detection.robot_pose,
            robot_status=robot_status)
        self.events.append(event)
        return event

    def capture_complete(self) -> None:
        if self.state == MissionState.OBSERVING:
            self.state = MissionState.WAITING

    def stop(self) -> None:
        self.state = MissionState.STOPPED

    def failure(self) -> None:
        self.state = MissionState.RECOVERY
