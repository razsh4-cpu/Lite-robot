#!/usr/bin/env python3
"""Lease-owning /cmd_vel adapter for the persistent Lite3 high-level runtime."""

from dataclasses import dataclass
import fcntl
import math
import os
from pathlib import Path
import signal
import time

os.environ.setdefault('FASTDDS_BUILTIN_TRANSPORTS', 'UDPv4')
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


@dataclass(frozen=True)
class CommandOutput:
    enabled: bool
    forward: float
    lateral: float
    yaw: float
    reason: str


class AutonomyCommandCore:
    def __init__(self, timeout_s=0.30, max_forward=0.10,
                 max_lateral=0.05, max_yaw=0.20):
        self.timeout_s = max(0.05, float(timeout_s))
        self.max_forward = max(0.0, float(max_forward))
        self.max_lateral = max(0.0, float(max_lateral))
        self.max_yaw = max(0.0, float(max_yaw))
        self.last_time = None
        self.values = (0.0, 0.0, 0.0)
        self.invalid = False

    def update(self, forward, lateral, yaw, now):
        values = (float(forward), float(lateral), float(yaw))
        if not all(math.isfinite(value) for value in values):
            self.invalid = True
            self.last_time = None
            self.values = (0.0, 0.0, 0.0)
            return
        self.invalid = False
        self.last_time = float(now)
        self.values = (
            max(-self.max_forward, min(self.max_forward, values[0])),
            max(-self.max_lateral, min(self.max_lateral, values[1])),
            max(-self.max_yaw, min(self.max_yaw, values[2])),
        )

    def output(self, now):
        if self.invalid:
            return CommandOutput(False, 0.0, 0.0, 0.0, 'invalid')
        if self.last_time is None:
            return CommandOutput(False, 0.0, 0.0, 0.0, 'waiting')
        if float(now) - self.last_time > self.timeout_s:
            return CommandOutput(False, 0.0, 0.0, 0.0, 'stale')
        return CommandOutput(True, *self.values, 'fresh')


class CommandSourceLease:
    VALID_SOURCES = {'NONE', 'LOCAL_XBOX', 'LAPTOP_XBOX', 'AUTONOMY'}

    def __init__(self, state_dir):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.source_path = self.state_dir / 'COMMAND_SOURCE'
        self.lock_path = self.state_dir / 'owner.lock'
        self.lock = None

    def acquire_autonomy(self):
        self.lock = self.lock_path.open('a+')
        try:
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            self.lock = None
            return False
        current = (self.source_path.read_text(encoding='utf-8').strip()
                   if self.source_path.exists() else 'NONE')
        if current != 'NONE':
            fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
            self.lock.close()
            self.lock = None
            return False
        self.source_path.write_text('AUTONOMY\n', encoding='utf-8')
        return True

    def release(self):
        if self.lock is None:
            return
        current = (self.source_path.read_text(encoding='utf-8').strip()
                   if self.source_path.exists() else 'NONE')
        if current == 'AUTONOMY':
            self.source_path.write_text('NONE\n', encoding='utf-8')
        fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
        self.lock.close()
        self.lock = None


def relocalization_inputs_ready(state_dir, max_age=2.5, now=None):
    """Allow explicit recovery only with fresh localization telemetry."""
    state_dir = Path(state_dir)
    now = time.time() if now is None else float(now)
    state_path = state_dir / 'LOCALIZATION_STATE'
    score_path = state_dir / 'LOCALIZATION_SCORE'
    try:
        score = float(score_path.read_text(encoding='utf-8').strip())
        state = state_path.read_text(encoding='utf-8').strip()
        age = max(now - state_path.stat().st_mtime,
                  now - score_path.stat().st_mtime)
    except (OSError, ValueError):
        return False
    return (0.0 <= score <= 1.0 and 0.0 <= age <= float(max_age) and
            state in {'LOCALIZED', 'UNLOCALIZED'})


def localization_ready(state_dir, minimum=0.80, max_age=2.5, now=None):
    """Require a fresh, validated localization before acquiring AUTONOMY."""
    state_dir = Path(state_dir)
    now = time.time() if now is None else float(now)
    state_path = state_dir / 'LOCALIZATION_STATE'
    score_path = state_dir / 'LOCALIZATION_SCORE'
    startup_path = state_dir / 'LOCALIZATION_STARTUP_STATE'
    try:
        state = state_path.read_text(encoding='utf-8').strip()
        score = float(score_path.read_text(encoding='utf-8').strip())
        startup = startup_path.read_text(encoding='utf-8').strip()
        age = max(now - state_path.stat().st_mtime,
                  now - score_path.stat().st_mtime)
    except (OSError, ValueError):
        return False
    return (startup == 'NAVIGATION_READY' and
            0.0 <= age <= float(max_age) and state == 'LOCALIZED' and
            score >= float(minimum))


