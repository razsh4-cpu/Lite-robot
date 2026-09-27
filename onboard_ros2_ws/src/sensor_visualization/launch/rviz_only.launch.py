from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    """Start RViz only; use this on a laptop connected to the robot ROS domain."""
    this_share = get_package_share_directory('sensor_visualization')
    return LaunchDescription([
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', os.path.join(this_share, 'rviz', 'sensors.rviz')],
             output='screen'),
    ])
