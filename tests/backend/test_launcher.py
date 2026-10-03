"""Approval boundary of the actual launcher, with ROS construction stubbed."""
import sys
from types import SimpleNamespace
import pytest
from backend.lite3.run import main


@pytest.mark.parametrize("reply", ["", "n", "invalid", "eof", "interrupt"])
def test_launcher_without_yes_never_enables_execution(tmp_path, monkeypatch, reply):
    site = tmp_path / "site.yaml"
    site.write_text("map_yaml: map.yaml\nsaved_goals: goals.yaml\n")
    authority = SimpleNamespace(approved=False)
    calls = []
    runtime = SimpleNamespace(
        navigation=SimpleNamespace(authority=authority),
        backend=SimpleNamespace(request_id=None, goals=SimpleNamespace(resolve=lambda *a: None)),
        observation=SimpleNamespace(tracker=SimpleNamespace(map_identity="sha256:test")),
        verify=lambda: True, status=lambda: {}, goto=lambda *a: calls.append(a))
    ros = SimpleNamespace(init=lambda: None, ok=lambda: True, shutdown=lambda: None)
    monkeypatch.setitem(sys.modules, "rclpy", ros)
    monkeypatch.setitem(sys.modules, "rclpy.node", SimpleNamespace(Node=lambda name:
                        SimpleNamespace(destroy_node=lambda: None)))
    monkeypatch.setattr("backend.lite3.runtime.create_ros_runtime", lambda *a: runtime)
    def answer(prompt):
        if reply == "eof": raise EOFError()
        if reply == "interrupt": raise KeyboardInterrupt()
        return reply
    monkeypatch.setattr("builtins.input", answer)
    assert main(["--site", str(site), "--goto", "measured_goal"]) == 0
    assert not authority.approved
    assert not calls