class AutonomyCommandSource(Node):
    def __init__(self):
        super().__init__('lite3_autonomy_command_source')
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic', '/lite3/autonomy/cmd_vel')
        self.declare_parameter('state_dir', '/run/lite3-control')
        self.declare_parameter('command_timeout_s', 0.30)
        self.declare_parameter('startup_timeout_s', 2.0)
        self.declare_parameter('max_forward', 0.10)
        self.declare_parameter('max_lateral', 0.05)
        self.declare_parameter('max_yaw', 0.20)
        self.declare_parameter('minimum_localization', 0.80)
        self.declare_parameter('localization_max_age_s', 2.5)
        self.declare_parameter('relocalization_mode', False)

        self.core = AutonomyCommandCore(
            self.get_parameter('command_timeout_s').value,
            self.get_parameter('max_forward').value,
            self.get_parameter('max_lateral').value,
            self.get_parameter('max_yaw').value)
        self.startup_timeout_s = max(
            self.core.timeout_s,
            float(self.get_parameter('startup_timeout_s').value))
        state_dir = self.get_parameter('state_dir').value
        self.relocalization_mode = bool(
            self.get_parameter('relocalization_mode').value)
        max_age = self.get_parameter('localization_max_age_s').value
        if self.relocalization_mode:
            if os.environ.get('LITE3_RELOCALIZATION_APPROVED') != '1':
                raise RuntimeError(
                    'relocalization mode requires explicit operator approval')
            if not relocalization_inputs_ready(state_dir, max_age):
                raise RuntimeError(
                    'relocalization blocked: localization telemetry unavailable or stale')
        elif not localization_ready(
                state_dir,
                self.get_parameter('minimum_localization').value,
                max_age):
            raise RuntimeError(
                'AUTONOMY blocked: localization is unavailable, stale, or below 80%')
        # Construct every ROS entity before acquiring ownership. If systemd
        # stops us during slow DDS entity creation, no stale AUTONOMY marker
        # can be left by a partially constructed node.
        self.lease = CommandSourceLease(state_dir)
        self.started_at = time.monotonic()
        self.stop_requested = False
        output_topic = str(self.get_parameter('output_topic').value)
        input_topic = str(self.get_parameter('input_topic').value)
        self.publisher = self.create_publisher(
            Twist, output_topic, qos_profile_sensor_data)
        self.create_subscription(
            Twist, input_topic, self._on_command, qos_profile_sensor_data)
        self.create_timer(0.05, self._tick)
        if not self.lease.acquire_autonomy():
            raise RuntimeError(
                'AUTONOMY lease unavailable; another command source owns control')
        self.get_logger().info(
            'AUTONOMY lease acquired; waiting for fresh /cmd_vel. '
            'No Stand request is generated by this source.')

    def _on_command(self, msg):
        self.core.update(
            msg.linear.x, msg.linear.y, msg.angular.z, time.monotonic())

    def _publish(self, forward, lateral, yaw):
        message = Twist()
        message.linear.x = forward
        message.linear.y = lateral
        message.angular.z = yaw
        self.publisher.publish(message)

    def _tick(self):
        now = time.monotonic()
        output = self.core.output(now)
        if output.enabled:
            self._publish(output.forward, output.lateral, output.yaw)
            return
        self._publish(0.0, 0.0, 0.0)
        startup_expired = (
            output.reason == 'waiting' and
            now - self.started_at > self.startup_timeout_s)
        if output.reason in {'invalid', 'stale'} or startup_expired:
            self.get_logger().error(
                f'/cmd_vel {output.reason}; publishing zero and releasing AUTONOMY')
            self.lease.release()
            self.stop_requested = True

    def destroy_node(self):
        # SIGTERM can invalidate the ROS context before cleanup. A failed final
        # zero publish must never skip release of the command-source lease.
        try:
            self._publish(0.0, 0.0, 0.0)
        except Exception as exc:
            self.get_logger().warning(
                f'Final zero publish unavailable during shutdown: {exc}')
        finally:
            self.lease.release()
        return super().destroy_node()


def main():
    rclpy.init()
    node = AutonomyCommandSource()
    try:
        while rclpy.ok() and not node.stop_requested:
            rclpy.spin_once(node, timeout_sec=0.10)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
