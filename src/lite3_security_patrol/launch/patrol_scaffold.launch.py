"""Launches only the ROS-only /cmd_vel normalizer; no Lite3 hardware bridge."""
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from os.path import join


def generate_launch_description():
    config = join(get_package_share_directory('lite3_security_patrol'), 'config', 'control_bridge.yaml')
    return LaunchDescription([
        Node(package='lite3_security_patrol', executable='cmd_vel_normalizer',
             name='lite3_cmd_vel_normalizer', parameters=[config], output='screen'),
    ])
