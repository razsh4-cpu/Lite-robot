import importlib.util
from pathlib import Path
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "connect_joystick", Path(__file__).with_name("connect_joystick.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RobotChooserTest(unittest.TestCase):
    def test_interactive_selection_uses_registry(self):
        with mock.patch("sys.stdin.isatty", return_value=True), \
                mock.patch("builtins.input", return_value="robot_01"), \
                mock.patch("c2_control_cli.configured_robots",
                           return_value={"robot_01"}):
            robot_id, reason = MODULE.choose_robot(None)
        self.assertEqual(robot_id, "robot_01")
        self.assertEqual(reason, "")

    def test_unknown_robot_is_rejected(self):
        with mock.patch("c2_control_cli.configured_robots",
                        return_value={"robot_01"}):
            robot_id, reason = MODULE.choose_robot("robot_02")
        self.assertEqual(robot_id, "")
        self.assertIn("not configured", reason)


if __name__ == "__main__":
    unittest.main()
