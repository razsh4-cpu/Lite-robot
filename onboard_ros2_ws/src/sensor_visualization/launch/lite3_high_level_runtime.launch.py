"""Persistent Lite3 Motion Host transport, telemetry and odometry runtime."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    transmit = LaunchConfiguration("transmit")
    zero_only = LaunchConfiguration("zero_only")
    return LaunchDescription([
        DeclareLaunchArgument("transmit", default_value="false"),
        DeclareLaunchArgument("zero_only", default_value="true"),
        Node(
            package="sensor_visualization",
            executable="xbox_lite3_motion_host_bridge",
            name="lite3_high_level_runtime",
            output="screen",
            parameters=[{
                "transmit": ParameterValue(transmit, value_type=bool),
                "zero_only": ParameterValue(zero_only, value_type=bool),
                "require_deadman": True,
                "max_forward": 1.0,
                "max_lateral": 1.0,
                "max_yaw": 1.0,
                "activate_after_stand": True,
                "heartbeat_enabled": True,
                "command_source_path": "/run/lite3-control/COMMAND_SOURCE",
            }],
        ),
    ])
