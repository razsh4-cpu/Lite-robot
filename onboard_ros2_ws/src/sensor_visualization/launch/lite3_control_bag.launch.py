"""Record the Lite3 control/safety/odometry topics without starting control."""

from datetime import datetime

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    default_path = (
        "/home/abx/ros2_ws/bags/lite3_"
        + datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    output = LaunchConfiguration("output")
    return LaunchDescription(
        [
            DeclareLaunchArgument("output", default_value=default_path),
            ExecuteProcess(
                cmd=[
                    "ros2", "run", "sensor_visualization",
                    "lite3_bag_recorder", "--output", output,
                ],
                output="screen",
            ),
        ]
    )
