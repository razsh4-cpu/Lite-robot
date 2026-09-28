#!/usr/bin/env python3
"""Request a 10 cm planning-only preview; never executes navigation."""
import argparse
import json
import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener


class Preview(Node):
    def __init__(self, distance=0.10, yaw_change=0.0):
        super().__init__("lite3_preview_10cm")
        self.distance = float(distance)
        self.yaw_change = float(yaw_change)
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.publisher = self.create_publisher(PoseStamped, "/day2/preview_goal", 10)
        self.path = None
        self.create_subscription(Path, "/planned_path", self._path, 10)

    def _path(self, msg):
        # A planner may briefly publish an empty clearing path before the
        # computed result. Only a non-empty plan completes the preview.
        if msg.poses:
            self.path = msg

    def run(self):
        deadline = time.monotonic() + 15.0
        transform = None
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            try:
                transform = self.buffer.lookup_transform(
                    "map", "base_link", rclpy.time.Time(),
                    timeout=Duration(seconds=0.1))
                if self.publisher.get_subscription_count() > 0:
                    break
            except TransformException:
                pass
        if transform is None or self.publisher.get_subscription_count() == 0:
            raise RuntimeError("planning bridge or map->base_link TF unavailable")
        q = transform.transform.rotation
        yaw = math.atan2(2.0 * (q.w*q.z + q.x*q.y),
                         1.0 - 2.0 * (q.y*q.y + q.z*q.z))
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.pose.position.x = transform.transform.translation.x + self.distance * math.cos(yaw)
        goal.pose.position.y = transform.transform.translation.y + self.distance * math.sin(yaw)
        goal_yaw = yaw + self.yaw_change
        goal.pose.orientation.z = math.sin(goal_yaw / 2.0)
        goal.pose.orientation.w = math.cos(goal_yaw / 2.0)
        self.publisher.publish(goal)
        rclpy.spin_once(self, timeout_sec=0.25)
        deadline = time.monotonic() + 15.0
        while self.path is None and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
        if self.path is None or not self.path.poses:
            raise RuntimeError("planner returned no preview path")
        length = sum(math.hypot(b.pose.position.x-a.pose.position.x,
                                b.pose.position.y-a.pose.position.y)
                     for a, b in zip(self.path.poses, self.path.poses[1:]))
        print(json.dumps({
            "preview_only": True,
            "start": {"x": transform.transform.translation.x,
                      "y": transform.transform.translation.y, "yaw": yaw},
            "goal": {"x": goal.pose.position.x, "y": goal.pose.position.y,
                     "yaw": goal_yaw},
            "poses": len(self.path.poses), "path_length_m": round(length, 3),
        }, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Planning-only Lite3 goal preview")
    parser.add_argument("--distance", type=float, default=0.10)
    parser.add_argument("--yaw-deg", type=float, default=0.0)
    args = parser.parse_args()
    if not 0.05 <= args.distance <= 2.0 or abs(args.yaw_deg) > 90.0:
        raise SystemExit("preview goal outside bounded test range")
    rclpy.init()
    node = Preview(args.distance, math.radians(args.yaw_deg))
    try:
        node.run()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
