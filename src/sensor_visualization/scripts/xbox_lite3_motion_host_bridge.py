#!/usr/bin/env python3
"""Safety-gated Xbox to Lite3 Motion Host bridge.

Default operation is DRY-RUN: it subscribes to /joy and logs the exact
high-level Motion Host packets that would be emitted, but never sends UDP.
The Lite3 plugin's protocol.py and codecs.py are loaded directly, without
importing the EMOS/Sugarcoat plugin runtime.
"""

import ctypes
import importlib.util
import json
import math
from collections import deque
from pathlib import Path
import socket
import sys
import time
import types

import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import Joy


def load_motion_host_codecs(plugin_root: Path):
    """Load only protocol.py and codecs.py without executing lite3_plugin/__init__.py."""
    package_dir = plugin_root / 'lite3_plugin'
    protocol_path = package_dir / 'protocol.py'
    codecs_path = package_dir / 'codecs.py'
    if not protocol_path.is_file() or not codecs_path.is_file():
        raise FileNotFoundError(
            f'Expected protocol.py and codecs.py under {package_dir}')

    package_name = '_lite3_motion_host'
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_dir)]
    sys.modules[package_name] = package

    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f'Cannot load {path}')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    protocol = load(f'{package_name}.protocol', protocol_path)
    codecs = load(f'{package_name}.codecs', codecs_path)
    return protocol, codecs


class DiagnosticCapture:
    """Bounded, passive event recorder for one forward-stick test.

    This class only records dictionaries supplied by the bridge.  It never
    owns a socket and cannot generate or transmit a robot packet.
    """

    def __init__(self, path: Path, pre_s=1.0, post_s=1.5):
        self.path = path
        self.pre_s = pre_s
        self.post_s = post_s
        self.history = deque()
        self.samples = []
        self.active = False
        self.complete = False
        self._end_after = None

    def observe(self, sample, trigger):
        if self.complete:
            return False
        now = sample['timestamp_monotonic_s']
        self.history.append(sample)
        while self.history and now - self.history[0]['timestamp_monotonic_s'] > self.pre_s:
            self.history.popleft()

        if trigger and not self.active:
            self.active = True
            self.samples = list(self.history)
            self._end_after = None
        elif self.active:
            self.samples.append(sample)

        if not self.active:
            return False
        if trigger:
            self._end_after = None
            return False
        if self._end_after is None:
            self._end_after = now + self.post_s
        if now < self._end_after:
            return False

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as output:
            for entry in self.samples:
                output.write(json.dumps(entry, sort_keys=True) + '\n')
        self.complete = True
        return True


