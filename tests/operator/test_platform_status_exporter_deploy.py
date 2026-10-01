from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_deployer_only_installs_and_starts_read_only_exporter():
    text = (ROOT / "operator/apply_platform_status_exporter.sh").read_text()
    assert "lite3-platform-status-exporter.service" in text
    assert "platform-status-exporter.env" in text
    assert "robot_id" in text
    assert "systemctl restart lite3-platform-status-exporter.service" in text
    for forbidden in ("lite3-high-level-runtime.service", "lite3-nav2.service",
                      "COMMAND_SOURCE", "owner.lock", "ros2 topic pub", "sendto"):
        assert forbidden not in text


def test_exporter_unit_has_no_motion_dependencies():
    text = (ROOT / "onboard_ros2_ws/src/sensor_visualization/systemd/"
            "lite3-platform-status-exporter.service").read_text()
    assert "lite3_platform_status_exporter" in text
    assert "WantedBy=multi-user.target" in text
    for forbidden in ("AUTONOMY", "LAPTOP_XBOX", "/cmd_vel", "nav2.service"):
        assert forbidden not in text
