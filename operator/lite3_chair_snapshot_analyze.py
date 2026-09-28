#!/usr/bin/env python3
"""Offline clearance/source analysis for a saved Lite3 chair dry-run package."""

from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path

RAW_HALF = (0.305, 0.185)
PADDED_HALF = (0.355, 0.235)


def load(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tf_yaw(rotation):
    x, y, z, w = rotation
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def apply(transform, x, y):
    angle = tf_yaw(transform["rotation"])
    tx, ty = transform["translation"][:2]
    return tx + math.cos(angle) * x - math.sin(angle) * y, ty + math.sin(angle) * x + math.cos(angle) * y


def compose(first, second):
    """Return first(target<-mid) composed with second(mid<-source), in 2-D."""
    sx, sy = apply(first, second["translation"][0], second["translation"][1])
    angle = tf_yaw(first["rotation"]) + tf_yaw(second["rotation"])
    return {"translation": [sx, sy, first["translation"][2] + second["translation"][2]],
            "rotation": [0.0, 0.0, math.sin(angle / 2), math.cos(angle / 2)]}


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segment_distance(point, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    denominator = vx * vx + vy * vy
    factor = 0.0 if denominator == 0 else max(0.0, min(
        1.0, ((point[0] - a[0]) * vx + (point[1] - a[1]) * vy) / denominator))
    return math.hypot(point[0] - a[0] - factor * vx,
                      point[1] - a[1] - factor * vy)


def inside(point, polygon):
    signs = [cross(polygon[index], polygon[(index + 1) % len(polygon)], point)
             for index in range(len(polygon))]
    return all(value >= -1e-9 for value in signs) or all(value <= 1e-9 for value in signs)


def polygon_distance(left, right):
    if any(inside(point, right) for point in left) or any(inside(point, left) for point in right):
        return 0.0
    return min(
        [segment_distance(point, right[index], right[(index + 1) % len(right)])
         for point in left for index in range(len(right))]
        + [segment_distance(point, left[index], left[(index + 1) % len(left)])
           for point in right for index in range(len(left))])


def rectangle(x, y, angle, half):
    cosine, sine = math.cos(angle), math.sin(angle)
    return [(x + cosine * dx - sine * dy, y + sine * dx + cosine * dy)
            for dx, dy in ((half[0], half[1]), (half[0], -half[1]),
                           (-half[0], -half[1]), (-half[0], half[1]))]


def grid_transform(grid, transforms):
    if grid["frame_id"] == "map":
        return {"translation": [0, 0, 0], "rotation": [0, 0, 0, 1]}
    if grid["frame_id"] == "odom":
        return transforms["map->odom"]
    raise ValueError(f"unsupported grid frame {grid['frame_id']}")


def lethal_cells(grid, transforms, layer):
    transform = grid_transform(grid, transforms)
    origin, resolution = grid["origin"], grid["resolution"]
    cells = []
    for row in range(grid["height"]):
        for column in range(grid["width"]):
            if grid["data"][row * grid["width"] + column] != 100:
                continue
            polygon = [apply(transform,
                origin["x"] + (column + dx) * resolution,
                origin["y"] + (row + dy) * resolution)
                for dx, dy in ((0, 0), (1, 0), (1, 1), (0, 1))]
            cells.append({"layer": layer, "row": row, "column": column,
                          "polygon": polygon,
                          "x": sum(point[0] for point in polygon) / 4,
                          "y": sum(point[1] for point in polygon) / 4})
    return cells


def scan_points(scan, transforms):
    map_scan = compose(transforms["map->base_link"], transforms["base_link->" + scan["frame_id"]])
    points = []
    for index, distance in enumerate(scan["ranges"]):
        if distance is None or not scan["range_min"] <= distance <= scan["range_max"]:
            continue
        angle = scan["angle_min"] + index * scan["angle_increment"]
        x, y = apply(map_scan, distance * math.cos(angle), distance * math.sin(angle))
        points.append((x, y, index, distance, angle))
    return points


def static_value(grid, x, y):
    origin, resolution = grid["origin"], grid["resolution"]
    column = int((x - origin["x"]) / resolution)
    row = int((y - origin["y"]) / resolution)
    return (grid["data"][row * grid["width"] + column]
            if 0 <= column < grid["width"] and 0 <= row < grid["height"] else -1)


def path_tangent_yaw(poses, index, fallback):
    """Return path travel direction even when NavFn leaves pose yaw at zero."""
    current = poses[index]
    before = index - 1
    while before >= 0:
        previous = poses[before]
        if math.hypot(current["x"] - previous["x"],
                      current["y"] - previous["y"]) > 1e-6:
            break
        before -= 1
    after = index + 1
    while after < len(poses):
        following = poses[after]
        if math.hypot(following["x"] - current["x"],
                      following["y"] - current["y"]) > 1e-6:
            break
        after += 1

    if before >= 0 and after < len(poses):
        dx = poses[after]["x"] - poses[before]["x"]
        dy = poses[after]["y"] - poses[before]["y"]
    elif after < len(poses):
        dx = poses[after]["x"] - current["x"]
        dy = poses[after]["y"] - current["y"]
    elif before >= 0:
        dx = current["x"] - poses[before]["x"]
        dy = current["y"] - poses[before]["y"]
    else:
        return fallback
    return math.atan2(dy, dx) if math.hypot(dx, dy) > 1e-6 else fallback


def analyze_candidate(path, cells, scan, static_map, start):
    sequence = []
    path_start = path["poses"][0]
    accumulated_lateral = maximum_lateral = 0.0
    for index, pose in enumerate(path["poses"]):
        moved = math.hypot(pose["x"] - path_start["x"], pose["y"] - path_start["y"])
        x, y, angle = ((start["x"], start["y"], start["yaw"])
                       if moved < 0.025 else
                       (pose["x"], pose["y"],
                        path_tangent_yaw(path["poses"], index, pose["yaw"])))
        polygons = {"raw": rectangle(x, y, angle, RAW_HALF),
                    "padded": rectangle(x, y, angle, PADDED_HALF)}
        nearest = {name: (math.inf, None) for name in polygons}
        for cell in cells:
            if abs(cell["x"] - x) > 1.2 or abs(cell["y"] - y) > 1.2:
                continue
            for name, polygon in polygons.items():
                distance = polygon_distance(polygon, cell["polygon"])
                if distance < nearest[name][0]:
                    nearest[name] = distance, cell
        cell = nearest["padded"][1]
        nearest_scan = min(scan,
            key=lambda point: math.hypot(point[0] - cell["x"], point[1] - cell["y"]),
            default=None) if cell else None
        scan_distance = (math.hypot(nearest_scan[0] - cell["x"], nearest_scan[1] - cell["y"])
                         if nearest_scan else math.inf)
        map_value = static_value(static_map, cell["x"], cell["y"]) if cell else -1
        static, live = map_value >= 65, scan_distance <= 0.08
        source = ("both" if static and live else "static_map" if static else
                  "live_lidar" if live else "stale_or_unknown")
        sequence.append({"index": index, "pose": {"x": x, "y": y, "yaw": angle},
            "raw_clearance": nearest["raw"][0], "padded_clearance": nearest["padded"][0],
            "nearest_obstacle": ({"x": cell["x"], "y": cell["y"], "layer": cell["layer"],
                "row": cell["row"], "column": cell["column"], "source": source,
                "static_map_value": map_value,
                "nearest_scan_distance": None if not math.isfinite(scan_distance) else scan_distance,
                "nearest_scan_index": nearest_scan[2] if nearest_scan else None,
                "nearest_scan_range": nearest_scan[3] if nearest_scan else None,
                "nearest_scan_angle": nearest_scan[4] if nearest_scan else None} if cell else None)})
        if index + 1 < len(path["poses"]):
            following = path["poses"][index + 1]
            dx, dy = following["x"] - pose["x"], following["y"] - pose["y"]
            lateral = -math.sin(angle) * dx + math.cos(angle) * dy
            accumulated_lateral += abs(lateral)
            maximum_lateral = max(maximum_lateral, abs(lateral))
    minimum_raw = min(sequence, key=lambda item: item["raw_clearance"])
    minimum_padded = min(sequence, key=lambda item: item["padded_clearance"])
    near = [item for item in sequence
            if item["padded_clearance"] <= minimum_padded["padded_clearance"] + 0.01]
    return {"minimum_raw_clearance": minimum_raw["raw_clearance"],
            "minimum_raw_index": minimum_raw["index"],
            "minimum_padded_clearance": minimum_padded["padded_clearance"],
            "minimum_padded_index": minimum_padded["index"],
            "minimum_obstacle": minimum_padded["nearest_obstacle"],
            "near_minimum_pose_count": len(near),
            "near_minimum_region": "isolated" if len(near) == 1 else "extended",
            "lateral_required": maximum_lateral > 1e-4,
            "maximum_lateral_step": maximum_lateral,
            "accumulated_absolute_lateral": accumulated_lateral,
            "clearance_sequence": sequence}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("session", type=Path)
    args = parser.parse_args()
    root = args.session.resolve()
    metadata, transforms = load(root / "metadata.json"), load(root / "tf.json")
    scan = load(root / "scan.json.gz")
    static_map = load(root / "static_map.json.gz")
    cells = (lethal_cells(load(root / "global_costmap.json.gz"), transforms, "global")
             + lethal_cells(load(root / "local_costmap.json.gz"), transforms, "local"))
    endpoints = scan_points(scan, transforms)
    analyzed = []
    for candidate in metadata["candidates"]:
        path = load(root / candidate["file"])
        analysis = analyze_candidate(path, cells, endpoints, static_map, metadata["robot_pose"])
        analyzed.append({**candidate, **{key: value for key, value in analysis.items()
                                        if key != "clearance_sequence"}})
        save(root / candidate["file"], {"path": path, "analysis": analysis})
    collision_free = [candidate for candidate in analyzed
                      if candidate["minimum_padded_clearance"] > 0.0]
    non_lateral = [candidate for candidate in collision_free if not candidate["lateral_required"]]
    pool = non_lateral or collision_free
    selected = (max(pool, key=lambda item: (item["minimum_padded_clearance"],
                                             -item["path_length"])) if pool else None)
    result = {"session_id": metadata["session_id"], "candidate_count": len(analyzed),
              "collision_free_count": len(collision_free),
              "non_lateral_collision_free_count": len(non_lateral),
              "selected": selected, "candidates": analyzed}
    save(root / "analysis.json", result)
    if selected:
        selected_data = load(root / selected["file"])
        save(root / "planned_path.json", selected_data)
        save(root / "selected_goal.json", selected_data["path"]["poses"][-1])
    print(json.dumps({"session_id": metadata["session_id"],
                      "candidate_count": len(analyzed),
                      "collision_free_count": len(collision_free),
                      "selected": selected, "analysis": str(root / "analysis.json")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
