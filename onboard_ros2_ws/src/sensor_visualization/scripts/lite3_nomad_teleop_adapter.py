#!/usr/bin/env python3
"""MQTT TeleopIntent/v2 to the existing protected LAPTOP_XBOX Joy path."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import threading
import time

os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import paho.mqtt.client as mqtt
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

from lite3_command_source_lease import LaptopXboxLease
from lite3_nomad_teleop_core import PhysicalTeleopMachine, neutral_joy


def _mqtt_client(client_id):
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except (AttributeError, TypeError):
        return mqtt.Client(client_id=client_id)


def _decode(payload):
    if not isinstance(payload, (bytes, bytearray)) or len(payload) > 16 * 1024:
        raise ValueError("invalid payload")
    value = json.loads(bytes(payload).decode("utf-8"),
                       parse_constant=lambda value: (_ for _ in ()).throw(
                           ValueError(f"invalid constant {value}")))
    if not isinstance(value, dict):
        raise ValueError("payload must be an object")
    return value


class NomadTeleopAdapter(Node):
    def __init__(self, robot_id, client, state_dir="/run/lite3-control",
                 physical_output_enabled=False, clock=None):
        super().__init__("lite3_nomad_teleop_adapter")
        self.robot_id = robot_id
        self.client = client
        self.clock = clock or time.time
        self.machine = PhysicalTeleopMachine(
            robot_id, clock=self.clock,
            physical_output_enabled=physical_output_enabled)
        self.lease = LaptopXboxLease(state_dir)
        self.lease.recover_stale_own_marker()
        self.publisher = self.create_publisher(Joy, "/lite3/laptop_xbox/joy", 10)
        self.platform = None
        self.authority = None
        self.intent_topic = "control/platform_teleop"
        self.platform_topic = "device/robot_platform_status"
        self.authority_topic = "device/robot_control_authority"
        self.status_topic = "device/robot_teleop_status"
        self._mutex = threading.Lock()
        self._last_terminal = None
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.create_timer(0.05, self._tick)

    @staticmethod
    def _joy(frame):
        return Joy(axes=list(frame.axes), buttons=list(frame.buttons))

    def _owner_metadata(self):
        status = self.machine.status()
        return {
            "authority_id": status["authority_id"],
            "control_epoch": status["control_epoch"],
            "lease_generation": status["lease_generation"],
            "session_id": status["session_id"],
        }

    def _publish_status(self, status):
        status = dict(status)
        status["physical_output_performed"] = False
        self.client.publish(self.status_topic, json.dumps(status), qos=1, retain=True)
        return status

    def _apply(self, decision):
        status = dict(decision.status)
        if decision.acquire and self.lease.lock is None:
            try:
                acquired = self.lease.acquire(self._owner_metadata())
            except (OSError, ValueError):
                acquired = False
            if not acquired:
                status.update(state="BLOCKED", result="REJECTED",
                              reason="LAPTOP_XBOX_LEASE_DENIED")
                self.publisher.publish(self._joy(neutral_joy()))
                return self._publish_status(status)
        self.publisher.publish(self._joy(decision.joy))
        if decision.release:
            self.publisher.publish(self._joy(neutral_joy()))
            self.lease.release()
        return self._publish_status(status)

    def _on_connect(self, _client, _userdata, _flags, reason_code, _properties=None):
        if int(reason_code) != 0:
            return
        self.client.subscribe(self.intent_topic, qos=0)
        self.client.subscribe(self.platform_topic, qos=1)
        self.client.subscribe(self.authority_topic, qos=1)
        self._publish_status(self.machine.status())

    def _on_disconnect(self, *_args):
        with self._mutex:
            self.platform = None
            self.authority = None
            decision = self.machine.tick(None, None)
            self._apply(decision)
            self.publisher.publish(self._joy(neutral_joy()))
            self.lease.release()

    def _on_message(self, _client, _userdata, message):
        try:
            value = _decode(message.payload)
        except (UnicodeDecodeError, ValueError, TypeError, json.JSONDecodeError):
            return
        with self._mutex:
            if message.topic == self.platform_topic:
                if value.get("robot_id") == self.robot_id:
                    self.platform = value
                return
            if message.topic == self.authority_topic:
                if value.get("robot_id") == self.robot_id:
                    self.authority = value
                return
            if message.topic != self.intent_topic:
                return
            self._apply(self.machine.handle(value, self.platform, self.authority))

    def _tick(self):
        with self._mutex:
            decision = self.machine.tick(self.platform, self.authority)
            terminal = (decision.status["state"], decision.status["reason"])
            if decision.release or terminal != self._last_terminal:
                self._apply(decision)
            self._last_terminal = terminal

    def destroy_node(self):
        try:
            self.publisher.publish(self._joy(neutral_joy()))
            self.lease.release()
        finally:
            return super().destroy_node()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot-id", default="robodog_01")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1885)
    parser.add_argument("--state-dir", default="/run/lite3-control")
    parser.add_argument("--physical-output-enabled", choices=("true", "false"),
                        default="false")
    args = parser.parse_args(argv)
    enabled = args.physical_output_enabled == "true"
    client = _mqtt_client(f"lite3-nomad-teleop-{args.robot_id}")
    rclpy.init()
    node = NomadTeleopAdapter(args.robot_id, client, args.state_dir, enabled)
    client.will_set(node.status_topic, json.dumps({
        **node.machine.status(), "state": "OFFLINE", "result": "ZEROED",
        "reason": "ADAPTER_OFFLINE", "vx": 0.0, "vy": 0.0, "wz": 0.0,
        "physical_output_performed": False,
    }), qos=1, retain=True)
    client.connect(args.host, args.port, 60)
    client.loop_start()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        client.loop_stop()
        client.disconnect()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
