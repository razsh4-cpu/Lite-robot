#!/usr/bin/env python3
"""Persist a reconstruction-complete, planning-only Lite3 obstacle dry run.

This tool never publishes velocity, invokes NavigateToPose, or acquires a
command-source lease.  It uses ComputePathToPose only and writes one bounded
diagnostic package for an explicitly requested general obstacle-test session.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
from pathlib import Path
import time
from typing import Iterable

os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")

import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Twist
from nav2_msgs.action import ComputePathToPose
from nav_msgs.msg import OccupancyGrid, Odometry, Path as PathMessage
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener


RAW_HALF = (0.305, 0.185)
PADDED_HALF = (0.355, 0.235)


def yaw(quaternion) -> float:
    return math.atan2(
        2.0 * (quaternion.w * quaternion.z + quaternion.x * quaternion.y),
        1.0 - 2.0 * (quaternion.y * quaternion.y + quaternion.z * quaternion.z),
    )


def transform_xy(transform, x: float, y: float) -> tuple[float, float]:
    angle = yaw(transform.rotation)
    return (
        transform.translation.x + math.cos(angle) * x - math.sin(angle) * y,
        transform.translation.y + math.sin(angle) * x + math.cos(angle) * y,
    )


def rectangle(x: float, y: float, angle: float, half: tuple[float, float]):
    hx, hy = half
    cosine, sine = math.cos(angle), math.sin(angle)
    return [
        (x + cosine * dx - sine * dy, y + sine * dx + cosine * dy)
        for dx, dy in ((hx, hy), (hx, -hy), (-hx, -hy), (-hx, hy))
    ]


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def point_segment_distance(point, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    denominator = vx * vx + vy * vy
    factor = 0.0 if denominator == 0.0 else max(
        0.0,
        min(1.0, ((point[0] - a[0]) * vx + (point[1] - a[1]) * vy) / denominator),
    )
    return math.hypot(
        point[0] - (a[0] + factor * vx),
        point[1] - (a[1] + factor * vy),
    )


def inside(point, polygon):
    signs = [cross(polygon[index], polygon[(index + 1) % len(polygon)], point)
             for index in range(len(polygon))]
    return all(value >= -1e-9 for value in signs) or all(
        value <= 1e-9 for value in signs)


def polygon_distance(left, right):
    if any(inside(point, right) for point in left) or any(
            inside(point, left) for point in right):
        return 0.0
    return min(
        [point_segment_distance(point, right[index], right[(index + 1) % len(right)])
         for point in left for index in range(len(right))]
        + [point_segment_distance(point, left[index], left[(index + 1) % len(left)])
           for point in right for index in range(len(left))]
    )


def stamp(message):
    return {"sec": int(message.sec), "nanosec": int(message.nanosec)}


def pose_dict(pose):
    return {
        "x": pose.position.x,
        "y": pose.position.y,
        "z": pose.position.z,
        "qx": pose.orientation.x,
        "qy": pose.orientation.y,
        "qz": pose.orientation.z,
        "qw": pose.orientation.w,
        "yaw": yaw(pose.orientation),
    }


def path_dict(path):
    return {
        "frame_id": path.header.frame_id,
        "stamp": stamp(path.header.stamp),
        "poses": [pose_dict(item.pose) for item in path.poses],
    }


def grid_dict(grid):
    return {
        "frame_id": grid.header.frame_id,
        "stamp": stamp(grid.header.stamp),
        "resolution": grid.info.resolution,
        "width": grid.info.width,
        "height": grid.info.height,
        "origin": pose_dict(grid.info.origin),
        "data": list(grid.data),
    }


def scan_dict(scan):
    return {
        "frame_id": scan.header.frame_id,
        "stamp": stamp(scan.header.stamp),
        "angle_min": scan.angle_min,
        "angle_max": scan.angle_max,
        "angle_increment": scan.angle_increment,
        "range_min": scan.range_min,
        "range_max": scan.range_max,
        "ranges": [None if not math.isfinite(value) else value for value in scan.ranges],
        "intensities": list(scan.intensities),
    }


class DryRun(Node):
    def __init__(self):
        super().__init__("lite3_chair_dryrun_snapshot")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.planner = ActionClient(self, ComputePathToPose, "/compute_path_to_pose")
        self.scan = self.local = self.global_cost = self.static_map = None
        self.amcl = self.localization = None
        self.odom = self.cmd_vel = None
        latched = QoSProfile(depth=1)
        latched.reliability = ReliabilityPolicy.RELIABLE
        latched.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.create_subscription(LaserScan, "/scan", self._set_scan, qos_profile_sensor_data)
        self.create_subscription(OccupancyGrid, "/local_costmap/costmap", self._set_local, latched)
        self.create_subscription(OccupancyGrid, "/global_costmap/costmap", self._set_global, latched)
        self.create_subscription(OccupancyGrid, "/map", self._set_map, latched)
        self.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", self._set_amcl, latched)
        self.create_subscription(String, "/localization/status", self._set_localization, latched)
        self.create_subscription(Odometry, "/odom", self._set_odom, qos_profile_sensor_data)
        self.create_subscription(Twist, "/cmd_vel", self._set_cmd_vel, qos_profile_sensor_data)
        self.path_pub = self.create_publisher(PathMessage, "/planned_path", latched)
        self.goal_pub = self.create_publisher(PoseStamped, "/day2/preview_goal", 10)

    def _set_scan(self, value): self.scan = value
    def _set_local(self, value): self.local = value
    def _set_global(self, value): self.global_cost = value
    def _set_map(self, value): self.static_map = value
    def _set_amcl(self, value): self.amcl = value
    def _set_localization(self, value): self.localization = value
    def _set_odom(self, value): self.odom = value
    def _set_cmd_vel(self, value): self.cmd_vel = value

    def lookup(self, target, source):
        try:
            return self.tf_buffer.lookup_transform(target, source, Time()).transform
        except Exception:
            return None

    def compute(self, goal):
        request = ComputePathToPose.Goal()
        request.goal = goal
        request.planner_id = "GridBased"
        request.use_start = False
        future = self.planner.send_goal_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=4)
        handle = future.result()
        if handle is None or not handle.accepted:
            return None
        result = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result, timeout_sec=6)
        wrapped = result.result()
        if wrapped is None or wrapped.result.error_code != ComputePathToPose.Result.NONE:
            return None
        return wrapped.result.path


def write_json(path: Path, value, compressed=False):
    if compressed:
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            json.dump(value, stream, separators=(",", ":"))
    else:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=str(Path.home() / "lite3_diagnostics" / "obstacle"))
    parser.add_argument("--max-candidates", type=int, default=80)
    args = parser.parse_args()
    session = time.strftime("%Y%m%dT%H%M%S")
    output = Path(args.output_root) / session
    output.mkdir(parents=True, exist_ok=False)
    rclpy.init()
    node = DryRun()
    try:
        deadline = time.monotonic() + 20.0
        map_base = None
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            map_base = node.lookup("map", "base_link")
            if all((node.scan, node.local, node.global_cost, node.static_map,
                    node.amcl, node.localization, node.odom, map_base)):
                break
        if not all((node.scan, node.local, node.global_cost, node.static_map,
                    node.amcl, node.localization, node.odom, map_base)):
            raise SystemExit("SNAPSHOT BLOCKED: required live data unavailable")
        if not node.planner.wait_for_server(timeout_sec=8):
            raise SystemExit("SNAPSHOT BLOCKED: planner unavailable")

        transforms = {}
        for parent, child in (("map", "odom"), ("odom", "base_link"),
                              ("map", "base_link"), ("base_link", node.scan.header.frame_id)):
            value = node.lookup(parent, child)
            if value is None:
                raise SystemExit(f"SNAPSHOT BLOCKED: missing TF {parent}->{child}")
            transforms[f"{parent}->{child}"] = {
                "translation": [value.translation.x, value.translation.y, value.translation.z],
                "rotation": [value.rotation.x, value.rotation.y, value.rotation.z, value.rotation.w],
            }

        write_json(output / "scan.json.gz", scan_dict(node.scan), True)
        write_json(output / "local_costmap.json.gz", grid_dict(node.local), True)
        write_json(output / "global_costmap.json.gz", grid_dict(node.global_cost), True)
        write_json(output / "static_map.json.gz", grid_dict(node.static_map), True)
        write_json(output / "tf.json", transforms)

        localization = json.loads(node.localization.data)
        start_x, start_y, heading = (map_base.translation.x,
                                     map_base.translation.y,
                                     yaw(map_base.rotation))
        candidates = []
        goals = []
        for forward_tenths in range(6, 25, 2):
            forward = forward_tenths / 10.0
            for lateral_tenths in range(-20, 21, 2):
                lateral = lateral_tenths / 10.0
                if abs(lateral) < 0.4 or math.hypot(forward, lateral) > 3.0:
                    continue
                goals.append((math.hypot(forward, lateral), forward, lateral))
        goals.sort()

        # Preserve every returned path. Clearance computation is deliberately
        # performed by the offline replay utility from the immutable snapshot;
        # this keeps acquisition bounded and makes the result reproducible.
        for _, forward, lateral in goals[:args.max_candidates]:
            goal = PoseStamped()
            goal.header.frame_id = "map"
            goal.header.stamp = node.get_clock().now().to_msg()
            goal.pose.position.x = start_x + forward * math.cos(heading) - lateral * math.sin(heading)
            goal.pose.position.y = start_y + forward * math.sin(heading) + lateral * math.cos(heading)
            goal.pose.orientation = map_base.rotation
            path = node.compute(goal)
            if path is None or len(path.poses) < 2:
                continue
            length = sum(math.hypot(b.pose.position.x - a.pose.position.x,
                                    b.pose.position.y - a.pose.position.y)
                         for a, b in zip(path.poses, path.poses[1:]))
            name = f"candidate_{len(candidates):03d}.json"
            write_json(output / name, path_dict(path))
            candidates.append({
                "file": name,
                "forward": forward,
                "lateral": lateral,
                "path_length": length,
                "pose_count": len(path.poses),
            })

        metadata = {
            "session_id": session,
            "created_unix": time.time(),
            "motion_sent": False,
            "command_source_required": "NONE",
            "robot_pose": {"x": start_x, "y": start_y, "yaw": heading},
            "localization": localization,
            "odom": {"frame_id": node.odom.header.frame_id,
                     "child_frame_id": node.odom.child_frame_id,
                     "stamp": stamp(node.odom.header.stamp),
                     "pose": pose_dict(node.odom.pose.pose),
                     "twist": {"vx": node.odom.twist.twist.linear.x,
                               "vy": node.odom.twist.twist.linear.y,
                               "wz": node.odom.twist.twist.angular.z}},
            "cmd_vel_at_snapshot": ({"vx": node.cmd_vel.linear.x,
                                      "vy": node.cmd_vel.linear.y,
                                      "wz": node.cmd_vel.angular.z}
                                     if node.cmd_vel is not None else None),
            "amcl_covariance": list(node.amcl.pose.covariance),
            "raw_body": {"length": 0.610, "width": 0.370},
            "footprint": [[0.355, 0.235], [0.355, -0.235],
                          [-0.355, -0.235], [-0.355, 0.235]],
            "footprint_padding": 0.0,
            "inflation_radius": 0.30,
            "cost_scaling_factor": 4.0,
            "velocity_limits": {"forward": 0.10, "lateral": 0.05, "yaw": 0.20},
            "candidate_count": len(candidates),
            "candidates": candidates,
        }
        write_json(output / "metadata.json", metadata)
        print(json.dumps({"session_id": session, "snapshot": str(output),
                          "candidate_count": len(candidates), "motion_sent": False},
                         sort_keys=True))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
