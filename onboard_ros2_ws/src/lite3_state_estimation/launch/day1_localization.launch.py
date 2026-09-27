import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node


def generate_launch_description():
    share = get_package_share_directory("lite3_state_estimation")
    map_yaml = LaunchConfiguration("map")
    pose_file = LaunchConfiguration("pose_file")
    minimum_match_fraction = LaunchConfiguration("minimum_match_fraction")
    return LaunchDescription([
        DeclareLaunchArgument(
            "map",
            default_value="/home/abx/ros2_ws/maps/room_map.yaml",
            description="Existing occupancy-map YAML; this launch never creates a map",
        ),
        DeclareLaunchArgument(
            "pose_file",
            default_value="/home/abx/.config/lite3/last_localized_pose.json",
            description="Per-map last validated AMCL startup hypothesis",
        ),
        DeclareLaunchArgument(
            "minimum_match_fraction", default_value="0.80",
            description="Minimum scan-to-map match required for LOCALIZED",
        ),
        LifecycleNode(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            namespace="",
            output="screen",
            parameters=[{"yaml_filename": map_yaml, "use_sim_time": False}],
        ),
        LifecycleNode(
            package="nav2_amcl",
            executable="amcl",
            name="amcl",
            namespace="",
            output="screen",
            parameters=[os.path.join(share, "config", "amcl.yaml")],
        ),
        Node(
            package="lite3_state_estimation",
            executable="localization_guard",
            name="lite3_localization_guard",
            output="screen",
            parameters=[{"pose_file": pose_file,
                         "minimum_match_fraction": minimum_match_fraction}],
        ),
    ])
