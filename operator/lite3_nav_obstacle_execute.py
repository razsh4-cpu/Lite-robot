#!/usr/bin/env python3
"""Execute one already selected obstacle-test goal through existing Nav2."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32, String


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def quaternion_from_dict(pose):
    from geometry_msgs.msg import Quaternion
    return Quaternion(x=pose.get("qx", 0.0), y=pose.get("qy", 0.0),
                      z=pose.get("qz", 0.0), w=pose.get("qw", 1.0))


def command_source():
    robot = os.environ.get("LITE3_ROBOT_SSH", "abx@192.168.2.32")
    try:
        result = subprocess.run([
            "ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=2",
            robot, "cat", "/run/lite3-control/COMMAND_SOURCE"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=3.0, check=False)
    except subprocess.TimeoutExpired:
        return "UNKNOWN"
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


class Execute(Node):
    def __init__(self, session: Path, localization_threshold: float = 0.80):
        super().__init__("lite3_builtin_obstacle_test")
        self.session = session
        self.localization_threshold = float(localization_threshold)
        self.client = ActionClient(self, NavigateToPose, "/navigate_to_pose")
        self.stamps = {"scan": None, "odom": None, "localization": None,
                       "battery": None, "cmd_vel": None,
                       "local_costmap": None, "global_costmap": None}
        self.localization = 0.0
        self.localization_state = "UNAVAILABLE"
        self.battery = None
        self.low_since = None
        self.max_cmd = [0.0, 0.0, 0.0]
        self.trace = []
        self.cancel_requested = False
        self.feedback_distance = None
        self.source_probe = None
        self.source_probe_started = None
        status_qos = QoSProfile(depth=1)
        status_qos.reliability = ReliabilityPolicy.RELIABLE
        status_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self.create_subscription(LaserScan, "/scan", lambda _: self.touch("scan"), qos_profile_sensor_data)
        self.create_subscription(Odometry, "/odom", lambda _: self.touch("odom"), qos_profile_sensor_data)
        self.create_subscription(OccupancyGrid, "/local_costmap/costmap",
                                 lambda _: self.touch("local_costmap"), status_qos)
        self.create_subscription(OccupancyGrid, "/global_costmap/costmap",
                                 lambda _: self.touch("global_costmap"), status_qos)
        self.create_subscription(Float32, "/lite3/battery_percent", self.on_battery, qos_profile_sensor_data)
        self.create_subscription(String, "/localization/status", self.on_localization, status_qos)
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd, qos_profile_sensor_data)

    def now_mono(self):
        return time.monotonic()

    def touch(self, name):
        self.stamps[name] = self.now_mono()

    def on_battery(self, msg):
        self.battery = float(msg.data)
        self.touch("battery")

    def on_localization(self, msg):
        try:
            value = json.loads(msg.data)
            self.localization = float(value.get("match_fraction", 0.0))
            self.localization_state = str(value.get("state", "UNLOCALIZED"))
        except (TypeError, ValueError, json.JSONDecodeError):
            self.localization = 0.0
            self.localization_state = "UNAVAILABLE"
        self.touch("localization")

    def on_cmd(self, msg):
        values = [float(msg.linear.x), float(msg.linear.y), float(msg.angular.z)]
        self.max_cmd = [max(old, abs(value)) for old, value in zip(self.max_cmd, values)]
        self.touch("cmd_vel")
        self.trace.append({"t": time.time(), "vx": values[0], "vy": values[1],
                           "wz": values[2], "localization": self.localization})

    def feedback(self, message):
        self.feedback_distance = float(message.feedback.distance_remaining)

    def start_source_probe(self):
        if self.source_probe is not None:
            return
        robot = os.environ.get("LITE3_ROBOT_SSH", "abx@192.168.2.32")
        self.source_probe = subprocess.Popen([
            "ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=2",
            robot, "cat", "/run/lite3-control/COMMAND_SOURCE"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.source_probe_started = self.now_mono()

    def poll_source_probe(self):
        if self.source_probe is None:
            return None
        if self.source_probe.poll() is None:
            if self.now_mono() - self.source_probe_started > 2.5:
                self.source_probe.kill()
                self.source_probe.wait(timeout=1.0)
                self.source_probe = None
                return "UNKNOWN"
            return None
        output = self.source_probe.stdout.read().strip()
        code = self.source_probe.returncode
        self.source_probe = None
        return output if code == 0 and output else "UNKNOWN"

    def stop_source_probe(self):
        if self.source_probe is not None and self.source_probe.poll() is None:
            self.source_probe.kill()
            self.source_probe.wait(timeout=1.0)
        self.source_probe = None

    def readiness_failure(self, require_cmd=False):
        now = self.now_mono()
        for key, timeout in (("scan", 1.0), ("odom", 1.0),
                             ("localization", 3.0), ("battery", 2.0),
                             ("local_costmap", 3.0), ("global_costmap", 3.0)):
            stamp = self.stamps[key]
            if stamp is None or now - stamp > timeout:
                return f"{key} stale"
        if self.battery is None or self.battery < 25.0:
            return "battery below safe threshold"
        if (self.localization_state != "LOCALIZED" or
                self.localization < self.localization_threshold):
            return ("localization below active test threshold "
                    f"{100.0 * self.localization_threshold:.0f}%")
        if require_cmd:
            stamp = self.stamps["cmd_vel"]
            if stamp is None or now - stamp > 0.50:
                return "cmd_vel stale"
        if (self.max_cmd[0] > 0.1001 or self.max_cmd[1] > 0.0501 or
                self.max_cmd[2] > 0.2001):
            return "cmd_vel exceeds configured limits"
        return None


def execute(session: Path, localization_threshold: float = 0.80) -> dict:
    selected = load(session / "selected_goal.json")
    rclpy.init()
    node = Execute(session, localization_threshold)
    handle = None
    result = {"success": False, "reason": "unknown", "started_unix": time.time()}
    def request_cancel(*_):
        node.cancel_requested = True
    signal.signal(signal.SIGINT, request_cancel)
    signal.signal(signal.SIGTERM, request_cancel)
    try:
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline and node.readiness_failure(False):
            rclpy.spin_once(node, timeout_sec=0.1)
        failure = node.readiness_failure(False)
        if failure:
            result["reason"] = failure
            return result
        if command_source() != "AUTONOMY":
            result["reason"] = "AUTONOMY ownership lost before goal"
            return result
        if not node.client.wait_for_server(timeout_sec=5.0):
            result["reason"] = "NavigateToPose unavailable"
            return result
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = node.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(selected["x"])
        goal.pose.pose.position.y = float(selected["y"])
        goal.pose.pose.position.z = float(selected.get("z", 0.0))
        goal.pose.pose.orientation = quaternion_from_dict(selected)
        sent = node.client.send_goal_async(goal, feedback_callback=node.feedback)
        rclpy.spin_until_future_complete(node, sent, timeout_sec=5.0)
        handle = sent.result()
        if handle is None or not handle.accepted:
            result["reason"] = "NavigateToPose goal rejected"
            return result
        future = handle.get_result_async()
        deadline = time.monotonic() + 60.0
        command_seen = False
        next_source_check = time.monotonic() + 1.0
        while not future.done() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            command_seen = command_seen or node.stamps["cmd_vel"] is not None
            if node.cancel_requested:
                result["reason"] = "operator cancel"
                break
            if time.monotonic() >= next_source_check:
                node.start_source_probe()
                next_source_check = time.monotonic() + 1.0
            observed_source = node.poll_source_probe()
            if observed_source is not None and observed_source != "AUTONOMY":
                result["reason"] = (
                    f"AUTONOMY ownership probe failed: {observed_source}")
                break
            failure = node.readiness_failure(require_cmd=command_seen)
            if failure:
                result["reason"] = failure
                break
        if not future.done():
            if handle is not None:
                cancel = handle.cancel_goal_async()
                rclpy.spin_until_future_complete(node, cancel, timeout_sec=3.0)
            if result["reason"] == "unknown":
                result["reason"] = "60 second bounded timeout"
            return result
        wrapped = future.result()
        result["action_status"] = int(wrapped.status)
        result["success"] = wrapped.status == 4
        result["reason"] = "goal reached" if result["success"] else f"action status {wrapped.status}"
        return result
    finally:
        result.update({
            "finished_unix": time.time(),
            "localization_final": node.localization,
            "max_cmd_vx": node.max_cmd[0],
            "max_cmd_vy": node.max_cmd[1],
            "max_cmd_wz": node.max_cmd[2],
            "last_distance_remaining": node.feedback_distance,
            "cmd_vel_trace": node.trace,
        })
        (session / "execution.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        node.stop_source_probe()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("session", type=Path)
    parser.add_argument("--localization-threshold", type=float, default=0.80)
    args = parser.parse_args()
    if args.localization_threshold not in (0.70, 0.80):
        parser.error("localization threshold must be 0.70 or 0.80")
    result = execute(args.session.resolve(), args.localization_threshold)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("success") else 4


if __name__ == "__main__":
    raise SystemExit(main())
