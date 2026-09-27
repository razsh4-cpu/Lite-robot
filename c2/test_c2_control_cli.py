import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "c2_control_cli", Path(__file__).with_name("c2_control_cli.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class C2ControlCliTest(unittest.TestCase):
    def capture(self, function, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = function(*args)
        return result, output.getvalue()

    def test_select_releases_before_changing_robot(self):
        calls = []
        with mock.patch.object(MODULE, "configured_robots", return_value={"robot_01"}), \
                mock.patch.object(MODULE, "selected_robot", return_value="robot_01"), \
                mock.patch.object(MODULE, "release_control",
                                  side_effect=lambda robot: (calls.append(("release", robot)) or (True, ""))), \
                mock.patch.object(MODULE, "set_parameter",
                                  side_effect=lambda name, value: (calls.append((name, value)) or (True, ""))):
            result, output = self.capture(MODULE.select_command, "robot_01")
        self.assertEqual(result, 0)
        self.assertEqual(calls, [("release", "robot_01"),
                                 ("selected_robot", "robot_01")])
        self.assertIn("COMMAND_SOURCE=NONE", output)

    def test_take_requires_joystick_before_enabling(self):
        with mock.patch.object(MODULE, "selected_robot", return_value="robot_01"), \
                mock.patch.object(MODULE, "configured_robots", return_value={"robot_01"}), \
                mock.patch.object(MODULE, "joystick_ready", return_value=False), \
                mock.patch.object(MODULE, "set_parameter") as setter:
            result, output = self.capture(MODULE.take_command)
        self.assertEqual(result, 3)
        setter.assert_not_called()
        self.assertIn("connect joystick", output)

    def test_take_acquires_only_after_arbiter_confirmation(self):
        with mock.patch.object(MODULE, "selected_robot", return_value="robot_01"), \
                mock.patch.object(MODULE, "configured_robots", return_value={"robot_01"}), \
                mock.patch.object(MODULE, "joystick_ready", return_value=True), \
                mock.patch.object(MODULE, "set_parameter", return_value=(True, "")) as setter, \
                mock.patch.object(MODULE, "wait_status", return_value=(True, "")):
            result, output = self.capture(MODULE.take_command)
        self.assertEqual(result, 0)
        setter.assert_called_once_with("manual_enabled", "true")
        self.assertIn("COMMAND_SOURCE=LAPTOP_XBOX", output)
        self.assertIn("no Stand or motion was sent", output)

    def test_release_returns_to_none(self):
        with mock.patch.object(MODULE, "selected_robot", return_value="robot_01"), \
                mock.patch.object(MODULE, "release_control", return_value=(True, "")):
            result, output = self.capture(MODULE.release_command)
        self.assertEqual(result, 0)
        self.assertIn("COMMAND_SOURCE=NONE", output)


if __name__ == "__main__":
    unittest.main()
