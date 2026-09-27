import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
REPO = ROOT.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GUARD = load("posture_guard", ROOT / "scripts" / "lite3_posture_guard.py")
CLI = load("posture_cli", REPO / "operator" / "lite3_robot_cli.py")


def healthy(posture="sitting", source="NONE"):
    return {
        "high_level_healthy": True,
        "telemetry_fresh": True,
        "posture": posture,
        "command_source": source,
        "motion_enabled": False,
        "velocities_zero": True,
    }


def test_state_aware_toggle_never_reverses_an_achieved_posture():
    assert GUARD.decision(healthy("standing"), "stand") == (
        True, "ROBOT ALREADY STANDING")
    assert GUARD.decision(healthy("sitting"), "down") == (
        True, "ROBOT ALREADY DOWN")


def test_posture_refuses_owner_motion_stale_or_unknown_state():
    assert not GUARD.decision(healthy(source="AUTONOMY"), "stand")[0]
    state = healthy()
    state["velocities_zero"] = False
    assert not GUARD.decision(state, "stand")[0]
    assert not GUARD.decision(healthy("unknown"), "stand")[0]
    state = healthy()
    state["telemetry_fresh"] = False
    assert not GUARD.decision(state, "stand")[0]


def test_only_existing_sit_stand_edge_is_generated():
    class Joy:
        def __init__(self, axes=None, buttons=None):
            self.axes = axes
            self.buttons = buttons

    neutral = CLI.neutral_message(Joy)
    edge = CLI.posture_message(Joy)
    assert neutral.axes == [0.0] * 8
    assert neutral.buttons == [0] * 15
    assert edge.axes == [0.0] * 8
    assert edge.buttons[0] == 1
    assert sum(edge.buttons) == 1


def test_cli_does_not_open_udp_or_bypass_c2():
    text = (REPO / "operator" / "lite3_robot_cli.py").read_text()
    assert "sendto(" not in text
    assert "43897" not in text
    assert "/c2/robot_01/laptop_xbox" in text
    assert '"/request"' in text
    assert '"/heartbeat"' in text
    assert '"/joy"' in text


def test_dry_run_acquires_and_releases_without_posture_edge():
    text = (REPO / "operator" / "lite3_robot_cli.py").read_text()
    acquired = text.index('relay.get("command_source") == "LAPTOP_XBOX"')
    dry_run = text.index("if dry_run:", acquired)
    pose_edge = text.index("pose_edge=True", dry_run)
    finally_release = text.index("node.send(False)", pose_edge)
    assert acquired < dry_run < pose_edge < finally_release
    assert "temporary C2 lease acquired" in text
    assert "guard_while_heartbeating" in text
    assert 'executor.submit(\n                remote_guard' in text
    assert '"preflight", action, "--allow-source", "LAPTOP_XBOX"' in text
