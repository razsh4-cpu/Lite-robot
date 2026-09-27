"""Saved-map localization using the verified Lite3 odometry/TF chain.

This launches map server and AMCL only. It launches no Nav2 controller or
motion node.
"""
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    share = get_package_share_directory('sensor_visualization')
    return LaunchDescription([
        LifecycleNode(
            package='nav2_map_server', executable='map_server', name='map_server', namespace='',
            output='screen', parameters=[{
                'yaml_filename': '/home/abx/ros2_ws/maps/room_map.yaml',
                'use_sim_time': False,
            }]),
        LifecycleNode(
            package='nav2_amcl', executable='amcl', name='amcl', namespace='', output='screen',
            parameters=[os.path.join(share, 'config', 'amcl_stationary.yaml'), {
                'base_frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'global_frame_id': 'map',
                'scan_topic': '/scan',
                'tf_broadcast': True,
            }]),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lidar_map_visualization_lifecycle_manager', output='screen',
            parameters=[{
                'use_sim_time': False,
                'autostart': True,
                'node_names': ['map_server', 'amcl'],
            }]),
    ])
