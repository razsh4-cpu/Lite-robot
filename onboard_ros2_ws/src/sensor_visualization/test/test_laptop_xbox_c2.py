import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import time
from unittest.mock import Mock


ROOT = Path(__file__).parents[1]
REPO = ROOT.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ROBOT = load("laptop_xbox_source", ROOT / "scripts" / "lite3_laptop_xbox_source.py")
C2 = load("c2_xbox", REPO / "c2" / "lite3_c2_xbox.py")
AUTONOMY = load("autonomy_for_c2", ROOT / "scripts" / "lite3_autonomy_command_source.py")


def test_fresh_request_heartbeat_and_joy_are_all_required():
    core = ROBOT.LaptopXboxFreshness(0.30)
    joy = SimpleNamespace(axes=[0.0] * 8, buttons=[0] * 15)
    core.request(True, 1.0)
    core.heartbeat(True, 1.0)
    assert not core.ready(1.0)
    core.update_joy(joy, 1.0)
    assert core.ready(1.299)
    assert not core.ready(1.301)
    core.clear()
    assert not core.ready(1.0)


def test_laptop_xbox_and_autonomy_leases_are_mutually_exclusive(tmp_path):
    (tmp_path / "COMMAND_SOURCE").write_text("NONE\n")
    autonomy = AUTONOMY.CommandSourceLease(tmp_path)
    laptop = ROBOT.LaptopXboxLease(tmp_path)
    assert autonomy.acquire_autonomy()
    assert not laptop.acquire()
    assert laptop.owner() == "AUTONOMY"
    autonomy.release()
    assert laptop.acquire()
    assert laptop.owner() == "LAPTOP_XBOX"
    second_autonomy = AUTONOMY.CommandSourceLease(tmp_path)
    assert not second_autonomy.acquire_autonomy()
    laptop.release()
    assert laptop.owner() == "NONE"


def test_relay_restart_clears_only_orphaned_laptop_marker(tmp_path):
    source = tmp_path / "COMMAND_SOURCE"
    source.write_text("LAPTOP_XBOX\n")
    restarted = ROBOT.LaptopXboxLease(tmp_path)
    assert restarted.recover_stale_own_marker()
    assert restarted.owner() == "NONE"

    source.write_text("AUTONOMY\n")
    assert not restarted.recover_stale_own_marker()
    assert restarted.owner() == "AUTONOMY"


def test_relay_restart_does_not_clear_live_owner(tmp_path):
    source = tmp_path / "COMMAND_SOURCE"
    source.write_text("NONE\n")
    live = ROBOT.LaptopXboxLease(tmp_path)
    assert live.acquire()
    restarted = ROBOT.LaptopXboxLease(tmp_path)
    assert not restarted.recover_stale_own_marker()
    assert restarted.owner() == "LAPTOP_XBOX"
    live.release()


def test_robot_selection_is_single_target_and_switch_revokes_manual():
    robots = {"robot_01": {}, "robot_02": {}}
    registry = SimpleNamespace(get=lambda robot_id: robots[robot_id])
    core = C2.C2SelectionCore(registry, "robot_01")
    assert core.enable_manual(True)
    old = core.select("robot_02")
    assert old == "robot_01"
    assert core.selected == "robot_02"
    assert core.manual_enabled is False


def test_unknown_robot_is_rejected():
    registry = C2.RobotRegistry(REPO / "c2" / "robots.json")
    core = C2.C2SelectionCore(registry)
    try:
        core.select("missing")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown robot must be rejected")


def test_disabled_persistent_c2_releases_once_then_does_not_compete():
    node = C2.C2Xbox.__new__(C2.C2Xbox)
    node.core = SimpleNamespace(selected="robot_01", manual_enabled=False)
    node._disabled_release_sent = False
    node._release = Mock()
    node._tick()
    node._tick()
    node._release.assert_called_once_with("robot_01")


def test_enabled_stale_c2_still_releases_fail_safe():
    node = C2.C2Xbox.__new__(C2.C2Xbox)
    node.core = SimpleNamespace(selected="robot_01", manual_enabled=True)
    node._disabled_release_sent = True
    node.last_joy_time = None
    node._release = Mock()
    node._tick()
    node._release.assert_called_once_with("robot_01")
    assert node._disabled_release_sent is False


def test_c2_and_relay_never_open_robot_udp_or_write_command_source_directly():
    c2_text = (REPO / "c2" / "lite3_c2_xbox.py").read_text()
    relay_text = (ROOT / "scripts" / "lite3_laptop_xbox_source.py").read_text()
    assert "43897" not in c2_text + relay_text
    assert "sendto(" not in c2_text + relay_text
    assert "LAPTOP_XBOX\\n" not in c2_text
    assert "LAPTOP_XBOX\\n" in relay_text


def test_robot_relay_service_starts_safe_waiting_path_at_boot():
    unit = (ROOT / "systemd" / "lite3-laptop-xbox-source.service").read_text()
    assert "WantedBy=multi-user.target" in unit
    assert "lite3-high-level-runtime.service" in unit
    assert "lite3_laptop_xbox_source" in unit
    assert "lite3-high-level-xbox.service" not in unit


def test_runtime_has_separate_laptop_joy_topic_and_same_safety_gate():
    text = (ROOT / "scripts" / "xbox_lite3_motion_host_bridge.py").read_text()
    assert "'/lite3/laptop_xbox/joy'" in text
    assert "{'LOCAL_XBOX', 'LAPTOP_XBOX'}" in text
    assert "self._lease_is_held()" in text
    assert "self._manual_authorized" in text
    assert "self._robot_basic_state == self.STANDING_BASIC_STATE" in text
