from pathlib import Path
import importlib.util
import sys

import pytest
import yaml

ROOT = Path(__file__).parents[1]

def load_module():
    path = ROOT / "scripts/lite3_mission_manager.py"
    spec = importlib.util.spec_from_file_location("lite3_mission_manager", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def test_placeholder_names_exist_but_are_not_configured_for_execution():
    data = yaml.safe_load((ROOT / "config/named_locations.yaml").read_text())
    assert data["frame_id"] == "map"
    assert set(data["locations"]) == {"gate", "entrance", "parking"}
    assert all(goal["configured"] is False for goal in data["locations"].values())
    assert all(goal["x"] is None and goal["y"] is None and goal["yaw"] is None
               for goal in data["locations"].values())

def test_registry_accepts_only_finite_configured_map_poses(tmp_path):
    module = load_module()
    good = tmp_path / "good.yaml"
    good.write_text("map: Home_Map\nframe_id: map\nlocations:\n  gate: {configured: true, x: 1.0, y: 2.0, yaw: 0.5}\n")
    assert module.load_registry(good)["locations"]["gate"]["x"] == 1.0
    bad = tmp_path / "bad.yaml"
    bad.write_text("map: Home_Map\nframe_id: map\nlocations:\n  gate: {configured: true, x: null, y: 2.0, yaw: 0.5}\n")
    with pytest.raises(ValueError):
        module.load_registry(bad)

def test_manager_has_no_navigation_or_motion_execution_path():
    text = (ROOT / "scripts/lite3_mission_manager.py").read_text()
    for forbidden in ("NavigateToPose", "/cmd_vel", "ActionClient", "COMMAND_SOURCE", "systemctl"):
        assert forbidden not in text
