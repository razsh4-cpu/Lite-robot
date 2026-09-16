"""Passive Lite3 LiDAR + ICP + SLAM visualization.

This launch contains no robot-control node and never publishes ``/cmd_vel``.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("sensor_visualization")

    def include(name, arguments=None):
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(share, "launch", name)),
            launch_arguments=(arguments or {}).items(),
        )

    return LaunchDescription(
        [
            include(
                "lite3_lidar_bringup.launch.py",
                {"use_rviz": "false", "publish_base_tf": "true"},
            ),
            include("lidar_odometry.launch.py"),
            include("slam_mapping.launch.py"),
            Node(
                package="rviz2",
                executable="rviz2",
                name="lite3_lidar_slam_rviz",
                arguments=["-d", os.path.join(share, "rviz", "lite3_lidar_slam.rviz")],
                output="screen",
            ),
        ]
    )
