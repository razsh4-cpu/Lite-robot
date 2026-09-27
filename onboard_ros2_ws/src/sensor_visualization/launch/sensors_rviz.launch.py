from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    realsense_share = get_package_share_directory('realsense2_camera')
    sllidar_share = get_package_share_directory('sllidar_ros2')
    this_share = get_package_share_directory('sensor_visualization')
    start_rviz = LaunchConfiguration('start_rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'start_rviz', default_value='true',
            description='Start RViz on this machine. Set false on the robot when RViz runs on a laptop.'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            os.path.join(realsense_share, 'launch', 'rs_launch.py')),
            launch_arguments={'pointcloud.enable': 'true'}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            os.path.join(sllidar_share, 'launch', 'sllidar_s2_launch.py'))),
        # Temporary visualization-only transform. laser is the parent so SLAM
        # can publish map -> laser without conflicting TF parents. Measure and
        # calibrate this transform before using fused sensor data.
        Node(package='tf2_ros', executable='static_transform_publisher',
             arguments=['0', '0', '0', '0', '0', '0', 'laser', 'camera_link']),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', os.path.join(this_share, 'rviz', 'sensors.rviz')],
             condition=IfCondition(start_rviz),
             output='screen'),
    ])
