#!/usr/bin/env python3
"""Planning-only close-obstacle validation. Never publishes motion."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")

import json
import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose
from nav_msgs.msg import OccupancyGrid
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener

BODY_FRONT_X = 0.355
EXPECTED_BODY_CLEARANCE = (0.05, 0.35)
LETHAL_COST_MIN = 90


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y),
                      1 - 2 * (q.y * q.y + q.z * q.z))


def transform_xy(transform, x, y):
    angle = yaw(transform.rotation)
    return (transform.translation.x + math.cos(angle) * x - math.sin(angle) * y,
            transform.translation.y + math.sin(angle) * x + math.cos(angle) * y)


def grid_cost(grid, x, y, radius_cells=2):
    origin = grid.info.origin.position
    resolution = grid.info.resolution
    gx = math.floor((x - origin.x) / resolution)
    gy = math.floor((y - origin.y) / resolution)
    values = []
    for yy in range(gy - radius_cells, gy + radius_cells + 1):
        for xx in range(gx - radius_cells, gx + radius_cells + 1):
            if 0 <= xx < grid.info.width and 0 <= yy < grid.info.height:
                values.append(grid.data[yy * grid.info.width + xx])
    return max(values) if values else -1


class Preview(Node):
    def __init__(self):
        super().__init__("lite3_close_obstacle_preview")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.client = ActionClient(self, ComputePathToPose, "/compute_path_to_pose")
        self.goal_pub = self.create_publisher(PoseStamped, "/day2/preview_goal", 10)
        cost_qos = QoSProfile(depth=1)
        cost_qos.reliability = ReliabilityPolicy.RELIABLE
        cost_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.scan_msg = None
        self.local_costmap = None
        self.global_costmap = None
        self.create_subscription(LaserScan, "/scan", self._scan, qos_profile_sensor_data)
        self.create_subscription(OccupancyGrid, "/local_costmap/costmap", self._local, cost_qos)
        self.create_subscription(OccupancyGrid, "/global_costmap/costmap", self._global, cost_qos)

    def _scan(self, msg):
        self.scan_msg = msg

    def _local(self, msg):
        self.local_costmap = msg

    def _global(self, msg):
        self.global_costmap = msg

    def lookup(self, target, source):
        try:
            return self.tf_buffer.lookup_transform(target, source, Time()).transform
        except Exception:
            return None

    def front_obstacle(self):
        scan = self.scan_msg
        if scan is None:
            return None
        tf_base_scan = self.lookup("base_link", scan.header.frame_id)
        if tf_base_scan is None:
            return None
        best = None
        for index, distance in enumerate(scan.ranges):
            if not math.isfinite(distance) or not scan.range_min <= distance <= scan.range_max:
                continue
            angle = scan.angle_min + index * scan.angle_increment
            bx, by = transform_xy(tf_base_scan,
                                  distance * math.cos(angle),
                                  distance * math.sin(angle))
            if bx <= BODY_FRONT_X or abs(math.atan2(by, bx)) > math.radians(25):
                continue
            clearance = bx - BODY_FRONT_X
            if best is None or clearance < best[0]:
                best = (clearance, bx, by, scan.header.frame_id,
                        distance * math.cos(angle), distance * math.sin(angle))
        return best

    def verify_costmap(self, obstacle):
        _, _, _, scan_frame, sx, sy = obstacle
        evidence = {}
        for name, grid in (("local", self.local_costmap),
                           ("global", self.global_costmap)):
            if grid is None:
                evidence[name] = None
                continue
            transform = self.lookup(grid.header.frame_id, scan_frame)
            if transform is None:
                evidence[name] = None
                continue
            gx, gy = transform_xy(transform, sx, sy)
            evidence[name] = grid_cost(grid, gx, gy)
        return evidence

    def compute(self, pose):
        request = ComputePathToPose.Goal()
        request.goal = pose
        request.planner_id = "GridBased"
        request.use_start = False
        sent = self.client.send_goal_async(request)
        rclpy.spin_until_future_complete(self, sent, timeout_sec=6)
        handle = sent.result()
        if handle is None or not handle.accepted:
            return None
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=10)
        wrapped = result_future.result()
        if wrapped is None or wrapped.result.error_code != ComputePathToPose.Result.NONE:
            return None
        return wrapped.result.path


def main():
    rclpy.init()
    node = Preview()
    try:
        deadline = time.monotonic() + 15.0
        map_base = None
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            map_base = node.lookup("map", "base_link")
            if (map_base is not None and node.scan_msg is not None and
                    node.local_costmap is not None and node.global_costmap is not None):
                break
        if map_base is None or node.scan_msg is None:
            raise SystemExit("PREVIEW BLOCKED: LiDAR/TF unavailable")
        obstacle = node.front_obstacle()
        if obstacle is None:
            raise SystemExit("PREVIEW BLOCKED: chair not detected in front")
        clearance, bx, by, *_ = obstacle
        costs = node.verify_costmap(obstacle)
        if not EXPECTED_BODY_CLEARANCE[0] <= clearance <= EXPECTED_BODY_CLEARANCE[1]:
            raise SystemExit(
                f"PREVIEW BLOCKED: expected chair 5-35 cm from body; measured={clearance:.2f} m")
        if not any(value is not None and value >= LETHAL_COST_MIN for value in costs.values()):
            raise SystemExit(
                f"PREVIEW BLOCKED: chair not lethal in costmap; costs={costs}")
        if not node.client.wait_for_server(timeout_sec=8):
            raise SystemExit("PREVIEW BLOCKED: planner unavailable")

        start_x = map_base.translation.x
        start_y = map_base.translation.y
        heading = yaw(map_base.rotation)
        # Shortest candidates first. NavFn/costmaps decide whether any is safe.
        candidates = []
        for lateral in (0.32, -0.32, 0.40, -0.40):
            forward = 0.10 if abs(lateral) <= 0.32 else 0.15
            pose = PoseStamped()
            pose.header.frame_id = "map"
            pose.header.stamp = node.get_clock().now().to_msg()
            pose.pose.position.x = (start_x + forward * math.cos(heading)
                                    - lateral * math.sin(heading))
            pose.pose.position.y = (start_y + forward * math.sin(heading)
                                    + lateral * math.cos(heading))
            pose.pose.orientation = map_base.rotation
            path = node.compute(pose)
            if path is None or len(path.poses) < 2:
                continue
            length = sum(math.hypot(b.pose.position.x - a.pose.position.x,
                                    b.pose.position.y - a.pose.position.y)
                         for a, b in zip(path.poses, path.poses[1:]))
            candidates.append((length, pose, path, forward, lateral))

        if not candidates:
            print(json.dumps({
                "motion_sent": False,
                "chair_detected": True,
                "body_clearance_m": round(clearance, 3),
                "local_cost": costs["local"],
                "global_cost": costs["global"],
                "result": "NO SAFE PATH — OBSTACLE TOO CLOSE",
            }, sort_keys=True))
            return 4

        length, pose, path, forward, lateral = min(candidates, key=lambda item: item[0])
        discovery = time.monotonic() + 3.0
        while (node.count_subscribers("/day2/preview_goal") == 0 and
               time.monotonic() < discovery):
            rclpy.spin_once(node, timeout_sec=0.1)
        node.goal_pub.publish(pose)
        for _ in range(12):
            rclpy.spin_once(node, timeout_sec=0.1)
        print(json.dumps({
            "motion_sent": False,
            "chair_detected": True,
            "body_clearance_m": round(clearance, 3),
            "obstacle_base_x": round(bx, 3),
            "obstacle_base_y": round(by, 3),
            "local_cost": costs["local"],
            "global_cost": costs["global"],
            "path_safe_for_execution": True,
            "path_length_m": round(length, 3),
            "path_poses": len(path.poses),
            "goal_forward_m": forward,
            "goal_lateral_m": lateral,
        }, sort_keys=True))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
