"""Local Xbox control through the proven Lite3 high-level Motion Host path."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    transmit = LaunchConfiguration("transmit")
    zero_only = LaunchConfiguration("zero_only")
    device_id = LaunchConfiguration("device_id")

    return LaunchDescription(
        [
            DeclareLaunchArgument("transmit", default_value="false"),
            DeclareLaunchArgument("zero_only", default_value="true"),
            DeclareLaunchArgument("device_id", default_value="0"),
            Node(
                package="joy",
                executable="game_controller_node",
                name="lite3_local_xbox_joy",
                output="screen",
                parameters=[{
                    "device_id": ParameterValue(device_id, value_type=int),
                    "deadzone": 0.05,
                    "autorepeat_rate": 20.0,
                    "coalesce_interval_ms": 1,
                }],
            ),
            Node(
                package="sensor_visualization",
                executable="xbox_lite3_motion_host_bridge",
                name="lite3_local_xbox_high_level",
                output="screen",
                parameters=[{
                    "transmit": ParameterValue(transmit, value_type=bool),
                    "zero_only": ParameterValue(zero_only, value_type=bool),
                    # Direct stick operation was requested after Stand. Freshness,
                    # centering, state-6 and telemetry gates remain mandatory.
                    "require_deadman": False,
                    "max_forward": 1.0,
                    "max_lateral": 1.0,
                    "max_yaw": 1.0,
                    "activate_after_stand": True,
                    "heartbeat_enabled": True,
                }],
            ),
        ]
    )
