"""Read-only ROS readiness observation for the independent autonomy backend."""
from collections import deque
import importlib.util
import math
from pathlib import Path
import time
from .autonomy import Readiness, SavedGoals
from .site_map import map_grid_matches


def sample_guard_files(tracker, directory, now=None, wall=None):
    """Each atomic SCORE rewrite is a guard measurement, even at equal score.

    The existing guard intentionally suppresses identical ROS status messages.
    Never count polling/callback arrival as a new measurement.
    """
    now = time.monotonic() if now is None else now
    wall = time.time() if wall is None else wall
    try:
        paths = [Path(directory) / name for name in
                 ("LOCALIZATION_STATE", "LOCALIZATION_SCORE", "LOCALIZATION_STARTUP_STATE")]
        revisions = [p.stat().st_mtime_ns for p in paths]
        stamps = [r / 1e9 for r in revisions]
        state, score, startup = [p.read_text().strip() for p in paths]
        fresh = all(0 <= wall - stamp <= 2.5 for stamp in stamps)
        policy = startup == "NAVIGATION_READY" and not (Path(directory) / "NAV_TEST_OVERRIDE.json").exists()
        tracker.update("normal_policy", fresh and policy, now)
        if not fresh or not policy:
            tracker.samples.clear()
            return
        fraction = float(score)
        if state != "LOCALIZED" or not math.isfinite(fraction) or not 0.8 <= fraction <= 1:
            tracker.samples.clear()
            return
        if revisions[1] == tracker.last_guard_revision:
            return
        tracker.last_guard_revision = revisions[1]
        # Convert producer measurement time into this process's monotonic clock.
        tracker.localization(fraction, state, now - (wall - stamps[1]))
    except (OSError, ValueError):
        tracker.samples.clear()
        tracker.update("normal_policy", False, now)


class ReadinessTracker:
    required = {"scan": 1.0, "odom": 1.0, "battery": 2.0, "tf": 1.0,
                "local_costmap": 3.0, "global_costmap": 3.0,
                "robot": 2.0, "map_identity": 3.0,
                "map_server": 3.0, "amcl": 3.0, "planner_server": 3.0,
                "controller_server": 3.0, "bt_navigator": 3.0,
                "mission_clear": 3.0, "safety_monitor": 2.0, "normal_policy": 2.5}

    def __init__(self, map_identity):
        self.map_identity = map_identity
        self.active_map_identity = None
        self.observations = {}
        self.samples = deque(maxlen=3)
        self.last_localization_stamp = None
        self.last_guard_revision = None
        self.pose = None

    def update(self, name, valid, stamp):
        self.observations[name] = (valid is True, stamp)

    def localization(self, fraction, state, stamp):
        if self.last_localization_stamp is not None and stamp <= self.last_localization_stamp:
            return
        self.last_localization_stamp = stamp
        if state != "LOCALIZED" or not math.isfinite(fraction) or not 0.8 <= fraction <= 1:
            self.samples.clear()
            return
        self.samples.append((fraction, stamp))

    def ready(self, source, now=None, expected_source="NONE"):
        now = time.monotonic() if now is None else now
        for name, limit in self.required.items():
            valid, stamp = self.observations.get(name, (False, float("-inf")))
            if not valid or not 0 <= now - stamp <= limit:
                raise ValueError(f"{name} unavailable or stale")
        if not self.map_identity or self.active_map_identity != self.map_identity:
            raise ValueError("active map identity mismatch")
        if len(self.samples) != 3 or any(not 0 <= now - t <= 2.5 for _, t in self.samples):
            raise ValueError("localization requires fresh >=80% x3")
        if source != expected_source:
            raise ValueError("command source conflict")
        return Readiness(self.map_identity, tuple(v for v, _ in self.samples),
                         True, source, now)


