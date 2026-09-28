#!/usr/bin/env python3
"""Publish the selected dry path/goal for RViz; never publishes motion."""
import json
import math
import os
from pathlib import Path
import signal
import time
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path as PathMessage
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("session", type=Path)
    args = parser.parse_args()
    payload = json.loads((args.session / "planned_path.json").read_text())
    path = payload["path"] if "path" in payload else payload
    goal_data = json.loads((args.session / "selected_goal.json").read_text())
    rclpy.init()
    node = Node("lite3_obstacle_test_plan_display")
    qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL)
    path_pub = node.create_publisher(PathMessage, "/planned_path", qos)
    goal_pub = node.create_publisher(PoseStamped, "/day2/preview_goal", qos)
    path_msg = PathMessage()
    path_msg.header.frame_id = path.get("frame_id", "map")
    goal = PoseStamped()
    goal.header.frame_id = "map"
    goal.pose.position.x = goal_data["x"]
    goal.pose.position.y = goal_data["y"]
    goal.pose.position.z = goal_data.get("z", 0.0)
    goal.pose.orientation.x = goal_data.get("qx", 0.0)
    goal.pose.orientation.y = goal_data.get("qy", 0.0)
    goal.pose.orientation.z = goal_data.get("qz", 0.0)
    goal.pose.orientation.w = goal_data.get("qw", 1.0)
    for item in path["poses"]:
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.pose.position.x = item["x"]
        pose.pose.position.y = item["y"]
        pose.pose.position.z = item.get("z", 0.0)
        pose.pose.orientation.x = item.get("qx", 0.0)
        pose.pose.orientation.y = item.get("qy", 0.0)
        pose.pose.orientation.z = item.get("qz", 0.0)
        pose.pose.orientation.w = item.get("qw", 1.0)
        path_msg.poses.append(pose)
    running = True
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        while running:
            stamp = node.get_clock().now().to_msg()
            path_msg.header.stamp = stamp
            goal.header.stamp = stamp
            for pose in path_msg.poses:
                pose.header.stamp = stamp
            path_pub.publish(path_msg)
            goal_pub.publish(goal)
            rclpy.spin_once(node, timeout_sec=0.25)
            time.sleep(0.25)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
