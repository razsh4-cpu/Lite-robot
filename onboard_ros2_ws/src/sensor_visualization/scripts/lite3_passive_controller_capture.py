#!/usr/bin/env python3
"""Receive-only Lite3 Motion Host reference capture.

This utility binds UDP telemetry port 43897 and writes decoded RobotState,
HandleState, and JointState observations as JSON Lines.  It deliberately
creates no command socket and has no send/sendto call.
"""

import importlib.util
import argparse
import json
import socket
import struct
import sys
import time
import types
from pathlib import Path


PLUGIN_ROOT = Path('/home/abx/emos-plugin-lite3/lite3_plugin')
DEFAULT_OUTPUT = Path('/tmp/lite3_original_controller_capture.jsonl')


def load_codecs():
    package = types.ModuleType('_passive_lite3_capture')
    package.__path__ = [str(PLUGIN_ROOT)]
    sys.modules[package.__name__] = package
    for name in ('protocol', 'codecs'):
        spec = importlib.util.spec_from_file_location(
            f'{package.__name__}.{name}', PLUGIN_ROOT / f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    return (sys.modules[f'{package.__name__}.protocol'],
            sys.modules[f'{package.__name__}.codecs'])


def vector(value):
    return [float(item) for item in value]


def joint_positions(state):
    """Return all vendor JointState fields in their documented wire order."""
    return [float(getattr(state, name)) for name, _ctype in state._fields_]


def main():
    parser = argparse.ArgumentParser(description='Receive-only Lite3 telemetry capture')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT,
                        help='JSONL destination (default: %(default)s)')
    args = parser.parse_args()
    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    protocol, codecs = load_codecs()
    output_path.unlink(missing_ok=True)
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    receiver.bind(('0.0.0.0', 43897))
    receiver.settimeout(1.0)
    print(f'PASSIVE CAPTURE RECORDING: {output_path}', flush=True)

    with output_path.open('a', encoding='utf-8') as output:
        packet_sequence = 0
        while True:
            try:
                raw, source = receiver.recvfrom(4096)
            except socket.timeout:
                continue
            packet_sequence += 1
            entry = {
                'packet_sequence': packet_sequence,
                'timestamp_monotonic_s': round(time.monotonic(), 6),
                'timestamp_monotonic_ns': time.monotonic_ns(),
                'timestamp_unix_ns': time.time_ns(),
                'source_ip': source[0],
                'source_port': source[1],
                'packet_size': len(raw),
            }
            state = codecs.parse_robot_state(raw)
            if state is not None:
                entry.update({
                    'frame': 'RobotState',
                    'basic': int(state.robot_basic_state),
                    'gait': int(state.robot_gait_state),
                    'motion': int(state.robot_motion_state),
                    'status': codecs.describe_robot_status(state),
                    'body_velocity': vector(state.vel_body),
                    'world_velocity': vector(state.vel_world),
                    'battery_percent': float(state.battery_level),
                    'needs_balance_step': bool(state.is_robot_need_move),
                    # Capture every documented RobotState field.  The vendor
                    # marks the four placeholder fields below as invalid, so
                    # they are retained for comparison only, not interpreted.
                    'rpy_deg': vector(state.rpy),
                    'rpy_velocity_rad_s': vector(state.rpy_vel),
                    'acceleration_m_s2': vector(state.xyz_acc),
                    'world_pose': vector(state.pos_world),
                    'touch_down_and_stair_trot_raw': int(state.touch_down_and_stair_trot),
                    'is_charging_placeholder': bool(state.is_charging),
                    'error_state_placeholder': int(state.error_state),
                    'task_state_placeholder': int(state.task_state),
                    'zero_position_flag': bool(state.zero_position_flag),
                    'ultrasound_m': vector(state.ultrasound),
                })
                if len(raw) == protocol.ROBOT_STATE_WITH_POLICY_SIZE:
                    frame = protocol.RobotStateReceivedWithPolicy.from_buffer_copy(raw)
                    entry['robot_policy_state'] = int(frame.data.robot_policy_state)
            else:
                handle = codecs.parse_handle_state(raw)
                if handle is not None:
                    entry.update({
                        'frame': 'HandleState',
                        'left_axis_forward': float(handle.left_axis_forward),
                        'left_axis_side': float(handle.left_axis_side),
                        'right_axis_yaw': float(handle.right_axis_yaw),
                        'goal_vel_forward': float(handle.goal_vel_forward),
                        'goal_vel_side': float(handle.goal_vel_side),
                        'goal_vel_yaw': float(handle.goal_vel_yaw),
                    })
                elif (joint := codecs.parse_joint_state(raw)) is not None:
                    entry['frame'] = 'JointState'
                    entry['joint_names'] = list(codecs.JOINT_NAMES)
                    entry['joint_position_rad'] = joint_positions(joint)
                else:
                    entry['frame'] = 'Other'
                    # Preserve unrecognised vendor telemetry (including the
                    # MotionSDK RobotData stream) for strictly offline decode.
                    # This is receive-only evidence, not a command payload.
                    entry['packet_code_le'] = (
                        struct.unpack_from('<I', raw)[0] if len(raw) >= 4 else None)
                    entry['raw_packet_hex'] = raw.hex()
            output.write(json.dumps(entry, sort_keys=True) + '\n')
            output.flush()


if __name__ == '__main__':
    main()
