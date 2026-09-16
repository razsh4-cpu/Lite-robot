"""Safe ROS 2 stage: /cmd_vel -> normalized command topic only.

It intentionally does not invoke Lite3_rl_deploy or MotionSDK. A future,
separately reviewed bridge may consume /lite3/normalized_cmd_vel.
"""
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

from .velocity_mapping import CommandWatchdog, VelocityCommand, VelocityMapper, VelocityMappingConfig


class CmdVelNormalizer(Node):
    def __init__(self):
        super().__init__('lite3_cmd_vel_normalizer')
        self.declare_parameter('max_forward_mps', 0.0)
        self.declare_parameter('max_lateral_mps', 0.0)
        self.declare_parameter('max_yaw_radps', 0.0)
        self.declare_parameter('normalized_limit', 1.0)
        self.declare_parameter('command_timeout_sec', 0.3)
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic', '/lite3/normalized_cmd_vel')
        self.declare_parameter('publish_rate_hz', 20.0)

        config = VelocityMappingConfig(
            max_forward_mps=float(self.get_parameter('max_forward_mps').value),
            max_lateral_mps=float(self.get_parameter('max_lateral_mps').value),
            max_yaw_radps=float(self.get_parameter('max_yaw_radps').value),
            normalized_limit=float(self.get_parameter('normalized_limit').value),
            command_timeout_sec=float(self.get_parameter('command_timeout_sec').value),
        )
        self.mapper = VelocityMapper(config)
        self.watchdog = CommandWatchdog(config.command_timeout_sec)
        self.publisher = self.create_publisher(Twist, self.get_parameter('output_topic').value, 10)
        self.subscription = self.create_subscription(
            Twist, self.get_parameter('input_topic').value, self.on_cmd_vel, 10)
        rate = float(self.get_parameter('publish_rate_hz').value)
        self.timer = self.create_timer(1.0 / rate, self.publish_current)
        self.warned_uncalibrated = False
        if min(config.max_forward_mps, config.max_lateral_mps, config.max_yaw_radps) <= 0.0:
            self.get_logger().warning('Physical limits are UNCALIBRATED: normalized output is fail-safe zero.')
            self.warned_uncalibrated = True

    def on_cmd_vel(self, message: Twist) -> None:
        command = self.mapper.map_physical(message.linear.x, message.linear.y, message.angular.z)
        self.watchdog.update(command, time.monotonic())

    def publish_current(self) -> None:
        command = self.watchdog.current(time.monotonic())
        output = Twist()
        output.linear.x = command.forward
        output.linear.y = command.lateral
        output.angular.z = command.yaw
        self.publisher.publish(output)


def main() -> None:
    rclpy.init()
    node = CmdVelNormalizer()
    try:
        rclpy.spin(node)
    finally:
        # Publishing a final zero remains ROS-only; no robot transport exists here.
        node.publish_current()
        node.destroy_node()
        rclpy.shutdown()
