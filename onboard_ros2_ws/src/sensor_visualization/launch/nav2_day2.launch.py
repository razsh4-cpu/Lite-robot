"""Nav2 layer over the persistent Lite3 runtime and existing localization.

This launch does not start Map Server, AMCL, the robot transport, or the
AUTONOMY adapter. It cannot acquire motion ownership by itself.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable
from launch_ros.actions import LifecycleNode, Node


def generate_launch_description():
    share = get_package_share_directory("sensor_visualization")
    params = os.path.join(share, "config", "nav2_day2.yaml")
    safe_tree = os.path.join(share, "config", "navigate_to_pose_day2.xml")
    return LaunchDescription([
        SetEnvironmentVariable("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4"),
        LifecycleNode(
            package="nav2_controller", executable="controller_server",
            name="controller_server", namespace="", output="screen",
            parameters=[params],
            remappings=[("cmd_vel", "/cmd_vel")],
        ),
        LifecycleNode(
            package="nav2_planner", executable="planner_server",
            name="planner_server", namespace="", output="screen",
            parameters=[params],
        ),
        LifecycleNode(
            package="nav2_bt_navigator", executable="bt_navigator",
            name="bt_navigator", namespace="", output="screen",
            parameters=[params, {"default_nav_to_pose_bt_xml": safe_tree}],
        ),
        Node(
            package="nav2_lifecycle_manager", executable="lifecycle_manager",
            name="lifecycle_manager_navigation", output="screen",
            parameters=[params],
        ),
        # Safe path preview uses a private goal topic. /goal_pose is intentionally
        # avoided because BT Navigator can treat it as an execution request.
        Node(
            package="sensor_visualization", executable="plan_from_rviz_goal",
            name="plan_from_rviz_goal", output="screen",
        ),
    ])
