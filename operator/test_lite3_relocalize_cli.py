import importlib.util
from pathlib import Path
import sys
from unittest.mock import Mock, patch


PATH = Path(__file__).with_name("lite3_relocalize_cli.py")
SPEC = importlib.util.spec_from_file_location("lite3_relocalize_cli", PATH)
CLI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CLI
SPEC.loader.exec_module(CLI)


def healthy():
    return {
        "connected": True,
        "high_level_healthy": True,
        "telemetry_fresh": True,
        "posture": "standing",
        "command_source": "NONE",
        "motion_enabled": False,
        "velocities_zero": True,
        "localization_confidence": 0.77,
        "localization_state": "UNLOCALIZED",
    }


def healthy_system():
    return {
        "robot": True,
        "lidar": True,
        "odometry": True,
        "tf": True,
        "map": "Home_Map",
    }


def test_start_gate_requires_standing_none_and_zero():
    assert CLI.safe_to_start(healthy())[0]
    for key, value in (("posture", "sitting"),
                       ("command_source", "AUTONOMY"),
                       ("velocities_zero", False)):
        state = healthy()
        state[key] = value
        assert not CLI.safe_to_start(state)[0]


def test_wrapper_uses_only_existing_service_and_never_publishes_motion():
    text = PATH.read_text()
    assert "lite3-relocalization-motion.service" in text
    assert '"start", SERVICE' in text
    assert '"stop", SERVICE' in text
    assert "create_publisher" not in text
    assert "cmd_vel" not in text
    assert "SIT_STAND" not in text


def test_start_defaults_to_no_before_any_service_start(capsys):
    remote = Mock()
    with patch.object(CLI, "robot_snapshot", return_value=(healthy(), None)), \
            patch.object(CLI, "service_state", return_value="inactive"), \
            patch.object(CLI, "map_snapshot", return_value=(healthy_system(), None)), \
            patch.object(CLI, "run_remote", remote), \
            patch("builtins.input", return_value=""):
        assert CLI.start() == 0
    remote.assert_not_called()
    output = capsys.readouterr().out
    assert "Physical robot movement will occur" in PATH.read_text()
    assert "no ownership acquired; no motion sent" in output


def test_only_explicit_lowercase_or_uppercase_y_starts_existing_service():
    result = Mock(returncode=0, stdout="")
    with patch.object(CLI, "robot_snapshot", return_value=(healthy(), None)), \
            patch.object(CLI, "service_state", return_value="inactive"), \
            patch.object(CLI, "map_snapshot", return_value=(healthy_system(), None)), \
            patch.object(CLI, "run_remote", return_value=result) as remote, \
            patch("builtins.input", return_value="Y"):
        assert CLI.start() == 0
    remote.assert_called_once_with(
        "sudo", "-n", "/usr/bin/systemctl", "start", CLI.SERVICE,
        timeout=15)


def test_status_path_has_no_mutating_remote_command(capsys):
    with patch.object(CLI, "robot_snapshot", return_value=(healthy(), None)), \
            patch.object(CLI, "service_state", return_value="inactive"), \
            patch.object(CLI, "map_snapshot", return_value=(healthy_system(), None)):
        assert CLI.print_status() == 0
    output = capsys.readouterr().out
    assert "RELOCALIZATION .... IDLE" in output
    assert "MAP ............... Home_Map" in output
    assert "/scan ............. OK" in output
    assert "/odom ............. OK" in output
    assert "TF ................ OK" in output


def test_cancel_stops_existing_service_and_confirms_none(capsys):
    owned = healthy()
    owned["command_source"] = "AUTONOMY"
    with patch.object(CLI, "service_state", return_value="active"), \
            patch.object(CLI, "marker_active", return_value=True), \
            patch.object(CLI, "stop_and_cleanup", return_value=True) as cleanup, \
            patch.object(CLI, "robot_snapshot", side_effect=[
                (owned, None), (healthy(), None)]):
        assert CLI.cancel() == 0
    cleanup.assert_called_once_with()
    assert "COMMAND_SOURCE=NONE" in capsys.readouterr().out


def test_cancel_recovers_partial_failure_with_marker_but_inactive_service(capsys):
    owned = healthy()
    owned["command_source"] = "AUTONOMY"
    with patch.object(CLI, "service_state", return_value="failed"), \
            patch.object(CLI, "marker_active", return_value=True), \
            patch.object(CLI, "stop_and_cleanup", return_value=True) as cleanup, \
            patch.object(CLI, "robot_snapshot", side_effect=[
                (owned, None), (healthy(), None)]):
        assert CLI.cancel() == 0
    cleanup.assert_called_once_with()
    assert "COMMAND_SOURCE=NONE" in capsys.readouterr().out


def test_cleanup_orders_stop_before_release_and_marker_clear():
    ok = Mock(returncode=0, stdout="")
    with patch.object(CLI, "run_remote", return_value=ok) as remote:
        assert CLI.stop_and_cleanup()
    assert remote.call_args_list == [
        (("sudo", "-n", "/usr/bin/systemctl", "stop", CLI.SERVICE),
         {"timeout": 15}),
        ((CLI.RELEASE_AUTONOMY,), {"timeout": 8}),
        (("rm", "-f", CLI.MARKER), {"timeout": 5}),
    ]


def test_repeated_cancel_is_idempotent_and_makes_no_change(capsys):
    with patch.object(CLI, "service_state", return_value="inactive"), \
            patch.object(CLI, "marker_active", return_value=False), \
            patch.object(CLI, "robot_snapshot", return_value=(healthy(), None)), \
            patch.object(CLI, "stop_and_cleanup") as cleanup:
        assert CLI.cancel() == 0
    cleanup.assert_not_called()
    assert "RELOCALIZATION ALREADY IDLE" in capsys.readouterr().out


def test_enter_n_invalid_and_ctrl_c_never_start_or_acquire(capsys):
    for answer in ("", "n", "NO", "invalid", EOFError(), KeyboardInterrupt()):
        remote = Mock()
        effect = answer if isinstance(answer, BaseException) else None
        with patch.object(CLI, "robot_snapshot", return_value=(healthy(), None)), \
                patch.object(CLI, "map_snapshot", return_value=(healthy_system(), None)), \
                patch.object(CLI, "service_state", return_value="inactive"), \
                patch.object(CLI, "run_remote", remote), \
                patch("builtins.input", side_effect=effect, return_value=answer):
            assert CLI.start() == 0
        remote.assert_not_called()
    assert "no ownership acquired; no motion sent" in capsys.readouterr().out


def test_start_failure_runs_safe_cleanup(capsys):
    failure = Mock(returncode=1, stdout="failed")
    with patch.object(CLI, "robot_snapshot", return_value=(healthy(), None)), \
            patch.object(CLI, "map_snapshot", return_value=(healthy_system(), None)), \
            patch.object(CLI, "service_state", return_value="inactive"), \
            patch.object(CLI, "run_remote", return_value=failure), \
            patch.object(CLI, "stop_and_cleanup", return_value=True) as cleanup, \
            patch("builtins.input", return_value="y"):
        assert CLI.start() == 1
    cleanup.assert_called_once_with()
    assert "START FAILED" in capsys.readouterr().out
