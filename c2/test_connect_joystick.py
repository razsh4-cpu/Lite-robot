import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "connect_joystick", Path(__file__).with_name("connect_joystick.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


INFO = """Device 78:86:2E:B6:8F:C3
    Name: Xbox Wireless Controller
    Paired: yes
    Trusted: yes
    Connected: yes
    Battery Percentage: 0x57 (87)
"""


class ConnectJoystickTest(unittest.TestCase):
    def run_main(self):
        output = io.StringIO()
        with mock.patch("sys.argv", ["connect", "joystick"]), \
                contextlib.redirect_stdout(output):
            result = MODULE.main()
        return result, output.getvalue()

    def test_ready_reports_device_and_battery(self):
        with mock.patch.object(MODULE, "bluetooth_info", return_value=INFO), \
                mock.patch.object(MODULE, "find_valid_joystick",
                                  return_value=("/dev/input/js0", "Xbox Wireless Controller")), \
                mock.patch.object(MODULE, "choose_robot", return_value=("robot_01", "")), \
                mock.patch.object(MODULE, "select_and_take", return_value=(True, "")):
            result, output = self.run_main()
        self.assertEqual(result, 0)
        self.assertIn("JOYSTICK READY", output)
        self.assertIn("Battery: 87%", output)
        self.assertIn("ROBOT READY: robot_01", output)
        self.assertIn("if already standing, press RB once", output)
        self.assertNotIn("Press A for fresh Stand authorization", output)


    def test_bluetooth_without_input_is_not_ready(self):
        with mock.patch.object(MODULE, "bluetooth_info", return_value=INFO), \
                mock.patch.object(MODULE, "find_valid_joystick",
                                  side_effect=[("", "missing"), ("", "missing")]), \
                mock.patch.object(MODULE, "reconnect", return_value="Connection successful"):
            result, output = self.run_main()
        self.assertEqual(result, 3)
        self.assertIn("BLUETOOTH CONNECTED BUT INPUT NOT AVAILABLE", output)

    def test_unknown_controller_is_not_found(self):
        with mock.patch.object(MODULE, "bluetooth_info", return_value=""):
            result, output = self.run_main()
        self.assertEqual(result, 2)
        self.assertIn("JOYSTICK NOT FOUND", output)


    def test_c2_service_is_started_and_node_is_awaited(self):
        control = mock.Mock()
        control.NODE = "/lite3_c2_xbox"
        control.ros2.return_value = mock.Mock(
            returncode=0, stdout="String value is: robot_01\n")
        with mock.patch.object(MODULE, "run", return_value=mock.Mock(
                returncode=0, stdout="")) as start:
            ready, reason = MODULE.ensure_c2_service(control)
        self.assertTrue(ready)
        self.assertEqual(reason, "")
        start.assert_called_once_with(
            "systemctl", "--user", "start", "lite3-c2-xbox.service",
            timeout=8.0)


    def test_offline_robot_is_reported_before_ros_status_wait(self):
        with mock.patch.object(MODULE, "robot_reachable", return_value=False), \
                mock.patch.object(MODULE, "ensure_c2_service") as ensure:
            ready, reason = MODULE.select_and_take("robot_01")
        self.assertFalse(ready)
        self.assertEqual(reason, "ROBOT OFFLINE: robot_01 (192.168.2.32)")
        ensure.assert_not_called()

if __name__ == "__main__":
    unittest.main()