class RosObservation:
    """Subscriptions/lifecycle queries only; no motion/ownership interfaces."""
    def __init__(self, node, goals, registry, authority):
        from lifecycle_msgs.srv import GetState
        from rcl_interfaces.srv import GetParameters
        from nav_msgs.msg import Odometry, OccupancyGrid
        from sensor_msgs.msg import LaserScan
        from std_msgs.msg import Float32
        from action_msgs.msg import GoalStatusArray
        from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
        from tf2_ros import Buffer, TransformListener
        self.node, self.authority, self.registry = node, authority, registry
        identities = {g.map_identity for g in goals.goals.values()}
        if len(identities) != 1:
            raise ValueError("exactly one site map identity required")
        self.tracker = ReadinessTracker(identities.pop())
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, node)
        self.pending = {}
        self.last_query = float("-inf")
        self.last_robot_query = float("-inf")
        self.clients = {name: node.create_client(GetState, f"/{name}/get_state")
                        for name in ("map_server", "amcl", "planner_server",
                                     "controller_server", "bt_navigator")}
        self.map_client = node.create_client(GetParameters, "/map_server/get_parameters")
        self.GetState, self.GetParameters = GetState, GetParameters
        script = Path(__file__).resolve().parents[2] / "onboard_ros2_ws/src/sensor_visualization/scripts/lite3_posture_guard.py"
        spec = importlib.util.spec_from_file_location("independent_posture_observer", script)
        self.guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.guard)
        self.last_robot_status = {}
        self.goal_status = None
        self.goal_status_received = float("-inf")
        self.static_map = None
        self.active_map_path = None
        self.map_validation_key = None
        self.map_validation_result = False
        self.transport = None
        node.create_subscription(LaserScan, "/scan", lambda msg: self.sensor("scan", msg), qos_profile_sensor_data)
        node.create_subscription(Odometry, "/odom", lambda msg: self.sensor("odom", msg), qos_profile_sensor_data)
        node.create_subscription(Float32, "/lite3/battery_percent", self.battery, qos_profile_sensor_data)
        # Guard atomic measurement files are authoritative; deduplicated ROS
        # status messages are not a measurement stream.
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.status_type, self.status_qos = GoalStatusArray, qos
        self.status_subscription = node.create_subscription(GoalStatusArray, "/navigate_to_pose/_action/status",
                                                            self.mission_status, qos)
        node.create_subscription(OccupancyGrid, "/map", self.on_map, qos)
        for name in ("local_costmap", "global_costmap"):
            node.create_subscription(OccupancyGrid, f"/{name}/costmap",
                                     lambda msg, n=name: self.sensor(n, msg), qos)

    def mission_status(self, msg):
        self.goal_status = msg.status_list
        self.goal_status_received = time.monotonic()

    def on_map(self, msg):
        self.static_map = msg

    def sensor(self, name, msg):
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        age = self.node.get_clock().now().nanoseconds / 1e9 - stamp
        self.tracker.update(name, math.isfinite(age) and 0 <= age <= self.tracker.required[name], time.monotonic() - age)

    def battery(self, msg):
        self.tracker.update("battery", math.isfinite(msg.data) and 25 <= msg.data <= 100, time.monotonic())

    def refresh(self):
        from rclpy.time import Time
        now = time.monotonic()
        sample_guard_files(self.tracker, self.authority.state_dir, now)
        own = self.transport.handle if self.transport is not None else None
        own_id = bytes(own.goal_id.uuid) if own is not None else None
        mission_clear = self.goal_status is not None and all(
            status.status not in (1, 2, 3) or bytes(status.goal_info.goal_id.uuid) == own_id
            for status in self.goal_status)
        self.tracker.update("mission_clear", mission_clear, self.goal_status_received)
        if now - self.last_query >= 1:
            self.last_query = now
            # Refresh the live publisher's latched status snapshot; do not make
            # a stale local cache fresh by repeatedly reading it.
            self.node.destroy_subscription(self.status_subscription)
            self.status_subscription = self.node.create_subscription(
                self.status_type, "/navigate_to_pose/_action/status", self.mission_status, self.status_qos)
            for name, client in self.clients.items():
                if name not in self.pending and client.service_is_ready():
                    self.pending[name] = (client.call_async(self.GetState.Request()), now)
            if "map_identity" not in self.pending and self.map_client.service_is_ready():
                request = self.GetParameters.Request()
                request.names = ["yaml_filename"]
                self.pending["map_identity"] = (self.map_client.call_async(request), now)
        for name, (future, started) in list(self.pending.items()):
            if future.done():
                valid = False
                try:
                    result = future.result()
                    if name == "map_identity":
                        goals = SavedGoals.for_site(self.registry, Path(result.values[0].string_value))
                        self.active_map_path = Path(result.values[0].string_value)
                        identities = {g.map_identity for g in goals.goals.values()}
                        self.tracker.active_map_identity = next(iter(identities)) if len(identities) == 1 else None
                        key = (self.tracker.active_map_identity, id(self.static_map))
                        if key != self.map_validation_key:
                            self.map_validation_result = (self.static_map is not None
                                and map_grid_matches(self.active_map_path, self.static_map))
                            self.map_validation_key = key
                        valid = (self.tracker.active_map_identity == self.tracker.map_identity
                                 and self.map_validation_result)
                    else:
                        valid = result.current_state.id == 3
                except (OSError, ValueError, KeyError, IndexError, AttributeError):
                    valid = False
                self.tracker.update(name, valid and now - started <= 2, now)
                del self.pending[name]
            elif now - started > 2:
                future.cancel()
                self.tracker.update(name, False, now)
                del self.pending[name]
        try:
            transforms = [self.buffer.lookup_transform(a, b, Time()) for a, b in
                          (("map", "odom"), ("odom", "base_link"), ("base_link", "lidar_link"))]
            ros_now = self.node.get_clock().now().nanoseconds / 1e9
            # AMCL deliberately future-dates map->odom by transform_tolerance.
            valid = all(-1.0 <= ros_now - (t.header.stamp.sec + t.header.stamp.nanosec / 1e9) <= 1
                        for t in transforms[:2])
            pose = self.buffer.lookup_transform("map", "base_link", Time())
            self.tracker.pose = {"frame_id": "map", "x": pose.transform.translation.x,
                                 "y": pose.transform.translation.y,
                                 "orientation": {k: getattr(pose.transform.rotation, k) for k in ("x", "y", "z", "w")}}
        except Exception:
            valid = False
            self.tracker.pose = None
        self.tracker.update("tf", valid, now)
        if now - self.last_robot_query >= 0.5:
            self.last_robot_query = now
            try:
                self.last_robot_status = self.guard.snapshot()
                valid = all(self.last_robot_status.get(k) is True for k in
                            ("connected", "high_level_healthy", "telemetry_fresh"))
                valid = valid and self.last_robot_status.get("posture") == "standing"
                monitor = self.guard.run(["systemctl", "is-active", "--quiet",
                                          "lite3-nav2-safety-monitor.service"])
                nodes = self.node.get_node_names()
                self.tracker.update("safety_monitor", monitor.returncode == 0
                                    and nodes.count("lite3_nav2_safety_monitor") == 1, now)
            except Exception:
                self.last_robot_status, valid = {}, False
            self.tracker.update("robot", valid, now)

    def readiness(self, expected_source="NONE"):
        self.refresh()
        return self.tracker.ready(self.authority.source(), expected_source=expected_source)
