"""Optional local Xbox input only; owns no Lite3 UDP sockets."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    device_id = LaunchConfiguration("device_id")
    return LaunchDescription([
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
    ])
