"""AMCL initialization and scan-to-map quality gate for Lite3."""

import json
import math
import os
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from std_srvs.srv import Empty
from tf2_ros import Buffer, TransformException, TransformListener


class LocalizationGuard(Node):
    def __init__(self):
        super().__init__("lite3_localization_guard")
        self.declare_parameter("minimum_match_fraction", 0.80)
        self.declare_parameter("wall_tolerance", 0.15)
        self.declare_parameter("scan_stride", 8)
        self.declare_parameter("startup_delay", 4.0)
        # One initial search plus one bounded retry after the requested
        # short manual movement.
        self.declare_parameter("global_retry_limit", 2)
        self.declare_parameter("hypothesis_grace_period", 8.0)
        self.declare_parameter("global_search_timeout", 45.0)
        self.declare_parameter("manual_rearm_distance", 0.15)
        self.declare_parameter("manual_rearm_yaw", math.radians(15.0))
        self.declare_parameter("state_dir", "/run/lite3-control")
        self.declare_parameter("pose_file", "/home/abx/.config/lite3/last_localized_pose.json")

        latched = QoSProfile(depth=1)
        latched.reliability = ReliabilityPolicy.RELIABLE
        latched.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self._map = None
        self._scan = None
        self._pose = None
        self._last_status = None
        self._localized = False
        self._good_cycles = 0
        self._global_attempts = 0
        self._started = self.get_clock().now()
        self._restored_pose = False
        self._hypothesis_started = None
        self._global_started = None
        self._odom_pose = None
        self._global_origin = None

        self.create_subscription(OccupancyGrid, "/map", self._on_map, latched)
        self.create_subscription(LaserScan, "/scan", self._on_scan, qos_profile_sensor_data)
        self.create_subscription(Odometry, "/odom", self._on_odom, qos_profile_sensor_data)
        self.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", self._on_pose, latched)
        self._status_pub = self.create_publisher(String, "/localization/status", latched)
        self._pose_pub = self.create_publisher(PoseStamped, "/localization/pose", latched)
        self._initial_pub = self.create_publisher(PoseWithCovarianceStamped, "/initialpose", 1)
        self._global = self.create_client(Empty, "/reinitialize_global_localization")
        self._nomotion = self.create_client(Empty, "/request_nomotion_update")
        self._tf = Buffer()
        self._tf_listener = TransformListener(self._tf, self)
        self.create_timer(1.0, self._tick)
        self.create_timer(0.1, self._publish_live_pose)
        self._set_status("INITIALIZING", 0.0, "waiting for map, scan and AMCL")

    def _on_map(self, msg):
        self._map = msg

    def _on_scan(self, msg):
        self._scan = msg

    def _on_pose(self, msg):
        self._pose = msg

    def _on_odom(self, msg):
        pose = msg.pose.pose
        yaw = math.atan2(
            2.0 * (pose.orientation.w * pose.orientation.z
                   + pose.orientation.x * pose.orientation.y),
            1.0 - 2.0 * (pose.orientation.y * pose.orientation.y
                         + pose.orientation.z * pose.orientation.z))
        self._odom_pose = (pose.position.x, pose.position.y, yaw)

    @staticmethod
    def _angle_delta(first, second):
        return math.atan2(math.sin(second - first), math.cos(second - first))

    def _manual_motion_detected(self):
        if self._odom_pose is None or self._global_origin is None:
            return False
        x0, y0, yaw0 = self._global_origin
        x1, y1, yaw1 = self._odom_pose
        distance = math.hypot(x1 - x0, y1 - y0)
        yaw_change = abs(self._angle_delta(yaw0, yaw1))
        return (
            distance >= float(
                self.get_parameter("manual_rearm_distance").value)
            or yaw_change >= float(
                self.get_parameter("manual_rearm_yaw").value)
        )

    def _publish_live_pose(self):
        if not self._localized:
            return
        try:
            tr = self._tf.lookup_transform(
                "map", "base_link", rclpy.time.Time(),
                timeout=Duration(seconds=0.1))
        except TransformException:
            return
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "map"
        pose.pose.position.x = tr.transform.translation.x
        pose.pose.position.y = tr.transform.translation.y
        pose.pose.position.z = tr.transform.translation.z
        pose.pose.orientation = tr.transform.rotation
        self._pose_pub.publish(pose)

    def _state_path(self, name):
        return Path(str(self.get_parameter("state_dir").value)) / name

    def _atomic_write(self, path, value):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_name("." + path.name + f".{os.getpid()}")
            temp.write_text(str(value) + "\n", encoding="utf-8")
            temp.replace(path)
        except OSError as exc:
            self.get_logger().warning(f"cannot write {path}: {exc}")

    def _set_status(self, state, score, reason):
        self._localized = state == "LOCALIZED"
        signature = (state, round(score, 3), reason)
        if signature != self._last_status:
            msg = String()
            msg.data = json.dumps({"state": state, "match_fraction": round(score, 3), "reason": reason})
            self._status_pub.publish(msg)
            self.get_logger().info(msg.data)
            self._last_status = signature
        self._atomic_write(self._state_path("LOCALIZATION_STATE"), state)
        self._atomic_write(self._state_path("LOCALIZATION_SCORE"), f"{score:.3f}")
        if state == "LOCALIZED":
            self._atomic_write(
                self._state_path("LOCALIZATION_STARTUP_STATE"),
                "NAVIGATION_READY")
            self._atomic_write(
                self._state_path("LOCALIZATION_STARTUP_ERROR"), "")
        elif state == "UNLOCALIZED" and not reason.startswith("waiting for"):
            self._atomic_write(
                self._state_path("LOCALIZATION_STARTUP_STATE"),
                "UNLOCALIZED")

    def _restore_last_pose(self):
        self._restored_pose = True
        path = Path(str(self.get_parameter("pose_file").value))
        if not path.is_file():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            msg = PoseWithCovarianceStamped()
            # A zero stamp tells AMCL to use the latest odom transform. Using
            # "now" races the high-rate odom publisher and can put the initial
            # pose a few milliseconds in TF's future.
            msg.header.stamp = rclpy.time.Time().to_msg()
            msg.header.frame_id = "map"
            msg.pose.pose.position.x = float(data["x"])
            msg.pose.pose.position.y = float(data["y"])
            yaw = float(data["yaw"])
            msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
            msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
            msg.pose.covariance[0] = 0.09
            msg.pose.covariance[7] = 0.09
            msg.pose.covariance[35] = math.radians(15.0) ** 2
            self._initial_pub.publish(msg)
            self._hypothesis_started = self.get_clock().now()
            self.get_logger().info(f"restored last validated pose from {path}")
            return True
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            self.get_logger().warning(f"ignored invalid saved pose: {exc}")
            return False

    def _request_nomotion(self):
        if not self._nomotion.service_is_ready():
            self._nomotion.wait_for_service(timeout_sec=0.1)
        if self._nomotion.service_is_ready():
            self._nomotion.call_async(Empty.Request())

    def _request_global(self):
        # One global initialization starts the search. Repeating this request
        # every second destroys the particle distribution before AMCL can
        # converge, especially while the robot is stationary.
        retry_limit = max(
            1, int(self.get_parameter("global_retry_limit").value))
        if self._global_attempts >= retry_limit:
            return False
        if not self._global.service_is_ready():
            self._global.wait_for_service(timeout_sec=0.1)
        if not self._global.service_is_ready():
            return False
        self._global.call_async(Empty.Request())
        self._global_attempts += 1
        self._global_started = self.get_clock().now()
        self._global_origin = self._odom_pose
        self.get_logger().warning(
            f"started bounded AMCL global relocalization search "
            f"{self._global_attempts}/{retry_limit}")
        self._request_nomotion()
        return True

    def _score(self):
        if self._map is None or self._scan is None or self._pose is None:
            return None, "waiting for map/scan/pose"
        try:
            tr = self._tf.lookup_transform(
                "base_link", self._scan.header.frame_id, rclpy.time.Time(),
                timeout=Duration(seconds=0.2))
        except TransformException as exc:
            return None, f"missing scan TF: {exc}"

        info = self._map.info
        grid = self._map.data
        width, height = int(info.width), int(info.height)
        resolution = float(info.resolution)
        origin_x, origin_y = info.origin.position.x, info.origin.position.y
        tolerance_cells = max(1, int(math.ceil(float(self.get_parameter("wall_tolerance").value) / resolution)))
        stride = max(1, int(self.get_parameter("scan_stride").value))

        q = tr.transform.rotation
        lidar_yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y*q.y + q.z*q.z))
        p = self._pose.pose.pose
        pose_yaw = math.atan2(2.0 * (p.orientation.w * p.orientation.z + p.orientation.x * p.orientation.y), 1.0 - 2.0 * (p.orientation.y*p.orientation.y + p.orientation.z*p.orientation.z))
        c_l, s_l = math.cos(lidar_yaw), math.sin(lidar_yaw)
        c_p, s_p = math.cos(pose_yaw), math.sin(pose_yaw)
        tx, ty = tr.transform.translation.x, tr.transform.translation.y

        hits = 0
        inside = 0
        usable = 0
        for i in range(0, len(self._scan.ranges), stride):
            r = float(self._scan.ranges[i])
            if not math.isfinite(r) or r <= self._scan.range_min or r >= min(self._scan.range_max, 12.0):
                continue
            angle = self._scan.angle_min + i * self._scan.angle_increment
            lx, ly = r * math.cos(angle), r * math.sin(angle)
            bx, by = tx + c_l*lx - s_l*ly, ty + s_l*lx + c_l*ly
            mx = p.position.x + c_p*bx - s_p*by
            my = p.position.y + s_p*bx + c_p*by
            gx, gy = int((mx-origin_x)/resolution), int((my-origin_y)/resolution)
            usable += 1
            if not (0 <= gx < width and 0 <= gy < height):
                continue
            inside += 1
            found = False
            for yy in range(max(0, gy-tolerance_cells), min(height, gy+tolerance_cells+1)):
                row = yy * width
                for xx in range(max(0, gx-tolerance_cells), min(width, gx+tolerance_cells+1)):
                    if grid[row+xx] >= 65:
                        found = True
                        break
                if found:
                    break
            hits += int(found)
        if usable < 50:
            return None, f"too few usable scan points ({usable})"
        return hits / usable, f"wall_hits={hits}/{usable}, inside={inside}/{usable}"

    def _tick(self):
        age = (self.get_clock().now() - self._started).nanoseconds / 1e9
        if age < float(self.get_parameter("startup_delay").value):
            return
        if not self._restored_pose:
            restored = self._restore_last_pose()
            if restored:
                return
            self._hypothesis_started = self.get_clock().now()
        score, reason = self._score()
        threshold = float(self.get_parameter("minimum_match_fraction").value)
        if score is not None and score >= threshold:
            self._good_cycles += 1
            state = "LOCALIZED" if self._good_cycles >= 3 else "VERIFYING"
            self._set_status(state, score, reason)
            return
        self._good_cycles = 0
        now = self.get_clock().now()
        self._set_status("UNLOCALIZED", score or 0.0, reason)
        grace = float(self.get_parameter("hypothesis_grace_period").value)
        hypothesis_age = ((now - self._hypothesis_started).nanoseconds / 1e9
                          if self._hypothesis_started is not None else grace)
        if self._global_attempts == 0 and hypothesis_age < grace:
            self._request_nomotion()
            return
        if self._global_attempts == 0:
            self._request_global()
            return
        search_timeout = float(self.get_parameter("global_search_timeout").value)
        search_age = ((now - self._global_started).nanoseconds / 1e9
                      if self._global_started is not None else search_timeout)
        if search_age < search_timeout:
            self._request_nomotion()
            return
        retry_limit = max(
            1, int(self.get_parameter("global_retry_limit").value))
        if self._global_attempts < retry_limit and self._manual_motion_detected():
            self._set_status(
                "UNLOCALIZED", score or 0.0,
                reason + "; manual motion detected; restarting bounded global search")
            self._request_global()
            return
        self._set_status(
            "UNLOCALIZED", score or 0.0,
            reason + "; stationary global search exhausted; short manual motion required")


def main(args=None):
    rclpy.init(args=args)
    node = LocalizationGuard()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
