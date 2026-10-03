"""Read-only identity check for standard grayscale trinary Nav2 site maps.

Semantics reference: navigation2/jazzy/nav2_map_server/src/map_io.cpp.
Unsupported image/mode is rejected, never guessed or converted on disk.
"""
import math
from pathlib import Path


def map_grid_matches(map_yaml, grid):
    import yaml
    from PIL import Image
    config = yaml.safe_load(Path(map_yaml).read_text())
    if config.get("mode", "trinary") != "trinary" or grid.header.frame_id != "map":
        return False
    image = Path(map_yaml).parent / config["image"]
    with Image.open(image) as img:
        if img.mode != "L" or img.size != (grid.info.width, grid.info.height):
            return False
        pixels = list(img.getdata())
    if not math.isclose(float(config["resolution"]), grid.info.resolution, rel_tol=1e-6):
        return False
    x, y, yaw = map(float, config["origin"])
    origin = grid.info.origin
    q = origin.orientation
    actual_yaw = math.atan2(2 * (q.w*q.z + q.x*q.y), 1 - 2 * (q.y*q.y + q.z*q.z))
    if not all(math.isfinite(v) for v in (x, y, yaw, origin.position.x, origin.position.y, actual_yaw)):
        return False
    if (abs(x - origin.position.x) > 1e-6 or abs(y - origin.position.y) > 1e-6
            or abs(math.atan2(math.sin(yaw-actual_yaw), math.cos(yaw-actual_yaw))) > 1e-6):
        return False
    occupied, free = float(config["occupied_thresh"]), float(config["free_thresh"])
    if not 0 <= free < occupied <= 1:
        return False
    width, height = img.size
    if len(grid.data) != width * height:
        return False
    for gy in range(height):
        for gx in range(width):
            value = pixels[(height - 1 - gy) * width + gx] / 255
            probability = value if config.get("negate", 0) else 1 - value
            expected = 100 if probability >= occupied else (0 if probability <= free else -1)
            if grid.data[gy * width + gx] != expected:
                return False
    return True
