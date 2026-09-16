"""Launch the fail-closed /cmd_vel to Lite3 vendor-gait control chain."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    transmit = LaunchConfiguration("transmit")
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "transmit",
                default_value="false",
                description="Enable verified UDP robot transmission (default: false)",
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_manual_axis_control",
                name="lite3_manual_axis_control",
                output="screen",
                parameters=[
                    {
                        "transmit": transmit,
                        "timeout_ms": 300,
                        "max_forward": 0.10,
                        "max_yaw": 0.25,
                        "min_battery_percent": 25.0,
                    }
                ],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_cmd_vel_adapter",
                name="lite3_cmd_vel_adapter",
                output="screen",
                parameters=[
                    {
                        "timeout_ms": 300,
                        "forward_normalized_per_mps": 1.0,
                        "yaw_normalized_per_radps": 1.0,
                        "max_forward_normalized": 0.10,
                        "max_yaw_normalized": 0.25,
                    }
                ],
            ),
        ]
    )
