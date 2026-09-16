"""LiDAR-odometry calibration harness for the proven Lite3 /cmd_vel path.

The launch defaults to robot transmission disabled and uses the project LiDAR
bringup for the temporary measured base_link-to-lidar_link extrinsic.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    sensor_share = get_package_share_directory("sensor_visualization")
    transmit = LaunchConfiguration("transmit")
    serial_port = LaunchConfiguration("serial_port")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "transmit",
                default_value="false",
                description="Enable verified robot UDP transmission (default: false)",
            ),
            DeclareLaunchArgument(
                "serial_port",
                default_value=(
                    "/dev/serial/by-id/"
                    "usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_"
                    "68c991365a09ec11b1de4397cf41db95-if00-port0"
                ),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        sensor_share, "launch", "lite3_lidar_bringup.launch.py"
                    )
                ),
                launch_arguments={
                    "serial_port": serial_port,
                    "use_rviz": "false",
                    "publish_base_tf": "true",
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(sensor_share, "launch", "lidar_odometry.launch.py")
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        sensor_share, "launch", "lite3_cmd_vel_vendor_gait.launch.py"
                    )
                ),
                launch_arguments={"transmit": transmit}.items(),
            ),
            Node(
                package="sensor_visualization",
                executable="lidar_odom_motion_monitor",
                name="lite3_cmd_vel_calibration_monitor",
                output="screen",
            ),
        ]
    )
