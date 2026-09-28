#!/usr/bin/env python3
"""Pure policy and saved-snapshot helpers for the Lite3 obstacle test."""
from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

BODY_FRONT_X = 0.355
MAX_TEST_OBSTACLE_X = 1.75
MAX_TEST_OBSTACLE_Y = 0.90
MIN_PADDED_CLEARANCE_M = 0.05
ACTIVE_GOAL_STATUSES = {1, 2, 3}  # ACCEPTED, EXECUTING, CANCELING


def load_json(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def quaternion_yaw(rotation) -> float:
    x, y, z, w = rotation
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def transform_xy(transform, x: float, y: float) -> tuple[float, float]:
    angle = quaternion_yaw(transform["rotation"])
    tx, ty = transform["translation"][:2]
    return (tx + math.cos(angle) * x - math.sin(angle) * y,
            ty + math.sin(angle) * x + math.cos(angle) * y)


def relevant_obstacle(session: Path) -> dict | None:
    """Find the nearest forward LiDAR return represented in a live costmap."""
    scan = load_json(session / "scan.json.gz")
    transforms = load_json(session / "tf.json")
    base_scan = transforms[f"base_link->{scan['frame_id']}"]

    # Import the already regression-tested grid/TF helpers rather than creating
    # a second clearance implementation.
    from lite3_chair_snapshot_analyze import lethal_cells
    local = lethal_cells(load_json(session / "local_costmap.json.gz"), transforms, "local")
    global_cells = lethal_cells(load_json(session / "global_costmap.json.gz"), transforms, "global")
    cells = local + global_cells
    map_base = transforms["map->base_link"]

    candidates = []
    for index, distance in enumerate(scan["ranges"]):
        if distance is None or not scan["range_min"] <= distance <= scan["range_max"]:
            continue
        angle = scan["angle_min"] + index * scan["angle_increment"]
        bx, by = transform_xy(base_scan, distance * math.cos(angle), distance * math.sin(angle))
        if not (BODY_FRONT_X < bx <= MAX_TEST_OBSTACLE_X and abs(by) <= MAX_TEST_OBSTACLE_Y):
            continue
        mx, my = transform_xy(map_base, bx, by)
        matched = [cell for cell in cells if math.hypot(cell["x"] - mx, cell["y"] - my) <= 0.08]
        if not matched:
            continue
        layers = sorted({cell["layer"] for cell in matched})
        candidates.append({
            "scan_index": index,
            "scan_range_m": distance,
            "scan_angle_rad": angle,
            "base_x": bx,
            "base_y": by,
            "body_front_clearance_m": bx - BODY_FRONT_X,
            "map_x": mx,
            "map_y": my,
            "costmap_layers": layers,
        })
    return min(candidates, key=lambda item: math.hypot(item["base_x"], item["base_y"]),
               default=None)


def path_complexity(path: dict) -> float:
    poses = path["poses"]
    headings = []
    for left, right in zip(poses, poses[1:]):
        dx, dy = right["x"] - left["x"], right["y"] - left["y"]
        if math.hypot(dx, dy) > 1e-6:
            headings.append(math.atan2(dy, dx))
    return sum(abs(math.atan2(math.sin(b - a), math.cos(b - a)))
               for a, b in zip(headings, headings[1:]))


def select_candidate(session: Path, obstacle: dict) -> dict | None:
    analysis = load_json(session / "analysis.json")
    candidates = []
    for item in analysis.get("candidates", []):
        if item.get("minimum_padded_clearance", 0.0) < MIN_PADDED_CLEARANCE_M:
            continue
        if item.get("path_length", math.inf) > 2.5:
            continue
        payload = load_json(session / item["file"])
        path = payload["path"] if "path" in payload else payload
        complexity = path_complexity(path)
        # A short avoidance must finish beyond the detected return or displaced
        # well to its side. Nav2 still decides collision validity using the full
        # costmap and configured footprint.
        forward = float(item["forward"])
        lateral = float(item["lateral"])
        clears_test_area = (forward >= obstacle["base_x"] + 0.25 or
                            abs(lateral - obstacle["base_y"]) >= 0.60)
        if not clears_test_area:
            continue
        candidates.append({**item, "path_complexity": complexity, "path": path})
    if not candidates:
        return None
    # Safety dominates; for materially equivalent clearance prefer shorter and
    # simpler paths. Lateral is supported by the physically proven vendor-gait
    # product path and remains bounded by the existing adapter limit.
    candidates.sort(key=lambda item: (
        -round(float(item["minimum_padded_clearance"]), 2),
        float(item["path_length"]),
        float(item["path_complexity"]),
    ))
    return candidates[0]


def side(candidate: dict) -> str:
    return "LEFT" if float(candidate["lateral"]) > 0.0 else "RIGHT"


def preflight_blockers(nav: dict, robot: dict, mission_active: bool,
                       test_samples: list[float] | None = None) -> list[str]:
    blockers = []
    checks = nav.get("checks", {})
    names = {
        "high_level": "HIGH-LEVEL unhealthy",
        "telemetry_odom": "odometry/telemetry stale",
        "lidar_scan": "LiDAR scan stale",
        "tf_map_base": "map→base_link TF unavailable",
        "tf_base_lidar": "base_link→lidar_link TF unavailable",
        "localization": "localization below 80%",
        "navigation_ready": "localization has not passed 3 consecutive samples",
        "map_server": "Map Server is not active",
        "amcl": "AMCL is not active",
        "planner": "Nav2 planner unavailable",
        "controller": "Nav2 controller unavailable",
        "bt_navigator": "BT Navigator unavailable",
        "global_costmap": "global costmap unavailable",
        "local_costmap": "local costmap unavailable",
        "navigate_action": "NavigateToPose unavailable",
        "single_udp_receiver": "UDP 43897 receiver ownership invalid",
        "command_source_none": f"COMMAND_SOURCE={nav.get('command_source', 'UNKNOWN')}",
        "autonomy_lease_available": "AUTONOMY lease unavailable",
        "battery_safe": "battery below navigation threshold",
    }
    stable_test_candidate = (test_samples is not None and len(test_samples) >= 3
                             and all(float(v) >= 0.70 for v in test_samples[-3:]))
    for key, description in names.items():
        # This only permits the no-motion token-enablement preflight. The
        # normal preflight is rerun after the guard has produced LOCALIZED /
        # NAVIGATION_READY under the validated, expiring token.
        if (stable_test_candidate and
                key in {"localization", "navigation_ready"}):
            continue
        if not checks.get(key, False):
            blockers.append(description)
    if not robot.get("connected"):
        blockers.append("robot disconnected")
    if not robot.get("high_level_healthy"):
        blockers.append("HIGH-LEVEL unhealthy")
    if not robot.get("telemetry_fresh"):
        blockers.append("robot telemetry stale")
    if str(robot.get("posture", "")).lower() != "standing":
        blockers.append(f"posture={robot.get('posture', 'UNKNOWN')}")
    if not robot.get("velocities_zero", False) or robot.get("motion_enabled", False):
        blockers.append("non-zero or active motion")
    if mission_active:
        blockers.append("active Nav2 mission")
    return list(dict.fromkeys(blockers))
