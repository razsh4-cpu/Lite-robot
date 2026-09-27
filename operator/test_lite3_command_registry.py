import importlib.util
from pathlib import Path
import sys


PATH = Path(__file__).with_name("lite3_command_registry.py")
SPEC = importlib.util.spec_from_file_location("lite3_command_registry", PATH)
REGISTRY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REGISTRY
SPEC.loader.exec_module(REGISTRY)


def test_required_real_operator_commands_are_registered():
    commands = {entry.command for entry in REGISTRY.COMMANDS}
    required = {
        "robot status", "robot stand", "robot down",
        "connect joystick", "disconnect joystick",
        "take control", "release control", "c2",
        "maps", "mapping",
        "relocalize status", "relocalize", "relocalize cancel",
        "status", "commands",
    }
    assert required <= commands


def test_registry_is_unique_and_motion_is_explicitly_marked():
    commands = [entry.command for entry in REGISTRY.COMMANDS]
    assert len(commands) == len(set(commands))
    tags = {entry.command: entry.tag for entry in REGISTRY.COMMANDS}
    for command in ("robot stand", "robot down", "relocalize"):
        assert tags[command] == "MOTION"
    for command in ("robot status", "relocalize status", "status", "commands"):
        assert tags[command] == "READ ONLY"


def test_menu_is_local_and_has_no_robot_side_effect_path():
    text = PATH.read_text()
    for forbidden in ("subprocess", "rclpy", "ssh", "systemctl", "cmd_vel"):
        assert forbidden not in text
    menu = REGISTRY.render()
    assert menu.startswith("# LITE3 OPERATOR COMMANDS")
    assert "[MOTION]" in menu
    assert "[READ ONLY]" in menu
