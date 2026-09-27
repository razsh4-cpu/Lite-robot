"""Launch only the RPLIDAR S2 driver and its LiDAR-only RViz view."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    lidar_share = get_package_share_directory('sllidar_ros2')
    visualization_share = get_package_share_directory('sensor_visualization')
    serial_port = LaunchConfiguration('serial_port')

    return LaunchDescription([
        DeclareLaunchArgument(
            'serial_port',
            default_value=(
                '/dev/serial/by-id/'
                'usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_'
                '68c991365a09ec11b1de4397cf41db95-if00-port0'
            ),
            description='Stable serial path for the RPLIDAR S2',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(lidar_share, 'launch', 'sllidar_s2_launch.py')
            ),
            launch_arguments={
                'serial_port': serial_port,
                'serial_baudrate': '1000000',
                'frame_id': 'laser',
                'scan_mode': 'DenseBoost',
            }.items(),
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='lite3_rplidar_rviz',
            arguments=['-d', os.path.join(
                visualization_share, 'rviz', 'lite3_rplidar_demo.rviz'
            )],
            output='screen',
        ),
    ])
