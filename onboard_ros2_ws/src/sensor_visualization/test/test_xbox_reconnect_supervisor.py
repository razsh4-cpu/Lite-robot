import importlib.util
from pathlib import Path


SCRIPT = (Path(__file__).parents[1] / "scripts" /
          "lite3_xbox_reconnect_supervisor.py")
SPEC = importlib.util.spec_from_file_location("xbox_supervisor", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeOps:
    def __init__(self, validator, runtime=None, robot_runtime=None):
        self.validator = list(validator)
        self.runtime = list(runtime or [])
        self.robot_runtime = list(robot_runtime or [])
        self.calls = []
        self.starts = []

    def run(self, args, timeout=None):
        self.calls.append(tuple(args))
        if args[0].endswith("validator"):
            return self.validator.pop(0) if self.validator else False
        if args[:3] == ["systemctl", "is-active", "--quiet"]:
            states = (self.robot_runtime if args[3] == "lite3-high-level-runtime.service"
                      else self.runtime)
            return states.pop(0) if states else False
        if args[:2] == ["systemctl", "start"]:
            self.starts.append(args[2])
            return True
        return True

    def sleep(self, _seconds):
        pass

    def output(self, args):
        self.calls.append(tuple(args))
        return "Connected: yes\n"


def make_supervisor(tmp_path, ops, attempts=2):
    env = {
        "LITE3_STATE_DIR": str(tmp_path),
        "LITE3_XBOX_VALIDATOR": "/tmp/validator",
        "LITE3_XBOX_MAX_ATTEMPTS": str(attempts),
        "LITE3_XBOX_RETRY_SECONDS": "0",
        "LITE3_XBOX_SUPERVISE": "false",
    }
    return MODULE.XboxReconnectSupervisor(ops=ops, env=env)


def test_boot_with_xbox_starts_exactly_one_runtime(tmp_path):
    ops = FakeOps([True], runtime=[False], robot_runtime=[False])
    supervisor = make_supervisor(tmp_path, ops)
    assert supervisor.run() == 0
    assert ops.starts == [
        "lite3-high-level-runtime.service",
        "lite3-high-level-xbox.service",
    ]
    assert (tmp_path / "MANUAL_CONTROL_AVAILABLE").read_text().strip() == "true"


def test_boot_without_xbox_finishes_normally_after_finite_window(tmp_path):
    ops = FakeOps([False, False], robot_runtime=[False])
    supervisor = make_supervisor(tmp_path, ops)
    assert supervisor.run() == 0
    assert ops.starts == ["lite3-high-level-runtime.service"]
    assert (tmp_path / "MANUAL_CONTROL_AVAILABLE").read_text().strip() == "false"
    assert (tmp_path / "COMMAND_SOURCE").read_text().strip() == "NONE"


def test_arbitrary_delay_then_reconnect_starts_fresh_runtime(tmp_path):
    ops = FakeOps([False, False, True], runtime=[False])
    supervisor = make_supervisor(tmp_path, ops)
    assert supervisor.reconnect_until_ready() is True
    assert ops.starts == ["lite3-high-level-xbox.service"]
    assert (tmp_path / "MANUAL_CONTROL_AVAILABLE").read_text().strip() == "true"


def test_repeated_reconnects_start_one_fresh_runtime_per_cycle(tmp_path):
    ops = FakeOps([True, False, True], runtime=[False, False])
    supervisor = make_supervisor(tmp_path, ops)
    assert supervisor.reconnect_until_ready() is True
    assert supervisor.reconnect_until_ready() is True
    assert ops.starts == [
        "lite3-high-level-xbox.service",
        "lite3-high-level-xbox.service",
    ]


def test_repeated_start_does_not_duplicate_active_runtime(tmp_path):
    ops = FakeOps([], runtime=[True, True])
    supervisor = make_supervisor(tmp_path, ops)
    assert supervisor.start_runtime() is True
    assert supervisor.start_runtime() is True
    assert ops.starts == []


def test_existing_command_source_prevents_takeover(tmp_path):
    ops = FakeOps([], runtime=[False])
    supervisor = make_supervisor(tmp_path, ops)
    supervisor.lease_available = lambda: False
    assert supervisor.start_runtime() is False
    assert ops.starts == []


def test_disconnect_marks_unavailable_and_none_only_after_release(tmp_path):
    ops = FakeOps([])
    supervisor = make_supervisor(tmp_path, ops)
    supervisor.write_state("MANUAL_CONTROL_AVAILABLE", "true")
    supervisor.write_state("COMMAND_SOURCE", "LOCAL_XBOX")
    supervisor.mark_unavailable()
    assert (tmp_path / "MANUAL_CONTROL_AVAILABLE").read_text().strip() == "false"
    assert (tmp_path / "COMMAND_SOURCE").read_text().strip() == "NONE"


def test_existing_robot_runtime_is_not_restarted(tmp_path):
    ops = FakeOps([False, False], robot_runtime=[True])
    supervisor = make_supervisor(tmp_path, ops)
    assert supervisor.run() == 0
    assert "lite3-high-level-runtime.service" not in ops.starts


def test_disconnect_never_stops_persistent_robot_runtime(tmp_path):
    ops = FakeOps([])
    supervisor = make_supervisor(tmp_path, ops)
    supervisor.write_state("MANUAL_CONTROL_AVAILABLE", "true")
    supervisor.write_state("COMMAND_SOURCE", "LOCAL_XBOX")
    supervisor.mark_unavailable()
    assert (tmp_path / "MANUAL_CONTROL_AVAILABLE").read_text().strip() == "false"
    assert (tmp_path / "COMMAND_SOURCE").read_text().strip() == "NONE"
    assert ("systemctl", "stop", "lite3-high-level-runtime.service") not in ops.calls
