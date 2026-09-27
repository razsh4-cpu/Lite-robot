#!/usr/bin/env python3
"""Execute one explicitly approved short Nav2 translation-plus-turn goal."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")

from pathlib import Path
import json
import math
import time
import sys

import rclpy
from geometry_msgs.msg import Twist
from nav2_msgs.action import ComputePathToPose, NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


SOURCE = Path("/run/lite3-control/COMMAND_SOURCE")
DISTANCE_M = 0.50
YAW_CHANGE_RAD = math.radians(20.0)


def owner():
    try:
        return SOURCE.read_text().strip()
    except OSError:
        return "UNKNOWN"


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def quaternion_from_yaw(angle):
    from geometry_msgs.msg import Quaternion
    return Quaternion(z=math.sin(angle / 2.0), w=math.cos(angle / 2.0))


class Execute(Node):
    def __init__(self):
        super().__init__("lite3_execute_turn_goal")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.plan_client = ActionClient(self, ComputePathToPose, "/compute_path_to_pose")
        self.nav_client = ActionClient(self, NavigateToPose, "/navigate_to_pose")
        self.max_cmd = [0.0, 0.0, 0.0]
        self.last_feedback = None
        self.create_subscription(Twist, "/cmd_vel", self.cmd, qos_profile_sensor_data)

    def cmd(self, msg):
        self.max_cmd = [
            max(self.max_cmd[0], abs(msg.linear.x)),
            max(self.max_cmd[1], abs(msg.linear.y)),
            max(self.max_cmd[2], abs(msg.angular.z)),
        ]

    def feedback(self, msg):
        self.last_feedback = float(msg.feedback.distance_remaining)

    def transform(self, timeout=8.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            try:
                return self.tf_buffer.lookup_transform("map", "base_link", Time())
            except Exception:
                pass
        return None


def main():
    plan_only = "--plan-only" in sys.argv[1:]
    if not plan_only and owner() != "AUTONOMY":
        raise SystemExit(f"EXECUTION BLOCKED: COMMAND_SOURCE={owner()}")
    rclpy.init()
    node = Execute()
    try:
        start = node.transform()
        if start is None:
            raise SystemExit("EXECUTION BLOCKED: map->base_link unavailable")
        transform = start.transform
        start_yaw = yaw(transform.rotation)
        goal_x = transform.translation.x + DISTANCE_M * math.cos(start_yaw)
        goal_y = transform.translation.y + DISTANCE_M * math.sin(start_yaw)
        goal_yaw = start_yaw + YAW_CHANGE_RAD

        plan_goal = ComputePathToPose.Goal()
        plan_goal.goal.header.frame_id = "map"
        plan_goal.goal.header.stamp = node.get_clock().now().to_msg()
        plan_goal.goal.pose.position.x = goal_x
        plan_goal.goal.pose.position.y = goal_y
        plan_goal.goal.pose.orientation = quaternion_from_yaw(goal_yaw)
        plan_goal.planner_id = "GridBased"
        plan_goal.use_start = False
        if not node.plan_client.wait_for_server(timeout_sec=5):
            raise SystemExit("EXECUTION BLOCKED: planner unavailable")
        future = node.plan_client.send_goal_async(plan_goal)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5)
        plan_handle = future.result()
        if plan_handle is None or not plan_handle.accepted:
            raise SystemExit("EXECUTION BLOCKED: plan rejected")
        plan_result = plan_handle.get_result_async()
        rclpy.spin_until_future_complete(node, plan_result, timeout_sec=10)
        wrapped_plan = plan_result.result()
        if wrapped_plan is None or wrapped_plan.result.error_code != ComputePathToPose.Result.NONE:
            code = None if wrapped_plan is None else wrapped_plan.result.error_code
            raise SystemExit(f"EXECUTION BLOCKED: no valid path ({code})")
        poses = wrapped_plan.result.path.poses
        path_length = sum(
            math.hypot(b.pose.position.x - a.pose.position.x, b.pose.position.y - a.pose.position.y)
            for a, b in zip(poses, poses[1:])
        )
        print(json.dumps({
            "dry_path_valid": True,
            "path_length_m": round(path_length, 3),
            "path_poses": len(poses),
            "goal_x": round(goal_x, 3),
            "goal_y": round(goal_y, 3),
            "goal_yaw_deg": round(math.degrees(goal_yaw), 1),
        }, sort_keys=True), flush=True)
        if plan_only:
            print("PLAN ONLY — NO MOTION COMMAND SENT", flush=True)
            return

        # Give the read-only command monitor time to match the existing
        # Nav2 publisher before execution. This does not affect control.
        monitor_deadline = time.monotonic() + 3.0
        while node.count_publishers("/cmd_vel") == 0 and time.monotonic() < monitor_deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        settle_deadline = time.monotonic() + 1.0
        while time.monotonic() < settle_deadline:
            rclpy.spin_once(node, timeout_sec=0.1)

        goal = NavigateToPose.Goal()
        goal.pose = plan_goal.goal
        if not node.nav_client.wait_for_server(timeout_sec=5):
            raise SystemExit("EXECUTION BLOCKED: navigate action unavailable")
        future = node.nav_client.send_goal_async(goal, feedback_callback=node.feedback)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5)
        handle = future.result()
        if handle is None or not handle.accepted:
            raise SystemExit("EXECUTION BLOCKED: goal rejected")
        result = handle.get_result_async()
        deadline = time.monotonic() + 35.0
        while not result.done() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            if owner() != "AUTONOMY":
                handle.cancel_goal_async()
                raise SystemExit(f"EXECUTION ABORTED: COMMAND_SOURCE={owner()}")
        if not result.done():
            cancel = handle.cancel_goal_async()
            rclpy.spin_until_future_complete(node, cancel, timeout_sec=3)
            raise SystemExit("EXECUTION ABORTED: 35s timeout")
        wrapped = result.result()
        end = node.transform(3.0)
        if end is None:
            raise SystemExit("EXECUTION ABORTED: final TF unavailable")
        final = end.transform
        displacement = math.hypot(
            final.translation.x - transform.translation.x,
            final.translation.y - transform.translation.y,
        )
        yaw_change = math.degrees(math.atan2(
            math.sin(yaw(final.rotation) - start_yaw),
            math.cos(yaw(final.rotation) - start_yaw),
        ))
        print(json.dumps({
            "action_status": int(wrapped.status),
            "measured_displacement_m": round(displacement, 3),
            "measured_yaw_change_deg": round(yaw_change, 1),
            "max_cmd_vx": round(node.max_cmd[0], 3),
            "max_cmd_vy": round(node.max_cmd[1], 3),
            "max_cmd_wz": round(node.max_cmd[2], 3),
            "last_distance_remaining": None if node.last_feedback is None else round(node.last_feedback, 3),
        }, sort_keys=True))
        if wrapped.status != 4:
            raise SystemExit(f"GOAL FAILED: action status {wrapped.status}")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
