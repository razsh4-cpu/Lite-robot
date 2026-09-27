#!/usr/bin/env python3
"""Laptop/C2 single-robot Xbox publisher; never owns robot transport directly."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import time

os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")
import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool


class RobotRegistry:
    def __init__(self, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.robots = {entry["robot_id"]: entry for entry in data["robots"]}
        if len(self.robots) != len(data["robots"]):
            raise ValueError("robot_id values must be unique")

    def get(self, robot_id):
        if robot_id not in self.robots:
            raise KeyError(f"unknown robot_id: {robot_id}")
        return self.robots[robot_id]


class C2SelectionCore:
    def __init__(self, registry, selected=""):
        self.registry = registry
        self.selected = ""
        self.manual_enabled = False
        if selected:
            self.select(selected)

    def select(self, robot_id):
        self.registry.get(robot_id)
        previous = self.selected
        self.selected = robot_id
        self.manual_enabled = False
        return previous

    def enable_manual(self, enabled):
        if enabled and not self.selected:
            return False
        self.manual_enabled = bool(enabled)
        return True


class C2Xbox(Node):
    JOY_TIMEOUT_S = 0.30

    def __init__(self):
        super().__init__("lite3_c2_xbox")
        default_registry = str(Path(__file__).with_name("robots.json"))
        self.declare_parameter("registry", default_registry)
        self.declare_parameter("selected_robot", "")
        self.declare_parameter("manual_enabled", False)
        self.registry = RobotRegistry(self.get_parameter("registry").value)
        self.core = C2SelectionCore(
            self.registry, str(self.get_parameter("selected_robot").value))
        self.core.enable_manual(self.get_parameter("manual_enabled").value)
        self.last_joy = None
        self.last_joy_time = None
        # A disabled C2 source publishes one explicit release boundary, then
        # stays silent. Repeating false at 20 Hz would race a separate,
        # temporary posture client using the same guarded C2 relay.
        self._disabled_release_sent = False
        self._target_publishers = {}
        self.create_subscription(Joy, "/joy", self._on_joy, 10)
        self.create_timer(0.05, self._tick)
        self.add_on_set_parameters_callback(self._on_parameters)
        if self.core.selected:
            self._create_publishers(self.core.selected)
        self.get_logger().warning(
            "C2 Xbox starts manual_enabled=false unless explicitly requested; "
            "one selected robot only")

    def _topics(self, robot_id):
        prefix = f"/c2/{robot_id}/laptop_xbox"
        return prefix + "/joy", prefix + "/heartbeat", prefix + "/request"

    def _create_publishers(self, robot_id):
        joy, heartbeat, request = self._topics(robot_id)
        self._target_publishers[robot_id] = (
            self.create_publisher(Joy, joy, 10),
            self.create_publisher(Bool, heartbeat, 10),
            self.create_publisher(Bool, request, 10),
        )

    def _release(self, robot_id):
        if not robot_id or robot_id not in self._target_publishers:
            return
        joy_pub, heartbeat_pub, request_pub = self._target_publishers[robot_id]
        neutral = Joy(axes=[0.0] * 8, buttons=[0] * 15)
        for _ in range(3):
            joy_pub.publish(neutral)
            heartbeat_pub.publish(Bool(data=False))
            request_pub.publish(Bool(data=False))

    def _on_parameters(self, parameters):
        requested_robot = self.core.selected
        requested_manual = self.core.manual_enabled
        for parameter in parameters:
            if parameter.name == "selected_robot":
                requested_robot = str(parameter.value)
            elif parameter.name == "manual_enabled":
                requested_manual = bool(parameter.value)
        try:
            if requested_robot and requested_robot not in self.registry.robots:
                raise ValueError(f"unknown robot_id: {requested_robot}")
            if requested_robot != self.core.selected:
                previous = self.core.selected
                self._release(previous)
                self.core.select(requested_robot)
                if requested_robot not in self._target_publishers:
                    self._create_publishers(requested_robot)
                requested_manual = False
            if not self.core.enable_manual(requested_manual):
                raise ValueError("select a robot before enabling manual control")
        except ValueError as error:
            return SetParametersResult(successful=False, reason=str(error))
        return SetParametersResult(successful=True)

    def _on_joy(self, message):
        self.last_joy = copy.deepcopy(message)
        self.last_joy_time = time.monotonic()

    def _tick(self):
        robot_id = self.core.selected
        if not robot_id:
            return
        if not self.core.manual_enabled:
            if not self._disabled_release_sent:
                self._release(robot_id)
                self._disabled_release_sent = True
            return
        self._disabled_release_sent = False
        fresh = (self.last_joy_time is not None and
                 time.monotonic() - self.last_joy_time <= self.JOY_TIMEOUT_S)
        if not fresh:
            self._release(robot_id)
            return
        joy_pub, heartbeat_pub, request_pub = self._target_publishers[robot_id]
        joy_pub.publish(self.last_joy)
        heartbeat_pub.publish(Bool(data=True))
        request_pub.publish(Bool(data=True))

    def destroy_node(self):
        try:
            self._release(self.core.selected)
        finally:
            return super().destroy_node()


def main():
    rclpy.init()
    node = C2Xbox()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
