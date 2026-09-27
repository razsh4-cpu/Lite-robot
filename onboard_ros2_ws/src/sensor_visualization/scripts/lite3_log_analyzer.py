#!/usr/bin/env python3
"""Summarize one JSONL control experiment without contacting the robot."""

import argparse
import json
import math
from pathlib import Path


def analyze(path):
    rows = []
    with path.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON on line {number}: {error}") from error
    if not rows:
        raise ValueError("log is empty")
    commands = [row.get("cmd_vel") for row in rows if row.get("cmd_vel")]
    odom = [row.get("odom") for row in rows if row.get("odom")]
    reasons = sorted({row.get("control_reason") for row in rows if row.get("control_reason")})
    result = {
        "path": str(path),
        "samples": len(rows),
        "duration_s": rows[-1]["monotonic_time"] - rows[0]["monotonic_time"],
        "max_abs_linear_x": max((abs(c["linear_x"]) for c in commands), default=0.0),
        "max_abs_angular_z": max((abs(c["angular_z"]) for c in commands), default=0.0),
        "max_abs_normalized_forward": max(
            (abs(row["normalized_forward"]) for row in rows
             if row.get("normalized_forward") is not None), default=0.0),
        "max_abs_normalized_yaw": max(
            (abs(row["normalized_yaw"]) for row in rows
             if row.get("normalized_yaw") is not None), default=0.0),
        "enabled_samples": sum(bool(row.get("control_enabled")) for row in rows),
        "deadman_samples": sum(bool(row.get("deadman")) for row in rows),
        "telemetry_stale_samples": sum(
            row.get("robot_state_fresh") is False for row in rows),
        "control_reasons": reasons,
        "odom_available": bool(odom),
    }
    if len(odom) >= 2:
        dx = odom[-1]["x"] - odom[0]["x"]
        dy = odom[-1]["y"] - odom[0]["y"]
        result.update({"odom_dx_m": dx, "odom_dy_m": dy,
                       "odom_displacement_m": math.hypot(dx, dy)})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = analyze(args.log)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
