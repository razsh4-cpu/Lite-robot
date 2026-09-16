#!/usr/bin/env python3
"""Replay a short /scan window into ICP on an isolated ROS domain.

This tool starts no robot-control component.  It replays only recorded scan
and cmd_vel messages, disables ICP TF publication, and writes a compact JSON
summary plus the complete ICP process log for repeatable parameter studies.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rtabmap_msgs.msg import OdomInfo
from sensor_msgs.msg import LaserScan


def stamp(message) -> float:
    return message.header.stamp.sec + message.header.stamp.nanosec * 1e-9


def yaw(message: Odometry) -> float:
    q = message.pose.pose.orientation
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class Monitor(Node):
    def __init__(self) -> None:
        super().__init__(
            "icp_replay_monitor",
            parameter_overrides=[Parameter("use_sim_time", value=True)],
        )
        self.scans: list[tuple[float, str, int]] = []
        self.odom: list[tuple[float, float, float, float]] = []
        self.info: list[tuple[float, bool, float, float, float]] = []
        self.commands: list[tuple[float, float, float, float]] = []
        qos = qos_profile_sensor_data
        self.create_subscription(LaserScan, "/replay/scan", self.on_scan, qos)
        self.create_subscription(Odometry, "/replay/odom", self.on_odom, qos)
        self.create_subscription(OdomInfo, "/replay/odom_info", self.on_info, qos)
        self.create_subscription(Twist, "/replay/cmd_vel", self.on_cmd, qos)

    def on_scan(self, message: LaserScan) -> None:
        self.scans.append((stamp(message), message.header.frame_id, len(message.ranges)))

    def on_odom(self, message: Odometry) -> None:
        p = message.pose.pose.position
        self.odom.append((stamp(message), float(p.x), float(p.y), yaw(message)))

    def on_info(self, message: OdomInfo) -> None:
        self.info.append((
            self.get_clock().now().nanoseconds * 1e-9,
            bool(message.lost), float(message.icp_inliers_ratio),
            float(message.icp_translation), float(message.icp_rotation)))

    def on_cmd(self, message: Twist) -> None:
        self.commands.append((
            self.get_clock().now().nanoseconds * 1e-9,
            float(message.linear.x), float(message.linear.y),
            float(message.angular.z)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--bag", type=Path, required=True)
    parser.add_argument("--start-offset", type=float, default=558.0)
    parser.add_argument("--duration", type=float, default=9.0)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("/home/abx/ros2_ws/logs/icp_replay"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.output_dir / f"{args.name}.log"
    summary_path = args.output_dir / f"{args.name}.json"

    # Put the monitor and both subprocesses on a domain isolated from all
    # live robot/sensor nodes before rclpy is initialized.
    os.environ.setdefault("ROS_DOMAIN_ID", "77")
    env = os.environ.copy()
    icp_command = [
        "ros2", "run", "rtabmap_odom", "icp_odometry", "--ros-args",
        "--params-file", str(args.params),
        "-r", "scan:=/replay/scan", "-r", "odom:=/replay/odom",
        "-r", "odom_info:=/replay/odom_info",
    ]
    play_command = [
        "ros2", "bag", "play", str(args.bag), "--clock", "100",
        "--disable-keyboard-controls", "--start-offset", str(args.start_offset),
        "--playback-duration", str(args.duration),
        "--topics", "/scan", "/cmd_vel",
        "--remap", "/scan:=/replay/scan", "/cmd_vel:=/replay/cmd_vel",
    ]

    with log_path.open("w", encoding="utf-8") as log:
        icp = subprocess.Popen(icp_command, env=env, stdout=log,
                               stderr=subprocess.STDOUT, text=True)
        try:
            time.sleep(1.0)
            player = subprocess.Popen(play_command, env=env, stdout=log,
                                      stderr=subprocess.STDOUT, text=True)
            rclpy.init()
            monitor = Monitor()
            while player.poll() is None:
                rclpy.spin_once(monitor, timeout_sec=0.05)
            for _ in range(20):
                rclpy.spin_once(monitor, timeout_sec=0.05)
            monitor.destroy_node()
            rclpy.shutdown()
        finally:
            icp.terminate()
            try:
                icp.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                icp.kill()
                icp.wait()

    text = log_path.read_text(encoding="utf-8", errors="replace")
    scan_times = [x[0] for x in monitor.scans]
    odom_times = [x[0] for x in monitor.odom]
    nonzero = [x for x in monitor.commands if abs(x[1]) + abs(x[2]) + abs(x[3]) > 1e-9]
    result = {
        "name": args.name,
        "params": str(args.params),
        "start_offset_s": args.start_offset,
        "duration_s": args.duration,
        "scan_count": len(monitor.scans),
        "scan_frame_ids": sorted({x[1] for x in monitor.scans}),
        "scan_mean_hz": ((len(scan_times) - 1) / (scan_times[-1] - scan_times[0])
                         if len(scan_times) > 1 else None),
        "odom_count": len(monitor.odom),
        "first_odom_stamp": odom_times[0] if odom_times else None,
        "last_odom_stamp": odom_times[-1] if odom_times else None,
        "odom_coverage_s": (odom_times[-1] - odom_times[0]
                            if len(odom_times) > 1 else 0.0),
        "last_scan_minus_last_odom_s": (scan_times[-1] - odom_times[-1]
                                         if scan_times and odom_times else None),
        "nonzero_command_count": len(nonzero),
        "nonzero_command_start": nonzero[0][0] if nonzero else None,
        "nonzero_command_end": nonzero[-1][0] if nonzero else None,
        "lost_info_count": sum(x[1] for x in monitor.info),
        "min_positive_inlier_ratio": (
            min(x[2] for x in monitor.info if x[2] > 0.0)
            if any(x[2] > 0.0 for x in monitor.info) else None),
        "null_guess_errors": text.count("cannot do registration with a null guess"),
        "registration_failures": text.count("Registration failed"),
        "trajectory": None,
        "log": str(log_path),
    }
    if len(monitor.odom) > 1:
        first, last = monitor.odom[0], monitor.odom[-1]
        result["trajectory"] = {
            "dx_m": last[1] - first[1], "dy_m": last[2] - first[2],
            "distance_m": math.hypot(last[1] - first[1], last[2] - first[2]),
            "dyaw_rad": math.atan2(math.sin(last[3] - first[3]),
                                    math.cos(last[3] - first[3])),
        }
    summary_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
