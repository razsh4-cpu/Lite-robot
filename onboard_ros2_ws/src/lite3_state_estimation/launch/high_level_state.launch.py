from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="lite3_state_estimation",
            executable="high_level_state_bridge",
            name="lite3_high_level_state_bridge",
            output="screen",
        )
    ])
