"""Launch USB Xbox teleop through the proven Lite3 vendor-gait safety chain."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    transmit = LaunchConfiguration("transmit")
    device_id = LaunchConfiguration("device_id")
    enable_logger = LaunchConfiguration("enable_logger")
    enable_dashboard = LaunchConfiguration("enable_dashboard")
    log_directory = LaunchConfiguration("log_directory")
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "transmit",
                default_value="false",
                description="Enable verified UDP robot transmission (default: false)",
            ),
            DeclareLaunchArgument(
                "device_id",
                default_value="0",
                description="USB game-controller device index used by game_controller_node",
            ),
            DeclareLaunchArgument(
                "enable_logger",
                default_value="true",
                description="Write passive 10 Hz JSONL control snapshots",
            ),
            DeclareLaunchArgument(
                "log_directory",
                default_value="/home/abx/ros2_ws/logs",
            ),
            DeclareLaunchArgument("enable_dashboard", default_value="true"),
            Node(
                package="joy",
                executable="game_controller_node",
                name="game_controller_node",
                output="screen",
                parameters=[
                    {
                        "device_id": device_id,
                        "deadzone": 0.05,
                        "autorepeat_rate": 20.0,
                        "coalesce_interval_ms": 1,
                    }
                ],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_xbox_cmd_vel_teleop",
                name="lite3_xbox_cmd_vel_teleop",
                output="screen",
                parameters=[
                    {
                        "timeout_ms": 300,
                        "deadzone": 0.05,
                        "max_forward": 0.10,
                        "max_yaw": 0.25,
                        "cmd_vel_topic": "/lite3/xbox/cmd_vel",
                        "deadman_topic": "/lite3/xbox/deadman",
                    }
                ],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_cmd_vel_arbiter",
                name="lite3_cmd_vel_arbiter",
                output="screen",
                parameters=[{"timeout_ms": 300, "selected_source": "xbox"}],
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
                executable="lite3_control_logger",
                name="lite3_control_logger",
                output="screen",
                condition=IfCondition(enable_logger),
                parameters=[{"output_directory": log_directory, "snapshot_hz": 10.0}],
            ),
            Node(
                package="sensor_visualization",
                executable="lite3_operator_dashboard",
                name="lite3_operator_dashboard",
                output="screen",
                condition=IfCondition(enable_dashboard),
            ),
        ]
    )
