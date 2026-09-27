import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).parents[1]
STARTUP = ROOT / "scripts" / "lite3_xbox_startup.sh"
SUPERVISOR = ROOT / "scripts" / "lite3_xbox_reconnect_supervisor.py"
ROBOT_LAUNCH = ROOT / "launch" / "lite3_high_level_runtime.launch.py"
XBOX_LAUNCH = ROOT / "launch" / "lite3_local_xbox_input.launch.py"


def executable(path: Path, body: str):
    path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    path.chmod(0o755)


def run_startup(tmp_path: Path, validator_result: int):
    bin_dir = tmp_path / "bin"
    state_dir = tmp_path / "state"
    bin_dir.mkdir()
    state_dir.mkdir()
    log = tmp_path / "calls"
    validator = tmp_path / "validator"
    executable(validator, f"exit {validator_result}\n")
    executable(
        bin_dir / "bluetoothctl",
        "if [[ \"${1:-}\" == info ]]; then echo 'Connected: yes'; exit 0; fi\n"
        f"echo bluetooth >>'{log}'\nexit 0\n")
    executable(
        bin_dir / "systemctl",
        f"echo systemctl \"$@\" >>'{log}'\n"
        "[[ \"${1:-}\" == is-active ]] && exit 1\nexit 0\n")
    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}:{env['PATH']}",
        "LITE3_STATE_DIR": str(state_dir),
        "LITE3_XBOX_VALIDATOR": str(validator),
        "LITE3_XBOX_SUPERVISOR": str(SUPERVISOR),
        "LITE3_XBOX_SUPERVISE": "false",
        "LITE3_XBOX_MAX_ATTEMPTS": "2",
        "LITE3_XBOX_RETRY_SECONDS": "0",
    })
    result = subprocess.run(
        ["bash", str(STARTUP)], env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    calls = log.read_text(encoding="utf-8") if log.exists() else ""
    return result, state_dir, calls


def test_xbox_available_selects_safe_local_runtime(tmp_path):
    result, state, calls = run_startup(tmp_path, 0)
    assert result.returncode == 0
    assert (state / "MANUAL_CONTROL_AVAILABLE").read_text().strip() == "true"
    assert "systemctl start lite3-high-level-runtime.service" in calls
    assert "systemctl start lite3-high-level-xbox.service" in calls


def test_xbox_unavailable_finishes_without_failing_system(tmp_path):
    result, state, calls = run_startup(tmp_path, 1)
    assert result.returncode == 0
    assert (state / "MANUAL_CONTROL_AVAILABLE").read_text().strip() == "false"
    assert (state / "COMMAND_SOURCE").read_text().strip() == "NONE"
    assert calls.count("bluetooth") == 2
    assert "systemctl start lite3-high-level-runtime.service" in calls
    assert "systemctl start lite3-high-level-xbox.service" not in calls


def test_persistent_robot_launch_owns_transport_without_joystick_node():
    text = ROBOT_LAUNCH.read_text(encoding="utf-8")
    assert 'executable="xbox_lite3_motion_host_bridge"' in text
    assert '"heartbeat_enabled": True' in text
    assert '"require_deadman": False' in text
    assert "game_controller_node" not in text


def test_optional_xbox_launch_owns_input_without_robot_transport():
    text = XBOX_LAUNCH.read_text(encoding="utf-8")
    assert 'executable="game_controller_node"' in text
    assert "xbox_lite3_motion_host_bridge" not in text


def test_xbox_input_acquires_lease_before_input_launch_only():
    text = (ROOT / "scripts" / "lite3_high_level_xbox_runtime.sh").read_text()
    assert text.index('flock -n 9') < text.index('ros2 launch')
    assert text.index('"$validator" "$joystick"') < text.index('ros2 launch')
    assert "lite3_local_xbox_input.launch.py" in text
    assert "lite3_high_level_runtime.launch.py" not in text


def test_core_services_do_not_depend_on_xbox_or_laptop():
    systemd = ROOT / "systemd"
    for name in (
        "lite3-high-level-runtime.service",
        "lite3-lidar.service",
        "lite3-localization.service",
    ):
        text = (systemd / name).read_text(encoding="utf-8")
        assert "WantedBy=multi-user.target" in text
        assert "lite3-xbox.service" not in text
        assert "rviz2" not in text.lower()


def test_realsense_is_preserved_but_on_demand():
    text = (ROOT / "systemd" / "lite3-realsense.service").read_text()
    assert "realsense2_camera rs_launch.py" in text
    assert "pointcloud.enable:=true" in text
    assert "WantedBy=multi-user.target" not in text


def test_headless_admin_preserves_robot_services_and_has_rollback():
    text = (ROOT / "scripts" / "lite3_headless_admin.sh").read_text()
    assert "systemctl set-default multi-user.target" in text
    assert "systemctl set-default graphical.target" in text
    assert "systemctl disable lite3-realsense.service" in text
    assert "systemctl start graphical.target" in text
    assert "systemctl isolate multi-user.target" in text
    assert "systemctl stop lite3-high-level-runtime.service" not in text
    assert "systemctl stop lite3-lidar.service" not in text


def test_health_monitor_is_continuous_and_read_only():
    unit = (ROOT / "systemd" / "lite3-system-health.service").read_text()
    script = (ROOT / "scripts" / "lite3_system_health.sh").read_text()
    assert "Type=simple" in unit
    assert "Restart=always" in unit
    assert "while [[ \"$stopping\" == false ]]" in script
    assert "topic_fresh /odom" in script
    assert "topic_fresh /scan" in script
    assert 'ros2 run tf2_ros tf2_echo "$1" "$2"' in script
    assert "tf_available odom base_link" in script
    assert "tf_available map base_link" in script
    assert "lifecycle_active /map_server" in script
    assert "lifecycle_active /amcl" in script
    assert "cmd_vel" not in script
    assert "ros2 topic pub" not in script


def test_localization_has_verified_automatic_initial_pose():
    launch = ROOT.parent / "lite3_state_estimation" / "launch" / "day1_localization.launch.py"
    text = launch.read_text(encoding="utf-8")
    assert 'pose_file = LaunchConfiguration("pose_file")' in text
    assert 'default_value="0.80"' in text


def test_laptop_rviz_shows_autonomy_state_without_odom_clutter():
    config = ROOT.parents[2] / "laptop_visualization" / "lite3_remote_lidar.rviz"
    text = config.read_text(encoding="utf-8")
    odom = text.split("Class: rviz_default_plugins/Odometry", 1)[1]
    odom = odom.split("Class: rviz_default_plugins/Map", 1)[0]
    assert "Enabled: false" in odom
    assert "Value: /scan" in text
    assert "Value: /map" in text
    assert "Value: /localization/pose" in text
    assert "Fixed Frame: map" in text
