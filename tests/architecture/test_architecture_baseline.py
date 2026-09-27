from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "docs" / "architecture"


def read(name):
    return (ARCH / name).read_text(encoding="utf-8")


def test_source_of_truth_defines_every_top_level_layer_and_supporting_concern():
    text = read("ARCHITECTURE.md")
    for layer in (
        "OPERATOR / C2",
        "MISSION LAYER",
        "AUTONOMY",
        "PERCEPTION",
        "SAFETY / ARBITRATION",
        "ROBOT INTERFACE",
        "ROBOT ADAPTER",
        "VENDOR / HARDWARE",
        "PHYSICAL ROBOT",
    ):
        assert layer in text
    for concern in (
        "State Estimation",
        "Sensor Management",
        "Configuration",
        "Calibration",
        "Robot Identity",
        "Health / Diagnostics",
        "Logging / Black Box",
        "Networking",
        "Deployment",
        "Updates / Rollback",
        "Backup / Restore",
        "Testing / Acceptance",
    ):
        assert concern in text


def test_real_inventory_names_all_robot_side_services_that_exist():
    inventory = read("COMPONENT_INVENTORY.md")
    unit_dir = ROOT / "onboard_ros2_ws" / "src" / "sensor_visualization" / "systemd"
    required = (
        "lite3-ros-network-ready.service",
        "lite3-high-level-runtime.service",
        "lite3-laptop-xbox-source.service",
        "lite3-lidar.service",
        "lite3-localization.service",
        "lite3-mapping.service",
        "lite3-nav2.service",
        "lite3-nav2-safety-monitor.service",
        "lite3-system-health.service",
        "lite3-realsense.service",
        "lite3-relocalization-motion.service",
    )
    for name in required:
        assert (unit_dir / name).is_file()
        assert name in inventory


def test_tf_ownership_matches_current_implementation():
    data = read("CONFIGURATION_CALIBRATION_DATA.md")
    runtime = (ROOT / "onboard_ros2_ws" / "src" / "sensor_visualization" /
               "scripts" / "xbox_lite3_motion_host_bridge.py").read_text(encoding="utf-8")
    lidar = (ROOT / "onboard_ros2_ws" / "src" / "sensor_visualization" /
             "launch" / "lite3_lidar_bringup.launch.py").read_text(encoding="utf-8")
    localization = (ROOT / "onboard_ros2_ws" / "src" / "lite3_state_estimation" /
                    "launch" / "day1_localization.launch.py").read_text(encoding="utf-8")
    assert "`map→odom` | AMCL" in data
    assert "`odom→base_link` | persistent `/lite3_high_level_runtime`" in data
    assert "`base_link→lidar_link` | `base_to_lidar_tf`" in data
    assert "TransformBroadcaster" in runtime and "child_frame_id = 'base_link'" in runtime
    assert '"--child-frame-id", "lidar_link"' in lidar
    assert 'executable="amcl"' in localization


def test_product_and_low_level_rnd_paths_are_explicitly_separate():
    architecture = read("ARCHITECTURE.md")
    operations = read("PLATFORM_OPERATIONS.md")
    assert "Advanced Locomotion / Physical AI R&D" in architecture
    assert "Vendor Gait + ROS2/Nav2 = product/patrol path" in operations
    assert "Low-Level/MotionSDK/ONNX = advanced locomotion R&D" in operations


def test_safety_baseline_preserves_sources_and_watchdog():
    safety = read("SAFETY_AND_ARBITRATION.md")
    for source in ("NONE", "LOCAL_XBOX", "LAPTOP_XBOX", "AUTONOMY"):
        assert source in safety
    assert "300 ms" in safety
    assert "zero" in safety.lower()
    assert "release" in safety.lower()
    assert "no restored velocity/authorization" in safety


def test_robot_site_software_and_calibration_are_separate():
    data = read("CONFIGURATION_CALIBRATION_DATA.md")
    for domain in ("Software", "Robot", "Site"):
        assert f"| {domain} |" in data
    assert "Calibration is a measured relationship" in data
    assert "must not be changed or duplicated during this phase" in data


def test_migration_plan_protects_single_owners_and_day3_boundary():
    migration = read("MIGRATION_PLAN.md")
    for protected in (
        "UDP 43897 ownership",
        "`/odom` and `odom→base_link`",
        "AMCL `map→odom`",
        "AUTONOMY 300 ms watchdog",
    ):
        assert protected in migration
    assert "Mission Layer (future Day 3)" in migration


def test_architecture_baseline_contains_no_new_runtime_unit_or_launch():
    # Architecture Baseline additions are documentation/tests only. The generic
    # Phase-1 code remains pure and no baseline-specific runtime artifact exists.
    assert not list(ROOT.glob("**/*architecture*baseline*.service"))
    assert not list(ROOT.glob("**/*architecture*baseline*.launch.py"))

def test_local_architecture_markdown_links_resolve():
    import re

    for document in ARCH.glob("*.md"):
        body = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", body):
            assert (document.parent / target).resolve().is_file(), (
                f"broken architecture link in {document.name}: {target}")
