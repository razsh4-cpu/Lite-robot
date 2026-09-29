from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_amcl_does_not_trust_a_fixed_startup_pose():
    config = (ROOT / "config/amcl.yaml").read_text(encoding="utf-8")
    assert "set_initial_pose: false" in config
    assert "set_initial_pose: true" not in config


def test_guard_is_launched_with_localization():
    launch = (ROOT / "launch/day1_localization.launch.py").read_text(encoding="utf-8")
    assert 'executable="localization_guard"' in launch
    assert 'name="lite3_localization_guard"' in launch


def test_guard_is_read_only_with_respect_to_robot_motion():
    guard = (ROOT / "lite3_state_estimation/localization_guard.py").read_text(encoding="utf-8")
    assert '"/scan"' in guard
    assert '"/map"' in guard
    assert '"/amcl_pose"' in guard
    assert '"/localization/status"' in guard
    assert "/cmd_vel" not in guard
    assert "joint" not in guard.lower()
    assert "minimum_match_fraction" in guard


def test_saved_pose_is_hypothesis_then_bounded_global_recovery():
    guard = (ROOT / "lite3_state_estimation/localization_guard.py").read_text(encoding="utf-8")
    assert "hypothesis_grace_period" in guard
    assert "global_search_timeout" in guard
    assert 'self.declare_parameter("global_retry_limit", 2)' in guard
    assert 'self.create_subscription(Odometry, "/odom"' in guard
    assert "_manual_motion_detected" in guard
    assert "manual motion detected; restarting bounded global search" in guard
    assert "self._global_attempts < retry_limit" in guard
    assert "rclpy.time.Time().to_msg()" in guard


def test_runtime_localization_never_overwrites_saved_pose():
    guard = (ROOT / "lite3_state_estimation/localization_guard.py").read_text(encoding="utf-8")
    assert "def _save_pose" not in guard
    assert "write_text(json.dumps" not in guard


def test_test_override_is_limited_to_180_seconds():
    guard = (ROOT / "lite3_state_estimation/localization_guard.py").read_text(
        encoding="utf-8")
    assert "0.0 < expires - created <= 180.0" in guard
    assert "0.0 < expires - created <= 600.0" not in guard
