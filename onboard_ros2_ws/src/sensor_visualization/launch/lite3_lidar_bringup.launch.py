"""RPLIDAR S2 bringup with the project-standard ``lidar_link`` frame."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    lidar_share = get_package_share_directory("sllidar_ros2")
    project_share = get_package_share_directory("sensor_visualization")
    serial_port = LaunchConfiguration("serial_port")
    use_rviz = LaunchConfiguration("use_rviz")
    publish_base_tf = LaunchConfiguration("publish_base_tf")
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "serial_port",
                default_value=(
                    "/dev/serial/by-id/"
                    "usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_"
                    "68c991365a09ec11b1de4397cf41db95-if00-port0"
                ),
            ),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            DeclareLaunchArgument(
                "publish_base_tf",
                default_value="true",
                description="Publish the temporary base_link->lidar_link extrinsic",
            ),
            DeclareLaunchArgument("lidar_x", default_value="0.0"),
            DeclareLaunchArgument("lidar_y", default_value="0.0"),
            DeclareLaunchArgument("lidar_z", default_value="0.08"),
            DeclareLaunchArgument("lidar_roll", default_value="0.0"),
            DeclareLaunchArgument("lidar_pitch", default_value="0.0"),
            # Known physical forward motion appeared as -X when odometry was
            # expressed in lidar_link. Rotate the sensor frame by pi so the
            # robot convention is +X forward, +Y left and +Z up.
            DeclareLaunchArgument("lidar_yaw", default_value="3.141592653589793"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(lidar_share, "launch", "sllidar_s2_launch.py")
                ),
                launch_arguments={
                    "serial_port": serial_port,
                    "serial_baudrate": "1000000",
                    "frame_id": "lidar_link",
                    "scan_mode": "DenseBoost",
                }.items(),
            ),
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="base_to_lidar_tf",
                arguments=[
                    "--x", LaunchConfiguration("lidar_x"),
                    "--y", LaunchConfiguration("lidar_y"),
                    "--z", LaunchConfiguration("lidar_z"),
                    "--roll", LaunchConfiguration("lidar_roll"),
                    "--pitch", LaunchConfiguration("lidar_pitch"),
                    "--yaw", LaunchConfiguration("lidar_yaw"),
                    "--frame-id", "base_link",
                    "--child-frame-id", "lidar_link",
                ],
                condition=IfCondition(publish_base_tf),
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="lite3_lidar_rviz",
                arguments=[
                    "-d",
                    os.path.join(project_share, "rviz", "rplidar_s2_lidar_link.rviz"),
                ],
                output="screen",
                condition=IfCondition(use_rviz),
            ),
        ]
    )
