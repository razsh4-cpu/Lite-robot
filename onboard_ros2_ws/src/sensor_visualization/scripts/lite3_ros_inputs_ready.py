#!/usr/bin/env python3
"""Block localization startup until its live ROS inputs and TF exist."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shlex
import sys
import time


def write_startup_state(state, detail=""):
    directory = Path(os.environ.get("LITE3_STATE_DIR", "/run/lite3-control"))
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in (("LOCALIZATION_STARTUP_STATE", state),
                        ("LOCALIZATION_STARTUP_ERROR", detail)):
        path = directory / name
        temporary = path.with_name(f".{path.name}.{os.getpid()}")
        temporary.write_text(str(value).rstrip() + "\n", encoding="utf-8")
        temporary.replace(path)


def ensure_ros_environment():
    if os.environ.get("LITE3_INPUT_GATE_ROS_ENV") == "1":
        return
    command = " ".join(shlex.quote(a) for a in [str(Path(__file__).resolve()), *sys.argv[1:]])
    shell = (
        "source /opt/ros/jazzy/setup.bash && "
        "source /home/abx/ros2_ws/install/setup.bash && "
        "source /home/abx/Desktop/robotdog_ws/install/setup.bash && "
        "export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET && "
        "export FASTDDS_BUILTIN_TRANSPORTS=UDPv4 && "
        "export LITE3_INPUT_GATE_ROS_ENV=1 && exec " + command)
    os.execv("/bin/bash", ["/bin/bash", "-lc", shell])


def main():
    ensure_ros_environment()
    import rclpy
    from nav_msgs.msg import Odometry
    from rclpy.duration import Duration
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan
    from tf2_ros import Buffer, TransformException, TransformListener

    rclpy.init(args=None)
    node = rclpy.create_node("lite3_localization_input_gate")
    seen = {"scan": False, "odom": False}
    node.create_subscription(LaserScan, "/scan", lambda _m: seen.__setitem__("scan", True), qos_profile_sensor_data)
    node.create_subscription(Odometry, "/odom", lambda _m: seen.__setitem__("odom", True), qos_profile_sensor_data)
    tf_buffer = Buffer()
    listener = TransformListener(tf_buffer, node)
    transforms = {"odom_base": False, "base_lidar": False}
    deadline = time.monotonic() + 60.0
    last_stage = None
    write_startup_state("STARTING", "waiting for live ROS inputs")
    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.2)
            for key, parent, child in (("odom_base", "odom", "base_link"),
                                       ("base_lidar", "base_link", "lidar_link")):
                try:
                    tf_buffer.lookup_transform(parent, child, rclpy.time.Time(), timeout=Duration(seconds=0.05))
                    transforms[key] = True
                except TransformException:
                    pass
            if not seen["odom"] or not transforms["odom_base"]:
                current_stage = "WAITING_FOR_ODOM"
            elif not seen["scan"] or not transforms["base_lidar"]:
                current_stage = "WAITING_FOR_SCAN"
            else:
                current_stage = "STARTING"
            if current_stage != last_stage:
                write_startup_state(current_stage, "waiting for fresh inputs and base TF")
                last_stage = current_stage
            if all(seen.values()) and all(transforms.values()):
                print(json.dumps({"ready": True, **seen, **transforms}), flush=True)
                return 0
        print(json.dumps({"ready": False, **seen, **transforms}), flush=True)
        missing = [name for name, ready in {**seen, **transforms}.items() if not ready]
        write_startup_state("STARTUP_FAILED", "input timeout: " + ", ".join(missing))
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
