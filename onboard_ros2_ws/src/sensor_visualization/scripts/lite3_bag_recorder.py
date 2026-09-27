#!/usr/bin/env python3
"""Signal-clean wrapper around rosbag2 for the fixed Lite3 topic set."""

import argparse
import signal
import subprocess


TOPICS = [
    "/joy", "/cmd_vel", "/lite3/cmd_vel_deadman",
    "/lite3/manual_forward_normalized", "/lite3/manual_yaw_normalized",
    "/lite3/manual_axis_deadman", "/lite3/control_enabled",
    "/lite3/control_reason", "/lite3/active_command_source",
    "/lite3/select_command_source", "/lite3/robot_basic_state",
    "/lite3/battery_percent", "/lite3/robot_state_fresh", "/odom", "/scan",
    "/tf", "/tf_static",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    process = subprocess.Popen([
        "ros2", "bag", "record", "--storage", "sqlite3",
        "--max-cache-size", "10485760", "-o", args.output, *TOPICS,
    ])

    def forward_signal(signum, _frame):
        if process.poll() is None:
            process.send_signal(signum)

    signal.signal(signal.SIGINT, forward_signal)
    signal.signal(signal.SIGTERM, forward_signal)
    result = process.wait()
    return 0 if result in (0, 2, -signal.SIGINT, -signal.SIGTERM) else result


if __name__ == "__main__":
    raise SystemExit(main())
