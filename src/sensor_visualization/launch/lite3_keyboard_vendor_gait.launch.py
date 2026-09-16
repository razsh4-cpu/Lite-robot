"""Launch terminal keyboard teleop through the vendor-gait safety chain."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    transmit = LaunchConfiguration("transmit")
    return LaunchDescription(
        [
            DeclareLaunchArgument("transmit", default_value="false"),
            Node(
                package="sensor_visualization",
                executable="lite3_keyboard_cmd_vel",
                name="lite3_keyboard_cmd_vel",
                output="screen",
                emulate_tty=True,
                parameters=[{"forward": 0.10, "yaw": 0.25, "key_timeout_ms": 250}],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_cmd_vel_arbiter",
                name="lite3_cmd_vel_arbiter",
                output="screen",
                parameters=[{"timeout_ms": 300, "selected_source": "keyboard"}],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_cmd_vel_adapter",
                name="lite3_cmd_vel_adapter",
                output="screen",
                parameters=[{
                    "timeout_ms": 300,
                    "forward_normalized_per_mps": 1.0,
                    "yaw_normalized_per_radps": 1.0,
                    "max_forward_normalized": 0.10,
                    "max_yaw_normalized": 0.25,
                }],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_manual_axis_control",
                name="lite3_manual_axis_control",
                output="screen",
                parameters=[{
                    "transmit": transmit,
                    "timeout_ms": 300,
                    "max_forward": 0.10,
                    "max_yaw": 0.25,
                    "min_battery_percent": 25.0,
                }],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_control_logger",
                name="lite3_control_logger",
                output="screen",
                parameters=[{
                    "output_directory": "/home/abx/ros2_ws/logs",
                    "snapshot_hz": 10.0,
                }],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_operator_dashboard",
                name="lite3_operator_dashboard",
                output="screen",
            ),
        ]
    )
