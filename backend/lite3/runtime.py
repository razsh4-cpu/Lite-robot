"""Standalone mission runtime composition; no SABLE/NOMAD dependencies."""
from .autonomy import AutonomyBackend, SavedGoals
from .live_navigation import LiveNavigationPort, RosNav2Transport
from .autonomy_service import SystemdAutonomy
from .observation import RosObservation


class IndependentRuntime:
    def __init__(self, goals, navigation, observation, pump, alert_routes=None):
        self.navigation, self.observation, self.pump = navigation, observation, pump
        self.backend = AutonomyBackend(goals, navigation, alert_routes)
        self.blocker = None
        self.pending_result = None

    def _ready(self):
        source = "AUTONOMY" if self.backend.request_id else "NONE"
        return self.observation.readiness(expected_source=source)

    def verify(self):
        self.pump()
        try:
            ready = self._ready()
            self.backend.last_readiness = ready
            self.blocker = None
            return True
        except (ValueError, OSError) as exc:
            self.blocker = str(exc)
            return False

    def goto(self, saved_goal):
        self.backend.goto(saved_goal, self.observation.readiness())

    def start_patrol(self, patrol_id, route):
        self.backend.start_patrol(patrol_id, route, self.observation.readiness())

    def pause_patrol(self):
        return self.backend.pause_patrol()

    def resume_patrol(self):
        self.backend.resume_patrol(self.observation.readiness())

    def cancel_patrol(self):
        self.pending_result = None
        return self.backend.cancel_patrol()

    def stop_patrol(self):
        return self.cancel_patrol()

    def cancel_navigation(self):
        self.pending_result = None
        return self.backend.cancel_navigation()

    def handle_alert(self, alert):
        self.backend.handle_alert(alert, self._ready)

    def step(self):
        """Call continuously while active; exceptions require explicit cleanup."""
        self.pump()
        if not self.backend.request_id:
            return
        try:
            if self.pending_result is not None:
                if self.backend.navigation_result(*self.pending_result, self._ready):
                    self.pending_result = None
                return
            ready = self._ready()
            self.backend.check_readiness(ready)
            result = self.navigation.poll()
            if result is not None:
                if not self.backend.navigation_result(*result, self._ready):
                    self.pending_result = result
        except Exception as exc:
            self.pending_result = None
            self.blocker = str(exc)
            self.backend.faults.append(str(exc))
            if self.backend._stop("FAILED"):
                if self.backend.patrol_state == "RUNNING":
                    self.backend.patrol_state = "FAILED"
                if self.backend.alert_state == "NAVIGATING":
                    self.backend.alert_state = "FAILED"

    def status(self):
        from dataclasses import asdict
        status = self.backend.status()
        samples = self.observation.tracker.samples if hasattr(self.observation.tracker, "samples") else ()
        source = self.navigation.authority.source
        source = source() if callable(source) else source
        status.update({"pose": self.observation.tracker.pose,
                       "command_source": source,
                       "localization_confidence": samples[-1][0] if samples else None,
                       "localization_state": "LOCALIZED" if self.verify() else "UNAVAILABLE",
                       "blocker": self.blocker,
                       "navigation_transport": self.navigation.status()})
        status["readiness"] = asdict(self.backend.last_readiness) if self.backend.last_readiness else None
        return status


def create_ros_runtime(node, registry, map_yaml, alert_routes=None, motion_approved=False):
    """Does not acquire ownership/start services/send goals during construction."""
    import rclpy
    goals = SavedGoals.for_site(registry, map_yaml)
    authority = SystemdAutonomy(motion_approved=motion_approved)
    transport = RosNav2Transport(node)
    observation = RosObservation(node, goals, registry, authority)
    port = LiveNavigationPort(transport, authority)
    observation.transport = port
    return IndependentRuntime(goals, port, observation,
                              lambda: rclpy.spin_once(node, timeout_sec=0.05), alert_routes)
