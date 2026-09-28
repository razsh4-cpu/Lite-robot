from pathlib import Path
import pytest
from bipolix_missions import AdHocTarget, Mission, MissionState, SavedLocationTarget

ROOT = Path(__file__).resolve().parents[2]

def test_saved_and_ad_hoc_targets_are_vendor_neutral():
    named = SavedLocationTarget("main_gate_observation")
    ad_hoc = AdHocTarget(1.0, -0.5, 0.25)
    assert named.name == "main_gate_observation"
    assert ad_hoc.frame_id == "map"

def test_target_validation_rejects_unsafe_or_ambiguous_values():
    with pytest.raises(ValueError):
        SavedLocationTarget("../../unsafe")
    with pytest.raises(ValueError):
        AdHocTarget(float("nan"), 0.0, 0.0)
    with pytest.raises(ValueError):
        AdHocTarget(0.0, 0.0, 0.0, frame_id="odom")

def test_minimal_mission_lifecycle_and_cancel_are_explicit():
    mission = Mission("m-001", "robot_01", SavedLocationTarget("gate"))
    mission = mission.transition(MissionState.VALIDATING)
    mission = mission.transition(MissionState.NAVIGATING)
    mission = mission.transition(MissionState.CANCELLED, "operator request")
    assert mission.state is MissionState.CANCELLED
    assert mission.detail == "operator request"
    with pytest.raises(ValueError):
        mission.transition(MissionState.NAVIGATING)

def test_mission_contract_has_no_ros_vendor_or_motion_execution_dependency():
    body = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src/missions").rglob("*.py"))
    for forbidden in ("DeepRobotics", "MotionSDK", "SIT_STAND", "rclpy", "NavigateToPose", "/cmd_vel", "COMMAND_SOURCE", "43897"):
        assert forbidden not in body
