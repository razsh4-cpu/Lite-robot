"""Relocation tests with stub executables, never live ROS/services."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).parents[2]


def test_localization_uses_external_site_and_workspace(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    site = tmp_path / "maps" / "TestSite"
    site.mkdir(parents=True)
    (site / "map.yaml").write_text("image: map.pgm\n")
    (config / "default_map").write_text("TestSite\n")
    workspace = tmp_path / "workspace"
    package = workspace / "install/lite3_state_estimation/share/lite3_state_estimation"
    package.mkdir(parents=True)
    (workspace / "install/setup.bash").write_text("export FIXTURE_WORKSPACE=loaded\n")
    (package / "package.bash").write_text("export FIXTURE_PACKAGE=loaded\n")
    setup = tmp_path / "ros.bash"
    setup.write_text("export FIXTURE_ROS=loaded\n")
    binary = tmp_path / "bin"
    binary.mkdir()
    ros = binary / "ros2"
    ros.write_text('#!/bin/bash\nprintf "%s\\n" "$FIXTURE_ROS/$FIXTURE_WORKSPACE/$FIXTURE_PACKAGE" "$@"\n')
    ros.chmod(0o755)
    env = dict(os.environ, PATH=f"{binary}:{os.environ['PATH']}",
               LITE3_CONFIG_DIR=str(config), LITE3_MAPS_DIR=str(site.parent),
               LITE3_WORKSPACE=str(workspace), LITE3_ROS_SETUP=str(setup))
    result = subprocess.run(["bash", str(ROOT / "onboard_ros2_ws/src/sensor_visualization/scripts/lite3_localization_start.sh")],
                            env=env, capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert "loaded/loaded/loaded" in result.stdout
    assert f"map:={site}/map.yaml" in result.stdout
    assert f"pose_file:={site}/initial_pose.json" in result.stdout
    assert "minimum_match_fraction:=0.80" in result.stdout


def test_changed_shell_scripts_parse_without_execution():
    paths = ["laptop_visualization/lite3_nav2_rviz.sh",
             "laptop_visualization/lite3_nav2_rviz_session.sh",
             "laptop_visualization/lite3_rviz_watcher.sh",
             "onboard_ros2_ws/src/sensor_visualization/scripts/lite3_localization_start.sh",
             "onboard_ros2_ws/src/sensor_visualization/scripts/lite3_localization_supervisor.sh"]
    for path in paths:
        subprocess.run(["bash", "-n", str(ROOT / path)], check=True, timeout=5)
