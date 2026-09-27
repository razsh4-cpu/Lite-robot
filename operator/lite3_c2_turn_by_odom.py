#!/usr/bin/env python3
"""Bounded C2 in-place turn with /odom closed-loop stopping."""
import os
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
from pathlib import Path
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool

STATE = Path("/run/lite3-control/COMMAND_SOURCE")
PREFIX = "/c2/robot_01/laptop_xbox"
TARGET = math.radians(15.0)

def owner():
    try: return STATE.read_text().strip()
    except OSError: return "UNKNOWN"

def yaw_of(q):
    return math.atan2(2.0 * (q.w*q.z + q.x*q.y), 1.0 - 2.0 * (q.y*q.y + q.z*q.z))

def delta(a, b):
    return math.atan2(math.sin(a-b), math.cos(a-b))

class Turn(Node):
    def __init__(self):
        super().__init__("lite3_c2_turn_by_odom")
        self.yaw = None
        self.create_subscription(Odometry, "/odom", self.on_odom, qos_profile_sensor_data)
        self.joy = self.create_publisher(Joy, PREFIX + "/joy", 10)
        self.hb = self.create_publisher(Bool, PREFIX + "/heartbeat", 10)
        self.req = self.create_publisher(Bool, PREFIX + "/request", 10)
    def on_odom(self, msg): self.yaw = yaw_of(msg.pose.pose.orientation)
    def emit(self, joy, enabled=True):
        self.req.publish(Bool(data=enabled)); self.hb.publish(Bool(data=enabled)); self.joy.publish(joy)
        rclpy.spin_once(self, timeout_sec=0.0)

def main():
    if owner() != "NONE": raise SystemExit(f"TURN BLOCKED: COMMAND_SOURCE={owner()}")
    rclpy.init(); node=Turn()
    neutral=Joy(axes=[0.0]*8, buttons=[0]*15)
    authorize=Joy(axes=[0.0]*8, buttons=[0]*10+[1]+[0]*4)
    turn=Joy(axes=[0.0,0.0,0.20,0.0,0.0,0.0,0.0,0.0], buttons=[0]*15)
    try:
        deadline=time.monotonic()+5.0
        while node.yaw is None and time.monotonic()<deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if node.yaw is None: raise SystemExit("TURN BLOCKED: /odom unavailable")
        while owner() != "LAPTOP_XBOX" and time.monotonic()<deadline:
            node.emit(neutral); time.sleep(0.05)
        if owner() != "LAPTOP_XBOX": raise SystemExit("TURN BLOCKED: lease unavailable")
        for _ in range(12): node.emit(neutral); time.sleep(0.05)
        for _ in range(5): node.emit(authorize); time.sleep(0.05)
        for _ in range(24): node.emit(neutral); time.sleep(0.05)
        start=node.yaw; motion_deadline=time.monotonic()+5.0
        travelled=0.0
        while time.monotonic()<motion_deadline:
            node.emit(turn); time.sleep(0.05)
            travelled=abs(delta(node.yaw, start))
            if travelled >= TARGET: break
        for _ in range(20): node.emit(neutral); time.sleep(0.05)
        print(f"TURN STOPPED: odom_yaw_change_deg={math.degrees(travelled):.2f}")
        if travelled < math.radians(10.0): raise SystemExit("TURN INCOMPLETE: less than 10 degrees")
    finally:
        for _ in range(5): node.emit(neutral, enabled=False); time.sleep(0.05)
        node.destroy_node(); rclpy.shutdown()

if __name__ == "__main__": main()
