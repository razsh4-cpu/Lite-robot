import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "disconnect_joystick", Path(__file__).with_name("disconnect_joystick.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DisconnectJoystickTest(unittest.TestCase):
    def run_main(self):
        output = io.StringIO()
        with mock.patch("sys.argv", ["disconnect", "joystick"]), \
                contextlib.redirect_stdout(output):
            result = MODULE.main()
        return result, output.getvalue()

    def test_release_precedes_bluetooth_disconnect(self):
        calls = []
        with mock.patch.object(
                MODULE, "release_manual",
                side_effect=lambda: (calls.append("release") or (True, ""))), \
                mock.patch.object(
                    MODULE, "wait_for_release",
                    side_effect=lambda: (calls.append("confirm") or (True, ""))), \
                mock.patch.object(
                    MODULE, "disconnect_bluetooth",
                    side_effect=lambda: (calls.append("disconnect") or (True, ""))):
            result, output = self.run_main()
        self.assertEqual(result, 0)
        self.assertEqual(calls, ["release", "confirm", "disconnect"])
        self.assertIn("COMMAND_SOURCE=NONE", output)

    def test_disconnect_still_fails_safe_when_release_api_is_unavailable(self):
        with mock.patch.object(MODULE, "release_manual", return_value=(False, "denied")), \
                mock.patch.object(MODULE, "disconnect_bluetooth", return_value=(True, "")) as disconnect:
            result, output = self.run_main()
        self.assertEqual(result, 0)
        disconnect.assert_called_once()
        self.assertIn("release requested", output)


if __name__ == "__main__":
    unittest.main()
