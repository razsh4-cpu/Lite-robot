#!/usr/bin/env python3
"""One bounded in-place relocalization turn through the existing C2 lease."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
from pathlib import Path
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool

STATE = Path("/run/lite3-control/COMMAND_SOURCE")
PREFIX = "/c2/robot_01/laptop_xbox"

def owner():
    try:
        return STATE.read_text().strip()
    except OSError:
        return "UNKNOWN"

def main():
    if owner() != "NONE":
        raise SystemExit(f"TURN BLOCKED: COMMAND_SOURCE={owner()}")
    rclpy.init()
    node = Node("lite3_c2_relocalize_once")
    joy_pub = node.create_publisher(Joy, PREFIX + "/joy", 10)
    hb_pub = node.create_publisher(Bool, PREFIX + "/heartbeat", 10)
    req_pub = node.create_publisher(Bool, PREFIX + "/request", 10)
    neutral = Joy(axes=[0.0] * 8, buttons=[0] * 15)
    authorize = Joy(axes=[0.0] * 8, buttons=[0] * 10 + [1] + [0] * 4)
    turn = Joy(axes=[0.0, 0.0, 0.10, 0.0, 0.0, 0.0, 0.0, 0.0],
               buttons=[0] * 15)

    def publish(joy, enabled=True):
        req_pub.publish(Bool(data=enabled))
        hb_pub.publish(Bool(data=enabled))
        joy_pub.publish(joy)
        rclpy.spin_once(node, timeout_sec=0.0)

    try:
        deadline = time.monotonic() + 6.0
        while time.monotonic() < deadline and owner() != "LAPTOP_XBOX":
            publish(neutral)
            time.sleep(0.05)
        if owner() != "LAPTOP_XBOX":
            raise SystemExit("TURN BLOCKED: C2 lease was not acquired")
        for _ in range(12):
            publish(neutral); time.sleep(0.05)
        for _ in range(5):
            publish(authorize); time.sleep(0.05)
        for _ in range(20):
            publish(neutral); time.sleep(0.05)
        for _ in range(20):
            publish(turn); time.sleep(0.05)
        for _ in range(20):
            publish(neutral); time.sleep(0.05)
        print("BOUNDED TURN COMPLETE: yaw=+0.10 for 1.00s")
    finally:
        for _ in range(5):
            publish(neutral, enabled=False); time.sleep(0.05)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
