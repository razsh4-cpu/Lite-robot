#!/usr/bin/env python3
"""Inactive Day-3 named-location registry; never sends a navigation goal."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import yaml

DEFAULT_CONFIG = Path(
    "/home/abx/Desktop/robotdog_ws/install/sensor_visualization/"
    "share/sensor_visualization/config/named_locations.yaml")


def load_registry(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("frame_id") != "map":
        raise ValueError("registry must use frame_id: map")
    locations = data.get("locations")
    if not isinstance(locations, dict) or not locations:
        raise ValueError("registry has no named locations")
    for name, goal in locations.items():
        if not isinstance(name, str) or not name or not isinstance(goal, dict):
            raise ValueError("invalid named location")
        configured = goal.get("configured") is True
        values = (goal.get("x"), goal.get("y"), goal.get("yaw"))
        if configured and not all(
                isinstance(value, (int, float)) and math.isfinite(float(value))
                for value in values):
            raise ValueError(f"configured location {name} has invalid pose")
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Day-3 named-goal registry (execution intentionally disabled)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("name")
    sub.add_parser("validate")
    args = parser.parse_args()
    try:
        registry = load_registry(args.config)
        locations = registry["locations"]
        if args.command == "list":
            print(json.dumps({
                "map": registry.get("map"),
                "locations": [
                    {"name": name, "configured": goal.get("configured") is True}
                    for name, goal in locations.items()]}, sort_keys=True))
        elif args.command == "show":
            if args.name not in locations:
                raise ValueError(f"unknown location: {args.name}")
            print(json.dumps({"name": args.name, **locations[args.name]}, sort_keys=True))
        else:
            print("MISSION REGISTRY VALID — EXECUTION DISABLED")
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"MISSION REGISTRY INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
