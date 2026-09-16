#!/usr/bin/env python3
"""Fail-closed ROS 2 forward/backward/yaw control for the Lite3 vendor gait path.

Inputs are normalized joystick-like values, not m/s:
  /lite3/manual_forward_normalized  std_msgs/msg/Float32
  /lite3/manual_yaw_normalized      std_msgs/msg/Float32
  /lite3/manual_axis_deadman        std_msgs/msg/Bool (must refresh continuously)

Transmission is disabled by default. Lateral is always sent as neutral. It never
sends heartbeat, mode, posture, gait, KEEP_STEPPING, MotionSDK, RL, or joint
commands.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import os
import signal
import socket
import sys
import time
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


FORWARD_CODE = 0x21010130
LATERAL_CODE = 0x21010131
YAW_CODE = 0x21010135
COMMAND_TYPE = 0
HARD_MAX_FORWARD = 0.10
HARD_MAX_YAW = 0.25


def find_control_process_conflicts() -> list[str]:
    markers = (
        "lite3_validation_console",
        "xbox_lite3_motion_host_bridge",
        "lite3_replay_first_forward",
        "lite3_manual_axis_forward_probe",
        "lite3_manual_axis_backward_probe",
        "lite3_transfer",
    )
    own_pid = str(os.getpid())
    conflicts: list[str] = []
    for path in Path("/proc").glob("[0-9]*/cmdline"):
        if path.parent.name == own_pid:
            continue
        try:
            command = path.read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if any(marker in command for marker in markers):
            conflicts.append(f"pid={path.parent.name} cmd={command.strip()}")
    return conflicts


def load_existing_codecs(plugin_root: str):
    package_dir = Path(plugin_root) / "lite3_plugin"
    package_name = "_lite3_manual_axis_protocol"
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_dir)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    for name in ("protocol", "codecs"):
        full_name = f"{package_name}.{name}"
        spec = importlib.util.spec_from_file_location(full_name, package_dir / f"{name}.py")
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load existing Lite3 {name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_name] = module
        setattr(package, name, module)
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.codecs"]


def normalized_to_raw(value: float, hard_max: float = HARD_MAX_FORWARD) -> int:
    if not math.isfinite(value):
        raise ValueError("normalized command must be finite")
    value = max(-hard_max, min(hard_max, value))
    if value == 0.0:
        return 0
    if value > 0.0:
        return round(6553 + value * 26214)
    # Use floor so the exact -0.10 midpoint deterministically selects -9175,
    # matching the separately reviewed and hardware-proven backward profile.
    return math.floor(-6553 + value * 26215)


def raw_to_normalized(raw: int) -> float:
    if -6552 <= raw <= 6552:
        return 0.0
    if raw > 6552:
        return (raw - 6553) / 26214.0
    return (raw + 6553) / 26215.0


@dataclass
class SafetyState:
    command: float = 0.0
    command_time: Optional[float] = None
    yaw: float = 0.0
    yaw_time: Optional[float] = None
    deadman: bool = False
    deadman_time: Optional[float] = None
    robot_state: Optional[int] = None
    battery: Optional[float] = None
    robot_state_time: Optional[float] = None


class SafetyCore:
    def __init__(
        self, timeout_s: float, max_forward: float, max_yaw: float, min_battery: float
    ):
        if not 0.05 <= timeout_s <= 1.0:
            raise ValueError("timeout must be within [0.05, 1.0] seconds")
        if not 0.0 < max_forward <= HARD_MAX_FORWARD:
            raise ValueError(f"max_forward must be within (0, {HARD_MAX_FORWARD}]")
        if not 0.0 < max_yaw <= HARD_MAX_YAW:
            raise ValueError(f"max_yaw must be within (0, {HARD_MAX_YAW}]")
        self.timeout_s = timeout_s
        self.max_forward = max_forward
        self.max_yaw = max_yaw
        self.min_battery = min_battery
        self.state = SafetyState()

    def update_command(self, value: float, now: float) -> None:
        self.state.command = value if math.isfinite(value) else 0.0
        self.state.command_time = now

    def update_yaw(self, value: float, now: float) -> None:
        self.state.yaw = value if math.isfinite(value) else 0.0
        self.state.yaw_time = now

    def update_deadman(self, enabled: bool, now: float) -> None:
        self.state.deadman = bool(enabled)
        self.state.deadman_time = now

    def update_robot_state(self, state: int, battery: float, now: float) -> None:
        if not math.isfinite(battery):
            return
        self.state.robot_state = int(state)
        self.state.battery = float(battery)
        self.state.robot_state_time = now

    def output(self, now: float) -> tuple[bool, float, float, str]:
        s = self.state
        if s.robot_state_time is None or now - s.robot_state_time > self.timeout_s:
            return False, 0.0, 0.0, "robot_state_stale"
        if s.robot_state != 6:
            return False, 0.0, 0.0, f"robot_not_standing_{s.robot_state}"
        if s.battery is None or s.battery < self.min_battery:
            return False, 0.0, 0.0, "battery_low_or_unknown"
        if s.deadman_time is None or now - s.deadman_time > self.timeout_s:
            return False, 0.0, 0.0, "deadman_stale"
        if not s.deadman:
            return False, 0.0, 0.0, "deadman_released"
        if s.command_time is None or now - s.command_time > self.timeout_s:
            return False, 0.0, 0.0, "command_stale"
        if not math.isfinite(s.command):
            return False, 0.0, 0.0, "command_invalid"
        forward = max(-self.max_forward, min(self.max_forward, s.command))
        yaw_fresh = s.yaw_time is not None and now - s.yaw_time <= self.timeout_s
        yaw = max(-self.max_yaw, min(self.max_yaw, s.yaw)) if yaw_fresh else 0.0
        return True, forward, yaw, "enabled" if yaw_fresh else "enabled_yaw_stale_zeroed"


def run_self_test() -> int:
    assert normalized_to_raw(+0.10) == 9174
    assert normalized_to_raw(-0.10) == -9175
    # Positive ROS yaw maps to the vendor controller's negative right-stick X.
    assert normalized_to_raw(-0.25, HARD_MAX_YAW) == -13107
    assert abs(raw_to_normalized(9174) - 0.10) < 5e-5
    assert abs(raw_to_normalized(-9175) + 0.10) < 5e-5
    try:
        normalized_to_raw(math.nan)
    except ValueError:
        pass
    else:
        raise AssertionError("NaN accepted")

    core = SafetyCore(0.3, 0.1, 0.25, 25.0)
    assert core.output(1.0)[1:3] == (0.0, 0.0)
    core.update_robot_state(6, 50.0, 1.0)
    core.update_command(0.08, 1.0)
    core.update_deadman(True, 1.0)
    assert core.output(1.1) == (True, 0.08, 0.0, "enabled_yaw_stale_zeroed")
    core.update_yaw(0.10, 1.1)
    assert core.output(1.1) == (True, 0.08, 0.10, "enabled")
    assert core.output(1.31)[1] == 0.0  # all inputs stale
    core.update_robot_state(6, 50.0, 2.0)
    core.update_command(float("inf"), 2.0)
    core.update_deadman(True, 2.0)
    assert core.output(2.0)[1] == 0.0
    core.update_command(1.0, 2.1)
    core.update_yaw(-1.0, 2.1)
    core.update_robot_state(6, 50.0, 2.1)
    core.update_deadman(True, 2.1)
    assert core.output(2.1)[1:3] == (0.1, -0.25)
    core.update_deadman(False, 2.2)
    assert core.output(2.2)[1] == 0.0
    core.update_deadman(True, 3.0)
    core.update_command(-0.08, 3.0)
    core.update_robot_state(1, 50.0, 3.0)
    assert core.output(3.0)[1] == 0.0
    core.update_robot_state(6, 20.0, 4.0)
    core.update_deadman(True, 4.0)
    core.update_command(0.08, 4.0)
    assert core.output(4.0)[1] == 0.0
    print(
        "SELF_TEST_PASS forward_raw=9174 backward_raw=-9175 "
        "yaw_positive_raw=-13107 safety_fail_closed=YES"
    )
    print("ROBOT_PACKETS_SENT=0")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--self-test", action="store_true")
        parser.parse_args()
        return run_self_test()

    import rclpy
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from rclpy.signals import SignalHandlerOptions
    from std_msgs.msg import Bool, Float32, Int32, String

    class ManualAxisNode(Node):
        def __init__(self):
            super().__init__("lite3_manual_axis_control")
            self.declare_parameter("transmit", False)
            self.declare_parameter("robot_ip", "192.168.1.120")
            self.declare_parameter("command_port", 43893)
            self.declare_parameter("telemetry_port", 43897)
            self.declare_parameter("plugin_root", "/home/abx/emos-plugin-lite3")
            self.declare_parameter("timeout_ms", 300)
            self.declare_parameter("max_forward", 0.10)
            self.declare_parameter("max_yaw", 0.25)
            self.declare_parameter("min_battery_percent", 25.0)

            self.transmit = bool(self.get_parameter("transmit").value)
            self.robot_ip = str(self.get_parameter("robot_ip").value)
            self.command_port = int(self.get_parameter("command_port").value)
            telemetry_port = int(self.get_parameter("telemetry_port").value)
            timeout_s = int(self.get_parameter("timeout_ms").value) / 1000.0
            max_forward = float(self.get_parameter("max_forward").value)
            max_yaw = float(self.get_parameter("max_yaw").value)
            min_battery = float(self.get_parameter("min_battery_percent").value)
            self.core = SafetyCore(timeout_s, max_forward, max_yaw, min_battery)
            self.codecs = load_existing_codecs(str(self.get_parameter("plugin_root").value))

            if self.robot_ip != "192.168.1.120" or self.command_port != 43893:
                raise RuntimeError("V1 permits only the verified 192.168.1.120:43893 target")
            conflicts = find_control_process_conflicts()
            if conflicts:
                raise RuntimeError("conflicting control process(es): " + "; ".join(conflicts))

            self.telemetry = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.telemetry.setblocking(False)
            self.telemetry.bind(("0.0.0.0", telemetry_port))
            self.sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if self.transmit else None
            self.last_report: Optional[tuple[bool, str, int, int]] = None
            self.last_report_time = 0.0

            control_qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                reliability=ReliabilityPolicy.BEST_EFFORT,
            )
            self.create_subscription(
                Float32,
                "/lite3/manual_forward_normalized",
                self.on_command,
                control_qos,
            )
            self.create_subscription(
                Float32,
                "/lite3/manual_yaw_normalized",
                self.on_yaw,
                control_qos,
            )
            self.create_subscription(
                Bool,
                "/lite3/manual_axis_deadman",
                self.on_deadman,
                control_qos,
            )
            # Passive observability only. These publishers do not participate
            # in command decisions and cannot transmit to the robot.
            self.state_pub = self.create_publisher(
                Int32, "/lite3/robot_basic_state", control_qos
            )
            self.battery_pub = self.create_publisher(
                Float32, "/lite3/battery_percent", control_qos
            )
            self.state_fresh_pub = self.create_publisher(
                Bool, "/lite3/robot_state_fresh", control_qos
            )
            self.control_enabled_pub = self.create_publisher(
                Bool, "/lite3/control_enabled", control_qos
            )
            self.control_reason_pub = self.create_publisher(
                String, "/lite3/control_reason", control_qos
            )
            self.timer = self.create_timer(0.05, self.on_timer)
            self.get_logger().warning(
                f"Lite3 manual-axis control started transmit={self.transmit}; "
                "forward/back+yaw; normalized limits forward=%.3f yaw=%.3f; "
                "timeout=%.0fms"
                % (max_forward, max_yaw, timeout_s * 1000.0)
            )

        def on_command(self, msg) -> None:
            self.core.update_command(float(msg.data), time.monotonic())

        def on_yaw(self, msg) -> None:
            self.core.update_yaw(float(msg.data), time.monotonic())

        def on_deadman(self, msg) -> None:
            self.core.update_deadman(bool(msg.data), time.monotonic())

        def drain_telemetry(self) -> None:
            for _ in range(256):
                try:
                    raw, _source = self.telemetry.recvfrom(4096)
                except BlockingIOError:
                    return
                state = self.codecs.parse_robot_state(raw)
                if state is not None:
                    self.core.update_robot_state(
                        int(state.robot_basic_state),
                        float(state.battery_level),
                        time.monotonic(),
                    )

        def packets(self, forward: float, yaw: float = 0.0) -> list[bytes]:
            forward_raw = normalized_to_raw(forward)
            # The original-controller capture proves right_axis_yaw=-1.0
            # produces goal_vel_yaw=+1.0, hence the sign inversion here.
            yaw_raw = normalized_to_raw(-yaw, HARD_MAX_YAW)
            encode = self.codecs.encode_simple_cmd
            return [
                encode(FORWARD_CODE, forward_raw, COMMAND_TYPE),
                encode(LATERAL_CODE, 0, COMMAND_TYPE),
                encode(YAW_CODE, yaw_raw, COMMAND_TYPE),
            ]

        def send(self, forward: float, yaw: float = 0.0) -> None:
            if self.sender is None:
                return
            for payload in self.packets(forward, yaw):
                self.sender.sendto(payload, (self.robot_ip, self.command_port))

        def on_timer(self) -> None:
            self.drain_telemetry()
            now = time.monotonic()
            enabled, forward, yaw, reason = self.core.output(now)
            state = self.core.state
            state_fresh = (
                state.robot_state_time is not None
                and now - state.robot_state_time <= self.core.timeout_s
            )
            if state.robot_state is not None:
                self.state_pub.publish(Int32(data=state.robot_state))
            if state.battery is not None:
                self.battery_pub.publish(Float32(data=state.battery))
            self.state_fresh_pub.publish(Bool(data=state_fresh))
            self.control_enabled_pub.publish(Bool(data=enabled))
            self.control_reason_pub.publish(String(data=reason))
            self.send(forward if enabled else 0.0, yaw if enabled else 0.0)
            forward_raw = normalized_to_raw(forward if enabled else 0.0)
            yaw_raw = normalized_to_raw(
                -(yaw if enabled else 0.0), HARD_MAX_YAW
            )
            report = (enabled, reason, forward_raw, yaw_raw)
            if report != self.last_report or now - self.last_report_time >= 2.0:
                self.get_logger().info(
                    f"enabled={str(enabled).lower()} reason={reason} "
                    f"forward={forward if enabled else 0.0:+.6f} raw={forward_raw} "
                    f"lateral=0 yaw={yaw if enabled else 0.0:+.6f} yaw_raw={yaw_raw}"
                )
                self.last_report = report
                self.last_report_time = now

        def close(self) -> None:
            if self.sender is not None:
                for _ in range(5):
                    self.send(0.0)
                    time.sleep(0.02)
                self.sender.close()
                self.sender = None
            self.telemetry.close()

    # Preserve the ROS context until redundant neutral packets and socket
    # cleanup complete; the default handler can interrupt destroy_node().
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)

    def request_clean_shutdown(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, request_clean_shutdown)
    signal.signal(signal.SIGTERM, request_clean_shutdown)
    node = ManualAxisNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    finally:
        node.close()
        node.destroy_node()
        # ROS 2's SIGINT handler may already have shut down the context.
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
