"""Offline-prepared mission orchestration over the existing navigation boundary.

No concrete physical transport is provided here. A future navigation port must
use the existing Nav2/AUTONOMY path and confirm cancellation, zero and release.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import importlib.util
import hashlib
import math
from pathlib import Path
import time
from typing import Protocol
from uuid import uuid4

from bipolix_missions import AdHocTarget, SavedLocationTarget


@dataclass(frozen=True)
class SavedGoal:
    goal_id: str
    name: str
    map_identity: str
    pose: AdHocTarget | None
    enabled: bool
    tags: tuple[str, ...] = ()
    version: str = "legacy-registry/v1"


class SavedGoals:
    """Adapt the existing registry; do not maintain another coordinate store."""
    def __init__(self, goals):
        self.goals = dict(goals)

    @classmethod
    def for_site(cls, registry: Path, map_yaml: Path):
        """Bind an external site registry to exact map metadata/image contents."""
        import yaml
        metadata_bytes = Path(map_yaml).read_bytes()
        metadata = yaml.safe_load(metadata_bytes)
        image = Path(metadata["image"])
        if not image.is_absolute():
            image = Path(map_yaml).parent / image
        digest = hashlib.sha256(metadata_bytes + b"\0" + image.read_bytes()).hexdigest()
        return cls.load(registry, "sha256:" + digest)

    @classmethod
    def load(cls, path: Path, map_identity: str):
        if not map_identity or map_identity == "UNKNOWN":
            raise ValueError("verified map identity required")
        legacy = (Path(__file__).resolve().parents[2] / "onboard_ros2_ws/src/"
                  "sensor_visualization/scripts/lite3_mission_manager.py")
        spec = importlib.util.spec_from_file_location("lite3_named_registry", legacy)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data = module.load_registry(Path(path))
        if not data.get("map"):
            raise ValueError("registry map name required")
        goals = {}
        for goal_id, item in data["locations"].items():
            SavedLocationTarget(goal_id)
            enabled = item.get("configured") is True and item.get("enabled", True) is True
            pose = AdHocTarget(float(item["x"]), float(item["y"]), float(item["yaw"])) if enabled else None
            goals[goal_id] = SavedGoal(goal_id, item.get("name", goal_id), map_identity,
                                       pose, enabled, tuple(item.get("tags", ())))
        return cls(goals)

    def resolve(self, goal_id, map_identity):
        goal = self.goals.get(goal_id)
        if goal is None or not goal.enabled or goal.pose is None:
            raise ValueError("unknown or disabled saved goal")
        if not map_identity or goal.map_identity != map_identity:
            raise ValueError("incompatible or unknown map")
        return goal


def navigation_goal(goal: SavedGoal) -> dict:
    """Standard map pose for the future Nav2 port, without ROS imports."""
    p = goal.pose
    if p is None:
        raise ValueError("goal has no validated pose")
    return {"frame_id": p.frame_id,
            "position": {"x": p.x, "y": p.y, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0,
                            "z": math.sin(p.yaw / 2), "w": math.cos(p.yaw / 2)}}


@dataclass(frozen=True)
class Readiness:
    map_identity: str
    localization_samples: tuple[float, ...]
    prerequisites_verified: bool
    command_source: str
    observed_monotonic: float = field(default_factory=time.monotonic)

    def validate(self, expected_source="NONE"):
        age = time.monotonic() - self.observed_monotonic
        if not math.isfinite(age) or not 0 <= age <= 2.5:
            raise ValueError("readiness stale or invalid")
        if self.prerequisites_verified is not True or not self.map_identity or self.map_identity == "UNKNOWN":
            raise ValueError("navigation prerequisites unverified")
        if self.command_source != expected_source:
            raise ValueError("command source conflict")
        samples = self.localization_samples[-3:]
        if len(samples) != 3 or not all(math.isfinite(s) and 0.80 <= s <= 1 for s in samples):
            raise ValueError("localization requires >=80% x3")


@dataclass(frozen=True)
class StopConfirmation:
    navigation_cancelled: bool
    velocity_zero: bool
    ownership_released: bool
    command_source: str

    @property
    def safe(self):
        return (self.navigation_cancelled is True and self.velocity_zero is True
                and self.ownership_released is True and self.command_source == "NONE")


class NavigationPort(Protocol):
    def start(self, request_id: str, goal: dict) -> None: ...
    def stop(self, request_id: str) -> StopConfirmation: ...


class RecordingNavigation:
    """Explicit offline fixture: records requests and simulated stop results."""
    def __init__(self):
        self.requests = []
        self.stop_calls = 0
        self.start_error = None
        self.stop_confirmation = StopConfirmation(True, True, True, "NONE")

    def start(self, request_id, goal):
        self.requests.append((request_id, goal))
        if self.start_error:
            raise self.start_error

    def stop(self, request_id):
        self.stop_calls += 1
        return self.stop_confirmation


class AutonomyBackend:
    def __init__(self, goals: SavedGoals, navigation: NavigationPort, alert_routes=None):
        self.goals, self.navigation = goals, navigation
        self.alert_routes = dict(alert_routes or {})
        self.navigation_state = "IDLE"
        self.patrol_state = "IDLE"
        self.alert_state = "IDLE"
        self.current_goal = None
        self.request_id = None
        self.command_source = "UNKNOWN"
        self.patrol_id = None
        self.route = ()
        self.waypoint = 0
        self.faults = []
        self.last_readiness = None
        self.mode = None

    def _idle(self):
        if self.request_id or self.navigation_state == "STOPPING":
            raise ValueError("navigation active or stop unconfirmed")

    def _dispatch(self, goal, ready, mode):
        self._idle()
        ready.validate()
        self.last_readiness = ready
        self.command_source = ready.command_source
        self.current_goal, self.mode = goal.goal_id, mode
        self.request_id = str(uuid4())
        self.navigation_state = "NAVIGATING"
        try:
            self.navigation.start(self.request_id, navigation_goal(goal))
        except Exception as exc:
            self.faults.append(str(exc))
            self._stop("FAILED")
            if mode == "PATROL":
                self.patrol_state = "FAILED"
            if mode == "ALERT":
                self.alert_state = "FAILED"
            raise

    def goto(self, goal_id, ready):
        if self.patrol_state in ("RUNNING", "PAUSED"):
            raise ValueError("cancel patrol or use explicit alert routing first")
        self._dispatch(self.goals.resolve(goal_id, ready.map_identity), ready, "GOTO")

    def _stop(self, final_state):
        if not self.request_id:
            return self.navigation_state != "STOPPING"
        try:
            confirmation = self.navigation.stop(self.request_id)
        except Exception as exc:
            self.faults.append(str(exc))
            self.navigation_state = "STOPPING"
            self.command_source = "UNKNOWN"
            return False
        self.command_source = confirmation.command_source
        if not confirmation.safe:
            self.navigation_state = "STOPPING"
            self.faults.append("cancel/zero/release unconfirmed")
            return False
        self.request_id = None
        self.navigation_state = final_state
        return True

    def cancel_navigation(self):
        safe = self._stop("CANCELLED")
        if self.patrol_state in ("RUNNING", "PAUSED", "STOPPING"):
            self.patrol_state = "CANCELLED" if safe else "STOPPING"
        if self.alert_state in ("NAVIGATING", "STOPPING"):
            self.alert_state = "CANCELLED" if safe else "STOPPING"
        return safe

    def start_patrol(self, patrol_id, route, ready):
        self._idle()
        if self.patrol_state in ("RUNNING", "PAUSED") or not patrol_id or not route:
            raise ValueError("invalid or already active patrol")
        ready.validate()
        route = tuple(route)
        for name in route:
            self.goals.resolve(name, ready.map_identity)
        self.patrol_id, self.route, self.waypoint = patrol_id, route, 0
        self.patrol_state = "RUNNING"
        self._dispatch(self.goals.resolve(route[0], ready.map_identity), ready, "PATROL")

    def pause_patrol(self):
        if self.patrol_state == "PAUSED":
            return True
        if self.patrol_state != "RUNNING":
            raise ValueError("no running patrol")
        safe = self._stop("CANCELLED")
        self.patrol_state = "PAUSED" if safe else "STOPPING"
        return safe

    def resume_patrol(self, ready):
        if self.patrol_state != "PAUSED" or self.alert_state == "NAVIGATING":
            raise ValueError("patrol cannot resume")
        goal = self.goals.resolve(self.route[self.waypoint], ready.map_identity)
        ready.validate()
        self._idle()
        self.patrol_state, self.alert_state = "RUNNING", "IDLE"
        self._dispatch(goal, ready, "PATROL")

    def cancel_patrol(self):
        safe = self.cancel_navigation()
        self.patrol_state = "CANCELLED" if safe else "STOPPING"
        return safe

    def stop_patrol(self):
        return self.cancel_patrol()

    def handle_alert(self, alert, ready):
        if alert not in self.alert_routes:
            raise ValueError("unmapped alert")
        goal = self.goals.resolve(self.alert_routes[alert], ready.map_identity)
        # Validate input before interrupting any current patrol. Actual cleanup
        # must confirm NONE before the new navigation request can be dispatched.
        ready.validate("AUTONOMY" if ready.command_source == "AUTONOMY" and self.request_id else "NONE")
        if self.patrol_state == "RUNNING":
            if not self.pause_patrol():
                raise ValueError("patrol stop unconfirmed")
        self._idle()
        from dataclasses import replace
        dispatch_ready = replace(ready, command_source=self.command_source) if self.mode == "PATROL" else ready
        self._dispatch(goal, dispatch_ready, "ALERT")
        self.alert_state = "NAVIGATING"

    def navigation_result(self, request_id, result, ready):
        if request_id != self.request_id or self.request_id is None:
            return False
        mode = self.mode
        successful = result == "SUCCEEDED"
        if not self._stop("ARRIVED" if successful else "FAILED"):
            if mode == "PATROL":
                self.patrol_state = "STOPPING"
            return False
        if mode == "ALERT":
            self.alert_state = "AWAITING_DECISION" if successful else "FAILED"
        if mode == "PATROL":
            if not successful:
                self.patrol_state = "FAILED"
            elif self.waypoint + 1 >= len(self.route):
                self.patrol_state = "COMPLETED"
            else:
                self.waypoint += 1
                try:
                    self._dispatch(self.goals.resolve(self.route[self.waypoint], ready.map_identity), ready, "PATROL")
                except Exception:
                    self.patrol_state = "FAILED"
                    raise
        return True

    def check_readiness(self, ready):
        self.last_readiness = ready
        self.command_source = ready.command_source
        if not self.request_id:
            return
        try:
            ready.validate("AUTONOMY")
            self.goals.resolve(self.current_goal, ready.map_identity)
        except ValueError as exc:
            self.faults.append(str(exc))
            mode = self.mode
            if self._stop("FAILED"):
                if mode == "PATROL":
                    self.patrol_state = "FAILED"
                if mode == "ALERT":
                    self.alert_state = "FAILED"

    def prepare_manual_takeover(self):
        """Return permission to REQUEST manual ownership, never grant it."""
        safe = self.cancel_navigation()
        return safe and self.command_source == "NONE"

    def status(self):
        return {"navigation_state": self.navigation_state, "current_goal": self.current_goal,
                "request_id": self.request_id, "patrol_id": self.patrol_id,
                "patrol_state": self.patrol_state, "route": self.route,
                "current_waypoint": self.waypoint if self.route else None,
                "next_waypoint": self.waypoint + 1 if self.waypoint + 1 < len(self.route) else None,
                "alert_state": self.alert_state, "command_source": self.command_source,
                "faults": tuple(self.faults), "pose": None,
                "readiness": self.last_readiness}
