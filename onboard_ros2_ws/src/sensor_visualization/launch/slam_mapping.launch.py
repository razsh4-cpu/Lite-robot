from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('sensor_visualization'),
        'config', 'slam_toolbox_lidar_only.yaml')
    slam_share = get_package_share_directory('slam_toolbox')
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_share, 'launch', 'online_async_launch.py')),
            launch_arguments={
                'slam_params_file': config,
                'use_sim_time': 'false',
                'autostart': 'true',
            }.items()),
    ])
