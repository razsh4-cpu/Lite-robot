from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).parents[1]
MANAGER = ROOT / "onboard_ros2_ws/src/sensor_visualization/scripts/lite3_map_manager.py"
CLI = ROOT / "operator/lite3_map_cli.py"
LAUNCH = ROOT / "onboard_ros2_ws/src/lite3_state_estimation/launch/day1_localization.launch.py"
GUARD = ROOT / "onboard_ros2_ws/src/lite3_state_estimation/lite3_state_estimation/localization_guard.py"
RVIZ = ROOT / "laptop_visualization/lite3_remote_lidar.rviz"


def load_manager():
    spec = importlib.util.spec_from_file_location("manager", MANAGER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_is_eighty_percent_and_pose_is_per_map():
    assert 'default_value="0.80"' in LAUNCH.read_text()
    assert 'self.declare_parameter("minimum_match_fraction", 0.80)' in GUARD.read_text()
    assert 'pose_file = LaunchConfiguration("pose_file")' in LAUNCH.read_text()


def test_map_name_and_map_file_validation(tmp_path):
    manager = load_manager()
    assert manager.NAME_RE.fullmatch("warehouse_01")
    assert not manager.NAME_RE.fullmatch("../bad")
    directory = tmp_path / "map"
    directory.mkdir()
    (directory / "map.pgm").write_bytes(b"P5\n8 1\n255\n" + b"\x00" * 8)
    (directory / "map.yaml").write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n")
    assert manager.validate_map(directory) == (True, "valid")


def test_no_motion_commands_and_mutual_exclusion_are_explicit():
    text = MANAGER.read_text()
    forbidden = ("/cmd_vel", "StandingUp", "MODE_MOVE", "CONTROL_MANUAL")
    assert not any(token in text for token in forbidden)
    assert 'systemctl("stop", "lite3-localization.service")' in text
    assert 'systemctl("stop", "lite3-mapping.service")' in text
    assert '"conflict": mapping and localization' in text


def test_cli_supports_number_or_name_and_single_rviz_unit():
    text = CLI.read_text()
    assert 'requested.isdigit()' in text
    assert 'Map name: ' in text
    assert 'systemctl", "--user", "stop", RVIZ_UNIT' in text
    assert 'systemd-run", "--user", "--unit=lite3-rviz-session"' in text


def test_rviz_hides_tf_clutter_and_uses_live_pose():
    text = RVIZ.read_text()
    tf_section = text.split("Class: rviz_default_plugins/TF", 1)[1].split("Class:", 1)[0]
    assert "Enabled: false" in tf_section
    assert "Value: /localization/pose" in text
    assert "Fixed Frame: map" in text


def test_accept_rejects_low_confidence_and_overwrite(tmp_path, monkeypatch):
    import pytest
    from types import SimpleNamespace
    manager = load_manager()
    pending = tmp_path / "pending"
    maps = tmp_path / "maps"
    pending.mkdir(); maps.mkdir()
    (pending / "map.pgm").write_bytes(b"P5\n8 1\n255\n" + b"\x00" * 8)
    (pending / "map.yaml").write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n")
    (pending / "validation.json").write_text(json.dumps({"state": "UNLOCALIZED", "match_fraction": 0.79}))
    monkeypatch.setattr(manager, "PENDING", pending)
    monkeypatch.setattr(manager, "MAPS", maps)
    with pytest.raises(RuntimeError, match="below 80%"):
        manager.cmd_accept(SimpleNamespace(name="warehouse_01"))
    (maps / "warehouse_01").mkdir()
    (pending / "validation.json").write_text(json.dumps({"state": "LOCALIZED", "match_fraction": 0.90}))
    with pytest.raises(RuntimeError, match="already exists"):
        manager.cmd_accept(SimpleNamespace(name="warehouse_01"))



def load_cli():
    spec = importlib.util.spec_from_file_location("map_cli", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fresh_shell_wrapper_sources_jazzy_and_workspace():
    text = CLI.read_text()
    assert "/opt/ros/jazzy/setup.bash" in text
    assert "/home/raz/ros-robot-cc/install/setup.bash" in text
    assert "ensure_ros_environment()" in text


def test_offline_ssh_is_fast_and_human_readable(monkeypatch, capsys):
    from types import SimpleNamespace
    cli = load_cli()
    monkeypatch.setattr(cli, "execute", lambda *_a, **_k: SimpleNamespace(
        returncode=255, stdout="ssh: connect to host 192.168.2.32 timed out"))
    code, data = cli.remote("status")
    assert code == 255
    assert data["error"] == "MINI-PC OFFLINE"
    monkeypatch.setattr(cli, "remote", lambda *_a, **_k: (255, data))
    assert cli.status_command() == 255
    assert capsys.readouterr().out.strip() == "MINI-PC OFFLINE"


def test_select_refuses_offline_robot_before_side_effects(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace
    manager = load_manager()
    maps = tmp_path / "maps"
    home = maps / "Home_Map"
    home.mkdir(parents=True)
    (home / "map.pgm").write_bytes(b"P5\n8 1\n255\n" + b"\x00" * 8)
    (home / "map.yaml").write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n")
    monkeypatch.setattr(manager, "MAPS", maps)
    monkeypatch.setattr(manager, "preflight", lambda: {
        "robot": False, "lidar": True, "odom": False,
        "tf_odom_base": False, "tf_base_lidar": True})
    monkeypatch.setattr(manager, "systemctl", lambda *_a, **_k: (_ for _ in ()).throw(
        AssertionError("offline selection must not mutate services")))
    assert manager.cmd_select(SimpleNamespace(name="Home_Map")) == 2
    assert json.loads(capsys.readouterr().out)["error"] == "ROBOT OFFLINE"


def test_cancel_restores_localization_nonblocking():
    text = MANAGER.read_text()
    assert 'systemctl("restart", "lite3-localization.service", no_block=True)' in text
    assert "shutil.rmtree(PENDING)" in text


def test_acceptance_chain_is_read_only_and_complete():
    text = MANAGER.read_text()
    for token in ("lite3-high-level-runtime.service", "heartbeat_enabled", 'topic_fresh("/odom"',
                  'topic_fresh("/scan"', 'tf_fresh("odom", "base_link"',
                  'tf_fresh("base_link", "lidar_link"', 'selected_map() != "Home_Map"',
                  'service_active("lite3-localization.service")', 'tf_fresh("map", "base_link"',
                  'float(status.get("match_fraction", 0.0)) < 0.80'):
        assert token in text
    forbidden = ("/cmd_vel", "StandingUp", "MODE_MOVE", "CONTROL_MANUAL")
    function = text.split("def cmd_acceptance", 1)[1].split("def main", 1)[0]
    assert not any(token in function for token in forbidden)


def test_network_gate_does_not_require_powered_robot_and_dds_is_explicit():
    root = ROOT / "onboard_ros2_ws/src/sensor_visualization"
    gate = (root / "scripts/lite3_ros_network_ready.sh").read_text()
    assert "no stable routable interface" in gate
    assert "robot route not yet available" in gate
    assert "exit 1" not in gate.split("robot route not yet available", 1)[0]
    for name in ("lite3-high-level-runtime.service", "lite3-lidar.service",
                 "lite3-localization.service", "lite3-mapping.service"):
        unit = (root / "systemd" / name).read_text()
        assert "Environment=ROS_DOMAIN_ID=0" in unit
        assert "Environment=ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET" in unit



def test_successful_accept_preserves_home_map_and_separates_metadata(tmp_path, monkeypatch):
    from types import SimpleNamespace
    manager = load_manager()
    maps = tmp_path / "maps"
    pending = tmp_path / "pending"
    config = tmp_path / "config"
    state = tmp_path / "state"
    home = maps / "Home_Map"
    home.mkdir(parents=True)
    pending.mkdir(parents=True)
    config.mkdir()
    state.mkdir()
    for directory in (home, pending):
        (directory / "map.pgm").write_bytes(b"P5\n8 1\n255\n" + b"\x00" * 8)
        (directory / "map.yaml").write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n")
    home_pose = '{"x": 1, "y": 2, "yaw": 3}\n'
    (home / "initial_pose.json").write_text(home_pose)
    (home / "metadata.json").write_text('{"name":"Home_Map","validated":true}\n')
    (pending / "initial_pose.json").write_text('{"x": 4, "y": 5, "yaw": 6}\n')
    (pending / "validation.json").write_text(json.dumps({
        "state": "LOCALIZED", "match_fraction": 0.85}))
    monkeypatch.setattr(manager, "MAPS", maps)
    monkeypatch.setattr(manager, "PENDING", pending)
    monkeypatch.setattr(manager, "DEFAULT", config / "default_map")
    monkeypatch.setattr(manager, "ACTIVE", config / "active_map_yaml")
    monkeypatch.setattr(manager, "MODE", state / "MAP_MODE")
    monkeypatch.setattr(manager, "systemctl", lambda *_a, **_k: None)
    assert manager.cmd_accept(SimpleNamespace(name="warehouse_01")) == 0
    assert (home / "initial_pose.json").read_text() == home_pose
    assert (maps / "warehouse_01" / "initial_pose.json").is_file()
    assert json.loads((maps / "warehouse_01" / "metadata.json").read_text())["minimum_match_fraction"] == 0.80
    assert (config / "default_map").read_text().strip() == "warehouse_01"
