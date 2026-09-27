from pathlib import Path
import importlib.util
import sys
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "config" / "nav2_day2.yaml"


def load_safety_monitor():
    path = ROOT / "scripts" / "lite3_nav2_safety_monitor.py"
    spec = importlib.util.spec_from_file_location("day2_safety_monitor", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_nav2_limits_do_not_exceed_existing_autonomy_adapter():
    params = load_config()
    follow = params["controller_server"]["ros__parameters"]["FollowPath"]
    assert 0.0 < follow["max_vel_x"] <= 0.10
    # The first real goal is only 10 cm away; a 15 cm tolerance would falsely
    # succeed without motion. Keep arrival tolerance at or below 5 cm.
    assert params["controller_server"]["ros__parameters"][
        "goal_checker"]["xy_goal_tolerance"] <= 0.05
    assert follow["xy_goal_tolerance"] <= 0.05
    assert abs(follow["min_vel_y"]) <= 0.05
    assert follow["max_vel_y"] <= 0.05
    assert follow["max_vel_theta"] <= 0.20
    assert follow["min_vel_x"] >= 0.0


def test_saved_map_cli_has_explicit_80_percent_bounded_relocalization_gate():
    cli = (ROOT.parents[2] / "operator" / "lite3_map_cli.py").read_text(
        encoding="utf-8")
    manager = (ROOT / "scripts" / "lite3_map_manager.py").read_text(
        encoding="utf-8")
    guard = (ROOT.parent / "lite3_state_estimation" /
             "lite3_state_estimation" / "localization_guard.py").read_text(
        encoding="utf-8")
    assert "UNLOCALIZED — SHORT MANUAL MOVEMENT REQUIRED" in cli
    assert "LOCALIZED — NAVIGATION READY" in cli
    assert "Type YES" in cli
    assert 'remote("relocalize"' in cli
    assert "maximum lateral excursion" in cli
    assert '"navigation_ready": ok' in manager
    assert "self._good_cycles >= 3" in guard
    assert "_request_global" in guard


def test_costmaps_use_scan_and_conservative_lite3_footprint():
    config = load_config()
    expected = "[[0.355, 0.235], [0.355, -0.235], [-0.355, -0.235], [-0.355, 0.235]]"
    for name in ("global_costmap", "local_costmap"):
        params = config[name][name]["ros__parameters"]
        assert params["footprint"] == expected
        assert "obstacle_layer" in params["plugins"]
        assert params["obstacle_layer"]["scan"]["topic"] == "/scan"
        assert params["obstacle_layer"]["scan"]["marking"] is True
        assert params["obstacle_layer"]["scan"]["clearing"] is True


def test_safe_tree_has_no_automatic_recovery_motion():
    tree_path = ROOT / "config" / "navigate_to_pose_day2.xml"
    ET.parse(tree_path)
    text = tree_path.read_text(encoding="utf-8")
    assert "ComputePathToPose" in text and "FollowPath" in text
    assert "Spin" not in text and "BackUp" not in text
    assert "DriveOnHeading" not in text


def test_nav2_launch_does_not_duplicate_localization_or_own_autonomy():
    text = (ROOT / "launch" / "nav2_day2.launch.py").read_text(encoding="utf-8")
    assert "nav2_controller" in text
    assert "nav2_planner" in text
    assert "nav2_bt_navigator" in text
    assert "nav2_map_server" not in text
    assert "nav2_amcl" not in text
    assert "lite3_autonomy_command_source" not in text
    assert "43897" not in text


def test_path_preview_cannot_trigger_bt_navigation():
    bridge = (ROOT / "scripts" / "plan_from_rviz_goal.py").read_text(
        encoding="utf-8")
    launch = (ROOT / "launch" / "nav2_day2.launch.py").read_text(
        encoding="utf-8")
    rviz = (ROOT.parents[2] / "laptop_visualization" / "lite3_nav2.rviz").read_text(
        encoding="utf-8")
    assert "'/day2/preview_goal'" in bridge
    assert "'/goal_pose'" not in bridge
    assert "/day2/preview_goal" in rviz
    assert "Preview Goal (NO MOTION)" in rviz
    assert "/goal_pose" not in rviz
    assert "/goal_pose" in launch  # documented as intentionally unsafe for preview


def test_nav2_service_is_not_automatically_started_by_another_unit():
    unit = (ROOT / "systemd" / "lite3-nav2.service").read_text(encoding="utf-8")
    assert "lite3-localization.service" in unit
    assert "lite3-high-level-runtime.service" in unit
    assert "lite3-autonomy-command-source.service" not in unit
    assert "ROS_DOMAIN_ID=0" in unit
    assert "lite3_localization_gate --minimum 0.80" in unit


def test_autonomy_adapter_keeps_300ms_watchdog_and_explicit_start():
    unit = (ROOT / "systemd" / "lite3-autonomy-command-source.service").read_text(encoding="utf-8")
    assert "command_timeout_s:=0.30" in unit
    assert "max_forward:=0.10" in unit
    assert "max_lateral:=0.05" in unit
    assert "max_yaw:=0.20" in unit
    assert "ExecStopPost=" in unit
    assert "lite3_release_autonomy" in unit
    assert "lite3_localization_gate --minimum 0.80" in unit
    assert "[Install]" not in unit


def test_preflight_is_read_only_and_requires_none_source():
    text = (ROOT / "scripts" / "lite3_nav2_preflight.py").read_text(encoding="utf-8")
    assert 'source == "NONE"' in text
    assert "localization" in text and "0.80" in text
    assert "single_udp_receiver" in text
    for forbidden in ("create_publisher", "ros2 topic pub", "systemctl start",
                      "systemctl restart", "NavigateToPose.Goal"):
        assert forbidden not in text


def test_ultrasonic_telemetry_reuses_persistent_receiver():
    runtime = (ROOT / "scripts" / "xbox_lite3_motion_host_bridge.py").read_text(
        encoding="utf-8")
    assert "'/lite3/ultrasound'" in runtime
    assert "'/lite3/battery_percent'" in runtime
    assert 'state.battery_level' in runtime
    assert "state.ultrasound" in runtime
    # The existing persistent runtime still owns the sole telemetry bind.
    assert runtime.count("self._telemetry_socket.bind") == 1


def test_autonomy_acquires_lease_only_after_ros_entities_exist():
    source = (ROOT / "scripts" / "lite3_autonomy_command_source.py").read_text(
        encoding="utf-8")
    constructor = source.split("class AutonomyCommandSource", 1)[1].split(
        "    def _on_command", 1)[0]
    assert constructor.index("self.create_timer") < constructor.index(
        "self.lease.acquire_autonomy()")


def test_autonomy_shutdown_cannot_skip_lease_release_after_publish_error():
    source = (ROOT / "scripts" / "lite3_autonomy_command_source.py").read_text(
        encoding="utf-8")
    block = source.split("    def destroy_node(self):", 1)[1].split(
        "\n\ndef main()", 1)[0]
    assert "except Exception" in block
    assert "finally:" in block
    assert block.index("self.lease.release()") > block.index("finally:")


def test_release_helper_only_clears_stale_autonomy_source():
    helper = (ROOT / "scripts" / "lite3_release_autonomy.sh").read_text(
        encoding="utf-8")
    assert '== "AUTONOMY"' in helper
    assert "flock -n" in helper
    assert "NONE" in helper
    assert "ros2 topic pub" not in helper


def test_nav2_safety_monitor_revokes_adapter_without_robot_transport():
    monitor = (ROOT / "scripts" / "lite3_nav2_safety_monitor.py").read_text(
        encoding="utf-8")
    assert '!= "AUTONOMY"' in monitor
    assert 'localization_fraction < self.localization_hard_min' in monitor
    assert 'localization_grace' in monitor
    assert '"/scan"' in monitor and '"/odom"' in monitor
    assert '"/cmd_vel"' in monitor
    assert '"/lite3/battery_percent"' in monitor
    assert 'battery below safe threshold' in monitor
    assert "lite3-autonomy-command-source.service" in monitor
    assert "create_publisher" not in monitor
    assert "43897" not in monitor
    assert "cmd_stamp >= self.autonomy_since" in monitor


def test_safety_core_accepts_only_fresh_localized_bounded_state():
    core = load_safety_monitor().Nav2SafetyCore()
    now = 10.0
    core.touch("odom", now)
    core.touch("scan", now)
    core.update_localization("LOCALIZED", 0.85, now)
    core.update_battery(80.0, now)
    core.update_cmd(0.10, -0.05, 0.20, now)
    assert core.failure(now + 0.20) is None
    assert core.failure(now + 0.51) == "cmd_vel stale"


def test_safety_core_can_wait_for_first_approved_goal_only():
    core = load_safety_monitor().Nav2SafetyCore()
    now = 10.0
    core.touch("odom", now)
    core.touch("scan", now)
    core.update_localization("LOCALIZED", 0.85, now)
    core.update_battery(80.0, now)
    assert core.failure(now, require_cmd=False) is None
    assert core.failure(now, require_cmd=True) == "cmd_vel stale"


def test_safety_core_rejects_localization_loss_and_excess_command():
    core = load_safety_monitor().Nav2SafetyCore()
    now = 5.0
    core.touch("odom", now)
    core.touch("scan", now)
    core.update_cmd(0.0, 0.0, 0.0, now)
    core.update_battery(80.0, now)
    core.update_localization("UNLOCALIZED", 0.79, now)
    assert core.failure(now) is None
    for name in ("odom", "scan", "cmd_vel", "battery", "localization"):
        core.touch(name, now + 1.9)
    assert core.failure(now + 1.9) is None
    for name in ("odom", "scan", "cmd_vel", "battery", "localization"):
        core.touch(name, now + 2.0)
    assert core.failure(now + 2.0) == "localization below 80% beyond grace period"
    core.update_localization("LOCALIZED", 0.90, now + 2.0)
    core.update_cmd(0.101, 0.0, 0.0, now)
    assert core.failure(now) == "cmd_vel exceeds Day-2 limits"


def test_safety_core_localization_hysteresis_recovers_and_hard_loss_aborts():
    core = load_safety_monitor().Nav2SafetyCore()
    now = 5.0
    core.touch("odom", now)
    core.touch("scan", now)
    core.update_cmd(0.0, 0.0, 0.0, now)
    core.update_battery(80.0, now)
    core.update_localization("LOCALIZED", 0.85, now)
    assert core.failure(now) is None
    core.update_localization("UNLOCALIZED", 0.76, now + 0.1)
    for name in ("odom", "scan", "cmd_vel", "battery"):
        core.touch(name, now + 1.9)
    assert core.failure(now + 1.9) is None
    core.update_localization("LOCALIZED", 0.82, now + 1.9)
    assert core.failure(now + 1.9) is None
    core.update_localization("UNLOCALIZED", 0.69, now + 2.0)
    for name in ("odom", "scan", "cmd_vel", "battery"):
        core.touch(name, now + 2.0)
    assert core.failure(now + 2.0) == "localization below hard safety threshold"


def test_safety_core_rejects_low_or_stale_battery():
    core = load_safety_monitor().Nav2SafetyCore()
    now = 5.0
    core.touch("odom", now)
    core.touch("scan", now)
    core.update_localization("LOCALIZED", 0.90, now)
    core.update_cmd(0.0, 0.0, 0.0, now)
    core.update_battery(24.9, now)
    assert core.failure(now) == "battery below safe threshold"
    core.update_battery(80.0, now)
    assert core.failure(now) is None
    later = now + 2.01
    core.touch("odom", later)
    core.touch("scan", later)
    core.update_localization("LOCALIZED", 0.90, later)
    core.update_cmd(0.0, 0.0, 0.0, later)
    assert core.failure(later) == "battery stale"


def test_offline_world_has_no_command_or_hardware_path():
    text = (ROOT / "tools" / "nav2_offline_world.py").read_text(
        encoding="utf-8")
    assert '"/map"' in text and '"/scan"' in text and '"/odom"' in text
    for forbidden in ("/cmd_vel", "create_client", "socket.socket", "sendto",
                      "COMMAND_SOURCE", "systemctl"):
        assert forbidden not in text


def test_high_level_presence_watchdog_has_no_robot_command_path():
    script = (ROOT / "scripts" / "lite3_high_level_ros_watchdog.py").read_text(
        encoding="utf-8")
    wrapper = (ROOT / "scripts" / "lite3_high_level_runtime.sh").read_text(
        encoding="utf-8")
    assert "--parent-pid" in script
    assert "misses_required" in script and "startup_grace_s" in script
    assert 'lite3_high_level_ros_watchdog"' in wrapper
    assert '"$watchdog" --parent-pid "$$"' in wrapper
    for forbidden in ("create_publisher", "socket.socket", "sendto(",
                      "COMMAND_SOURCE", "StandingUp", "/cmd_vel", "systemctl"):
        assert forbidden not in script


def test_high_level_presence_watchdog_debounces_and_cools_down():
    path = ROOT / "scripts" / "lite3_high_level_ros_watchdog.py"
    spec = importlib.util.spec_from_file_location("runtime_presence_watchdog", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    core = module.RuntimePresenceCore(
        misses_required=3, startup_grace_s=10.0, cooldown_s=20.0)
    assert not core.observe(False, 1.0)
    assert not core.observe(False, 11.1)
    assert not core.observe(False, 13.1)
    assert core.observe(False, 15.1)
    assert not core.observe(False, 17.1)
    assert not core.observe(True, 36.0)


def test_navigation_critical_ros_entrypoints_use_udp_only_fastdds():
    launch = (ROOT / "launch" / "nav2_day2.launch.py").read_text(encoding="utf-8")
    assert 'SetEnvironmentVariable("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")' in launch
    units = (
        "lite3-high-level-runtime.service",
        "lite3-localization.service", "lite3-nav2.service",
        "lite3-nav2-safety-monitor.service",
        "lite3-autonomy-command-source.service",
        "lite3-laptop-xbox-source.service", "lite3-mapping.service",
        "lite3-system-health.service",
    )
    for name in units:
        text = (ROOT / "systemd" / name).read_text(encoding="utf-8")
        assert "FASTDDS_BUILTIN_TRANSPORTS=UDPv4" in text, name
    scripts = (
        "lite3_high_level_runtime.sh",
        "lite3_ros_inputs_ready.py", "lite3_localization_start.sh",
        "lite3_autonomy_command_source.py", "lite3_nav2_preflight.py",
        "lite3_nav2_safety_monitor.py", "lite3_laptop_xbox_source.py",
        "lite3_map_manager.py", "lite3_system_health.sh",
    )
    for name in scripts:
        text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "FASTDDS_BUILTIN_TRANSPORTS" in text, name



def test_rviz_uses_blue_live_heading_and_exact_body_marker():
    rviz = (ROOT.parents[2] / "laptop_visualization/lite3_nav2.rviz").read_text()
    marker = (ROOT.parents[2] / "laptop_visualization/lite3_robot_marker.py").read_text()
    session = (ROOT.parents[2] / "laptop_visualization/lite3_nav2_rviz_session.sh").read_text()
    assert "Color: 0; 90; 255" in rviz
    assert "Value: /localization/pose" in rviz
    assert "Value: /lite3/robot_body" in rviz
    assert 'marker.header.frame_id = "base_link"' in marker
    assert "marker.scale.x = 0.610" in marker
    assert "marker.scale.y = 0.370" in marker
    assert session.count("rviz2 ") == 1
    assert "lite3_robot_marker.py" in session
    assert "Class: rviz_default_plugins/TF\n      Enabled: false" in rviz

def test_day2_physical_plan_has_three_bounded_tests_and_abort_conditions():
    plan = (ROOT / "docs/DAY2_PHYSICAL_TESTS.md").read_text()
    assert "Test 1 — 10 cm" in plan
    assert "Test 2 — 0.5–1.0 m plus turn" in plan
    assert "Test 3 — obstacle response" in plan
    assert "localization <80%" in plan
    assert "stale scan/odom/telemetry" in plan
    assert "operator's explicit approval" in plan


def test_relocalization_motion_is_bounded_centered_and_operator_only():
    script = ROOT / "scripts" / "lite3_relocalization_motion.py"
    spec = importlib.util.spec_from_file_location("relocalization_motion", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    core = module.RecoveryCore()
    assert core.maximum_duration < 10.0
    lateral_integral = sum(duration * lateral for duration, lateral in core.PHASES)
    assert abs(lateral_integral) < 1e-9
    assert max(abs(value) for _, value in core.PHASES) <= 0.03
    assert not core.update_score("LOCALIZED", 0.81)
    assert not core.update_score("LOCALIZED", 0.82)
    assert core.update_score("LOCALIZED", 0.83)
    text = script.read_text(encoding="utf-8")
    assert "LITE3_RELOCALIZATION_APPROVED" in text
    assert "0.55" in text
    assert "battery below 25%" in text


def test_relocalization_service_never_starts_at_boot_and_uses_adapter():
    unit = (ROOT / "systemd" / "lite3-relocalization-motion.service").read_text(encoding="utf-8")
    runner = (ROOT / "scripts" / "lite3_relocalization_run.sh").read_text(encoding="utf-8")
    assert "no [Install]" in unit
    assert "lite3_relocalization_run" in unit
    assert "lite3_autonomy_command_source" in runner
    assert "relocalization_mode:=true" in runner
    assert "max_lateral:=0.03" in runner
    assert "COMMAND_SOURCE" in runner and "AUTONOMY" in runner


def test_all_operator_rviz_paths_use_one_clean_canonical_config():
    root = ROOT.parents[2]
    canonical = root / "laptop_visualization/lite3_remote_lidar.rviz"
    alias = root / "laptop_visualization/lite3_nav2.rviz"
    text = canonical.read_text(encoding="utf-8")
    assert alias.resolve() == canonical.resolve()
    assert "/global_costmap/costmap" not in text
    assert "/local_costmap/costmap" not in text
    assert "Color: 255; 60; 40" in text
    assert text.count("Color: 0; 90; 255") == 2
    assert "Value: /lite3/robot_body" in text
    assert "Value: /planned_path" in text
    assert "Value: /day2/preview_goal" in text
    for relative in (
        "laptop_visualization/lite3_nav2_rviz_session.sh",
        "laptop_visualization/lite3_nav2_rviz.sh",
        "laptop_visualization/lite3_rviz_watcher.sh",
        "operator/lite3_map_cli.py",
    ):
        launcher = (root / relative).read_text(encoding="utf-8")
        assert "lite3_nav2.rviz" not in launcher
        assert ("lite3_remote_lidar.rviz" in launcher or
                "lite3_nav2_rviz_session.sh" in launcher)
