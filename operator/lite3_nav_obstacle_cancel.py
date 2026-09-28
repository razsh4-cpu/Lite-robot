#!/usr/bin/env python3
"""Cancel every active NavigateToPose goal. Zero/release is owned by AUTONOMY."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import rclpy
from action_msgs.srv import CancelGoal
from rclpy.node import Node


def main():
    rclpy.init()
    node = Node("lite3_obstacle_test_cancel")
    try:
        client = node.create_client(CancelGoal, "/navigate_to_pose/_action/cancel_goal")
        if not client.wait_for_service(timeout_sec=3.0):
            print("NAV2 CANCEL SERVICE UNAVAILABLE")
            return 2
        request = CancelGoal.Request()  # zero UUID and zero stamp means cancel all goals
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=4.0)
        if future.result() is None:
            print("NAV2 CANCEL FAILED")
            return 3
        print(f"NAV2 CANCEL REQUESTED: {len(future.result().goals_canceling)} goal(s)")
        return 0
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