class XboxLite3MotionHostBridge(Node):
    """Map verified Xbox /joy inputs to high-level Lite3 Motion Host packets."""

    AXIS_LATERAL = 0
    AXIS_FORWARD = 1
    AXIS_YAW = 2
    BUTTON_STAND = 0  # A: vendor SIT_STAND toggle, not state-aware stand
    DEADZONE = 0.05
    # Hard first-motion-test limits.  These are applied after deadzone
    # rescaling, so no valid /joy input can produce a larger command.
    MAX_FORWARD = 0.10
    MAX_LATERAL = 0.10
    MAX_YAW = 0.10
    # Absolute cap for the explicitly requested, temporary forward-magnitude
    # test. The normal parameter default remains MAX_FORWARD (0.10).
    TEST_MAX_FORWARD = 0.30
    JOY_TIMEOUT_S = 0.300
    TELEMETRY_TIMEOUT_S = 1.000
    HEARTBEAT_PERIOD_S = 0.250  # 4 Hz
    COMMAND_PERIOD_S = 0.050  # 20 Hz
    TELEMETRY_PERIOD_S = 0.020  # 50 Hz passive status check
    STANDING_BASIC_STATE = 6  # Lite3 RobotState: torque-control standing

    def __init__(self):
        super().__init__('xbox_lite3_motion_host_bridge')
        self.declare_parameter('transmit', False)
        # This is deliberately default-on.  It is a test interlock, not a
        # speed limiter: while true, no joystick input can produce non-zero
        # velocity bytes on the network.
        self.declare_parameter('zero_only', True)
        self.declare_parameter('robot_ip', '192.168.1.120')
        self.declare_parameter('command_port', 43893)
        self.declare_parameter('telemetry_port', 43897)
        self.declare_parameter('max_forward', self.MAX_FORWARD)
        self.declare_parameter('max_lateral', self.MAX_LATERAL)
        self.declare_parameter('max_yaw', self.MAX_YAW)
        self.declare_parameter('plugin_root', '/home/abx/emos-plugin-lite3')
        self.declare_parameter('diagnostic_capture', False)
        # Runtime one-shot capture arm. Set false, then true, to arm each
        # additional capture without restarting the bridge.
        self.declare_parameter('diagnostic_capture_armed', False)
        self.declare_parameter('diagnostic_log_path',
                               '/tmp/lite3_forward_diagnostic.jsonl')
        # Experimental interlock: when false, a confirmed stand never causes
        # the normal MOVE/MANUAL reactivation.  It changes no packet encoding
        # and defaults to the established production behavior.
        self.declare_parameter('activate_after_stand', True)
        # Heartbeat interruption is unsafe for ordinary debugging: the Lite3
        # sits when the Motion Host heartbeat expires.  It is therefore only
        # permitted in an explicitly requested heartbeat-loss experiment.
        self.declare_parameter('heartbeat_enabled', True)
        self.declare_parameter('heartbeat_loss_test', False)

        self.transmit = bool(self.get_parameter('transmit').value)
        self.zero_only = bool(self.get_parameter('zero_only').value)
        self.robot_ip = str(self.get_parameter('robot_ip').value)
        self.command_port = int(self.get_parameter('command_port').value)
        self.telemetry_port = int(self.get_parameter('telemetry_port').value)
        self.max_forward = min(self.TEST_MAX_FORWARD,
                               max(0.0, float(self.get_parameter('max_forward').value)))
        self.max_lateral = min(self.MAX_LATERAL, max(0.0, float(self.get_parameter('max_lateral').value)))
        self.max_yaw = min(self.MAX_YAW, max(0.0, float(self.get_parameter('max_yaw').value)))
        self.diagnostic_log_path = Path(str(
            self.get_parameter('diagnostic_log_path').value))
        self.diagnostic_capture = None
        self._diagnostic_capture_armed = False
        # Keep the original startup parameter as a compatible shorthand, but
        # ordinary use should arm the runtime parameter after startup.
        if bool(self.get_parameter('diagnostic_capture').value) or bool(
                self.get_parameter('diagnostic_capture_armed').value):
            self._arm_diagnostic_capture()
        self.activate_after_stand = bool(
            self.get_parameter('activate_after_stand').value)
        self.heartbeat_enabled = bool(
            self.get_parameter('heartbeat_enabled').value)
        self.heartbeat_loss_test = bool(
            self.get_parameter('heartbeat_loss_test').value)
        if not self.heartbeat_enabled and not self.heartbeat_loss_test:
            raise ValueError(
                'heartbeat_enabled=false requires heartbeat_loss_test=true')
        plugin_root = Path(str(self.get_parameter('plugin_root').value)).expanduser()
        self.protocol, self.codecs = load_motion_host_codecs(plugin_root)
        self.codes = self.protocol.CommandCode
        self._validate_protocol()

        self._last_joy_time = None
        self._last_values = (0.0, 0.0, 0.0)
        self._last_raw_axes = (0.0, 0.0, 0.0)
        self._last_a_pressed = False
        self._stand_pending = False
        self._motion_locked_after_stand = False
        # Start locked. Only a fresh vendor standing-state telemetry frame can
        # make the external drive mode ready.
        self._awaiting_standing = True
        self._drive_reactivation_pending = False
        self._drive_ready = False
        self._robot_basic_state = None
        self._last_robot_status = 'unknown'
        self._last_robot_state = None
        self._last_robot_state_time = None
        self._last_robot_state_tuple = None
        self._invalid_joy = False
        self._was_enabled = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._target = (self.robot_ip, self.command_port)
        self._telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._telemetry_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._telemetry_socket.bind(('0.0.0.0', self.telemetry_port))
        self._telemetry_socket.setblocking(False)

        self.create_subscription(Joy, '/joy', self._on_joy, 10)
        self.create_timer(self.COMMAND_PERIOD_S, self._command_tick)
        self.create_timer(self.HEARTBEAT_PERIOD_S, self._heartbeat_tick)
        self.create_timer(self.TELEMETRY_PERIOD_S, self._telemetry_tick)
        self.create_timer(0.5, self._status_tick)
        self.add_on_set_parameters_callback(self._on_set_parameters)

        mode = 'TRANSMIT ENABLED' if self.transmit else 'DRY-RUN ONLY'
        self.get_logger().warn(
            f'{mode}: target={self.robot_ip}:{self.command_port}; '
            f'zero_only={str(self.zero_only).lower()}.')
        if not self.transmit:
            self.get_logger().info(
                'DRY-RUN: no UDP packets or control-mode packets will be sent. '
                'Waiting for standing telemetry before drive-ready.')

    def _on_set_parameters(self, parameters):
        proposed_enabled = self.heartbeat_enabled
        proposed_loss_test = self.heartbeat_loss_test
        proposed_log_path = self.diagnostic_log_path
        requested_capture_arm = None
        for parameter in parameters:
            if parameter.name == 'heartbeat_enabled':
                proposed_enabled = bool(parameter.value)
            elif parameter.name == 'heartbeat_loss_test':
                proposed_loss_test = bool(parameter.value)
            elif parameter.name == 'diagnostic_log_path':
                proposed_log_path = Path(str(parameter.value))
            elif parameter.name == 'diagnostic_capture_armed':
                requested_capture_arm = bool(parameter.value)
        if not proposed_enabled and not proposed_loss_test:
            return SetParametersResult(
                successful=False,
                reason='heartbeat_enabled=false requires heartbeat_loss_test=true')
        self.heartbeat_enabled = proposed_enabled
        self.heartbeat_loss_test = proposed_loss_test
        self.diagnostic_log_path = proposed_log_path
        if not self.heartbeat_enabled:
            self.get_logger().warn(
                'Heartbeat transmission disabled for explicit heartbeat-loss test; '
                'bridge remains alive.')
        if requested_capture_arm is False:
            self.diagnostic_capture = None
            self._diagnostic_capture_armed = False
            self.get_logger().info('Diagnostic capture disarmed.')
        elif requested_capture_arm is True:
            self._arm_diagnostic_capture()
        return SetParametersResult(successful=True)

    def _arm_diagnostic_capture(self):
        """Arm one local recorder; this has no control or heartbeat effect."""
        self.diagnostic_capture = DiagnosticCapture(self.diagnostic_log_path)
        self._diagnostic_capture_armed = True
        self.get_logger().info(
            f'Diagnostic capture armed: {self.diagnostic_log_path}. '
            'Heartbeat and motion behavior are unchanged.')

    def _validate_protocol(self):
        expected = {
            'VEL_FORWARD': 320,
            'VEL_LATERAL': 325,
            'VEL_YAW': 321,
            'HEARTBEAT': 0x21040001,
            'MODE_MOVE': 0x21010D06,
            'MODE_POSE': 0x21010D05,
            'CONTROL_MANUAL': 0x21010C02,
            'CONTROL_NAVIGATION': 0x21010C03,
            'SIT_STAND': 0x21010202,
        }
        for name, value in expected.items():
            actual = getattr(self.codes, name)
            if actual != value:
                raise RuntimeError(f'Protocol validation failed: {name}={actual}, expected {value}')
        self.simple_size = ctypes.sizeof(self.protocol.SimpleCMD)
        self.complex_size = ctypes.sizeof(self.protocol.ComplexCMD)
        self.get_logger().info(
            'Validated Motion Host protocol: '
            f'VEL_FORWARD={self.codes.VEL_FORWARD}, '
            f'VEL_LATERAL={self.codes.VEL_LATERAL}, '
            f'VEL_YAW={self.codes.VEL_YAW}, '
            f'HEARTBEAT=0x{self.codes.HEARTBEAT:08X}; '
            f'MODE_MOVE=0x{self.codes.MODE_MOVE:08X}, '
            f'MODE_POSE=0x{self.codes.MODE_POSE:08X}, '
            f'CONTROL_MANUAL=0x{self.codes.CONTROL_MANUAL:08X}, '
            f'CONTROL_NAVIGATION=0x{self.codes.CONTROL_NAVIGATION:08X} (blocked), '
            f'SIT_STAND=0x{self.codes.SIT_STAND:08X}; '
            f'SimpleCMD={self.simple_size} bytes ComplexCMD={self.complex_size} bytes')

    @classmethod
    def _shape_axis(cls, value):
        if not math.isfinite(value):
            return 0.0
        value = max(-1.0, min(1.0, float(value)))
        magnitude = abs(value)
        if magnitude <= cls.DEADZONE:
            return 0.0
        return math.copysign(
            min(1.0, (magnitude - cls.DEADZONE) / (1.0 - cls.DEADZONE)), value)

    def _limit_motion(self, forward, lateral, yaw):
        """Apply non-bypassable first-test limits to shaped joystick input."""
        return (
            max(-self.max_forward, min(self.max_forward, forward)),
            max(-self.max_lateral, min(self.max_lateral, lateral)),
            max(-self.max_yaw, min(self.max_yaw, yaw)),
        )

    def _on_joy(self, msg):
        max_axis = max(self.AXIS_LATERAL, self.AXIS_FORWARD, self.AXIS_YAW)
        if len(msg.axes) <= max_axis or len(msg.buttons) <= self.BUTTON_STAND:
            self._invalid_joy = True
            self._last_joy_time = None
            self._last_values = (0.0, 0.0, 0.0)
            return
        raw = (msg.axes[self.AXIS_FORWARD], msg.axes[self.AXIS_LATERAL],
               msg.axes[self.AXIS_YAW])
        if not all(math.isfinite(value) for value in raw):
            self._invalid_joy = True
            self._last_joy_time = None
            self._last_values = (0.0, 0.0, 0.0)
            return
        self._invalid_joy = False
        self._last_joy_time = time.monotonic()
        a_pressed = bool(msg.buttons[self.BUTTON_STAND])
        if a_pressed and not self._last_a_pressed:
            self._stand_pending = True
            # A pose transition must not be followed by an accidental velocity
            # command. Fresh standing telemetry must re-arm driving.
            self._motion_locked_after_stand = True
            self._drive_ready = False
        self._last_a_pressed = a_pressed
        self._last_values = tuple(self._shape_axis(value) for value in raw)
        self._last_raw_axes = tuple(float(value) for value in raw)

    def _state(self):
        stale = (self._last_joy_time is None or
                 time.monotonic() - self._last_joy_time > self.JOY_TIMEOUT_S)
        telemetry_stale = (self._last_robot_state_time is None or
                           time.monotonic() - self._last_robot_state_time
                           > self.TELEMETRY_TIMEOUT_S)
        enabled = (not stale and not telemetry_stale and not self._invalid_joy and self._drive_ready and
                   self._robot_basic_state == self.STANDING_BASIC_STATE and
                   not self._motion_locked_after_stand)
        if not enabled:
            return False, 0.0, 0.0, 0.0
        return True, *self._limit_motion(*self._last_values)

    def _emit(self, packet, description):
        if self.transmit:
            self._socket.sendto(packet, self._target)
            self.get_logger().info(f'TX {description} size={len(packet)} target={self._target}')

    def _emit_velocity(self, vx, vy, wz):
        if self.zero_only:
            vx = vy = wz = 0.0
        packets = self.codecs.encode_velocity(vx, vy, wz)
        details = (
            (self.codes.VEL_FORWARD, vx),
            (self.codes.VEL_LATERAL, vy),
            (self.codes.VEL_YAW, -wz),  # on-wire Motion Host yaw convention
        )
        # DRY-RUN still creates and validates the packets, but intentionally
        # does not call sendto().  Their full description is printed at the
        # human-readable status rate below.
        if self.transmit:
            for packet, (code, wire_value) in zip(packets, details):
                # Per-packet zero logs are intentionally suppressed: the
                # diagnostic recorder below preserves the useful bounded
                # event window without flooding the terminal.
                self._socket.sendto(packet, self._target)
                if any(abs(value) > 0.0 for value in (vx, vy, wz)):
                    self.get_logger().info(
                        f'TX ComplexCMD code={code} data={wire_value:+.3f} '
                        f'size={len(packet)} target={self._target}')

    def _activate_motion_host(self):
        """Enter MOVE/MANUAL at rest before normal Twist velocity streaming."""
        self.get_logger().warn(
            'Motion Host activation: MODE_MOVE -> CONTROL_MANUAL -> '
            'zero velocity triplet. '
            'CONTROL_NAVIGATION is intentionally not sent: the vendor plugin '
            'reserves it for the onboard navigation/autonomous source.')
        self._emit(self.codecs.encode_simple_cmd(self.codes.MODE_MOVE),
                   f'SimpleCMD MODE_MOVE code=0x{self.codes.MODE_MOVE:08X}')
        self._emit(self.codecs.encode_simple_cmd(self.codes.CONTROL_MANUAL),
                   f'SimpleCMD CONTROL_MANUAL code=0x{self.codes.CONTROL_MANUAL:08X}')
        self._emit_velocity(0.0, 0.0, 0.0)

    def _send_sit_stand_toggle(self):
        """Send one vendor sit/stand toggle, never a repeated held-button action."""
        pose_packet = self.codecs.encode_simple_cmd(self.codes.MODE_POSE)
        stand_packet = self.codecs.encode_simple_cmd(self.codes.SIT_STAND)
        self._awaiting_standing = True
        if self.transmit:
            self.get_logger().warn(
                'A rising edge: forcing zero velocity, then MODE_POSE and the '
                'vendor SIT_STAND toggle. Movement remains locked until standing telemetry.')
            self._emit_velocity(0.0, 0.0, 0.0)
            self._emit(pose_packet,
                       f'SimpleCMD MODE_POSE code=0x{self.codes.MODE_POSE:08X}')
            self._emit(stand_packet,
                       f'SimpleCMD SIT_STAND (toggle) code=0x{self.codes.SIT_STAND:08X}')
        else:
            self.get_logger().info(
                'DRY-RUN A rising edge: would send zero velocity triplet, '
                f'SimpleCMD MODE_POSE code=0x{self.codes.MODE_POSE:08X} size={len(pose_packet)}, '
                f'SimpleCMD SIT_STAND (toggle) code=0x{self.codes.SIT_STAND:08X} '
                f'size={len(stand_packet)}; no UDP transmission.')

    def _observe_robot_state(self, state):
        """Update the sit/stand state machine from a decoded vendor RobotState."""
        status = self.codecs.describe_robot_status(state)
        self._last_robot_status = status
        self._robot_basic_state = state.robot_basic_state
        self._last_robot_state = state
        self._last_robot_state_time = time.monotonic()
        state_tuple = (state.robot_basic_state, state.robot_gait_state,
                       state.robot_motion_state)
        if state_tuple != self._last_robot_state_tuple:
            self._last_robot_state_tuple = state_tuple
            self.get_logger().info(
                'Telemetry state tuple: '
                f'basic/gait/motion={state_tuple[0]}/{state_tuple[1]}/{state_tuple[2]} '
                f'status={status}')
        # Any state other than the vendor's explicit standing state locks
        # velocity immediately; no pose/IMU/velocity inference is allowed.
        if state.robot_basic_state != self.STANDING_BASIC_STATE:
            self._drive_ready = False
            return
        # The vendor decoder maps basic state 6 to the explicit "standing"
        # status. Do not infer standing from pose, IMU, or velocity fields.
        if (self._awaiting_standing and not self._drive_reactivation_pending
                and self.activate_after_stand):
            self._awaiting_standing = False
            self._drive_reactivation_pending = True
            self.get_logger().info(
                'Telemetry confirmed standing: robot_basic_state=6 status=standing. '
                'Scheduling MOVE/MANUAL reactivation at zero velocity.')
        elif self._awaiting_standing and not self.activate_after_stand:
            self._awaiting_standing = False
            self.get_logger().warn(
                'Telemetry confirmed standing: MODE_MOVE/CONTROL_MANUAL are '
                'intentionally suppressed for this zero-velocity experiment.')

    def _telemetry_tick(self):
        while True:
            try:
                raw, _ = self._telemetry_socket.recvfrom(4096)
            except BlockingIOError:
                return
            state = self.codecs.parse_robot_state(raw)
            if state is not None:
                self._observe_robot_state(state)

    @staticmethod
    def _vector(value):
        if value is None:
            return None
        try:
            return [float(component) for component in value]
        except TypeError:
            return None

    def _diagnostic_sample(self, vx, vy, wz):
        state = self._last_robot_state
        return {
            'timestamp_monotonic_s': round(time.monotonic(), 6),
            'raw_axes_1_forward': self._last_raw_axes[0],
            'processed_forward': self._last_values[0],
            'final_vx': vx,
            'final_vy': vy,
            'final_wz': wz,
            'standing_gate': self._robot_basic_state == self.STANDING_BASIC_STATE,
            'drive_ready': self._drive_ready,
            'vel_forward_transmitted': vx if self.transmit else None,
            'robot_basic_state': getattr(state, 'robot_basic_state', None),
            'robot_gait_state': getattr(state, 'robot_gait_state', None),
            'robot_motion_state': getattr(state, 'robot_motion_state', None),
            'body_velocity': self._vector(getattr(state, 'vel_body', None)),
            'world_velocity': self._vector(getattr(state, 'vel_world', None)),
        }

    def _command_tick(self):
        if self._stand_pending:
            self._stand_pending = False
            self._send_sit_stand_toggle()
            return
        if self._drive_reactivation_pending:
            self._drive_reactivation_pending = False
            self._motion_locked_after_stand = False
            self._activate_motion_host()
            self._drive_ready = True
            return
        enabled, vx, vy, wz = self._state()
        moving = (enabled and not self.zero_only and not self._motion_locked_after_stand
                  and any(abs(value) > 0.0 for value in (vx, vy, wz)))
        if moving:
            self._emit_velocity(vx, vy, wz)
        else:
            # Centered, stale, malformed, sitting, or otherwise locked input:
            # normal Twist behavior is a zero velocity triplet only.
            self._emit_velocity(0.0, 0.0, 0.0)
        if self.diagnostic_capture is not None:
            # Trigger solely on the requested raw forward-stick threshold;
            # capture observation never changes the command decision above.
            trigger = abs(self._last_raw_axes[0]) > self.DEADZONE
            if self.diagnostic_capture.observe(
                    self._diagnostic_sample(vx if moving else 0.0,
                                            vy if moving else 0.0,
                                            wz if moving else 0.0), trigger):
                self.get_logger().info(
                    f'Diagnostic capture saved: {self.diagnostic_capture.path}')
                self._diagnostic_capture_armed = False
        self._was_enabled = moving

    def _heartbeat_tick(self):
        heartbeat = self.codecs.encode_heartbeat()
        if self.transmit and self.heartbeat_enabled:
            self._emit(heartbeat,
                       f'SimpleCMD code=0x{self.codes.HEARTBEAT:08X} heartbeat@4Hz')

    def _status_tick(self):
        enabled, vx, vy, wz = self._state()
        if self.zero_only:
            vx = vy = wz = 0.0
        self.get_logger().info(
            f'enabled={str(enabled).lower()} forward={vx:.2f} lateral={vy:.2f} yaw={wz:.2f} '
            f'transmit={str(self.transmit).lower()} zero_only={str(self.zero_only).lower()} '
            f'robot_status={self._last_robot_status} '
            f'telemetry_fresh={str(self._last_robot_state_time is not None and time.monotonic() - self._last_robot_state_time <= self.TELEMETRY_TIMEOUT_S).lower()} '
            f'diagnostic_armed={str(self._diagnostic_capture_armed).lower()} '
            f'waiting_for_standing={str(self._awaiting_standing).lower()} '
            f'drive_ready={str(self._drive_ready).lower()}')
        if not self.transmit:
            self.get_logger().info(
                'DRY-RUN packet plan: @20Hz ComplexCMD '
                f'code={self.codes.VEL_FORWARD} forward={vx:+.3f} ({self.complex_size}B), '
                f'code={self.codes.VEL_LATERAL} lateral={vy:+.3f} ({self.complex_size}B), '
                f'code={self.codes.VEL_YAW} wire_yaw={-wz:+.3f} ({self.complex_size}B); '
                f'@4Hz SimpleCMD code=0x{self.codes.HEARTBEAT:08X} ({self.simple_size}B). '
                f'No UDP transmission to {self._target}.')

    def destroy_node(self):
        # In transmit mode this causes an explicit zero-Twist shutdown;
        # in dry-run it is logged only. No pose or control-mode changes are sent.
        try:
            self._emit_velocity(0.0, 0.0, 0.0)
            self.get_logger().info(
                'Shutdown: zero high-level velocity requested.')
        finally:
            self._socket.close()
            self._telemetry_socket.close()
        return super().destroy_node()


def main():
    rclpy.init()
    node = XboxLite3MotionHostBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
