"""No-motion profile: Nav2 outputs are isolated from every physical input."""
from pathlib import Path
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import LifecycleNode, Node


def generate_launch_description():
    root = Path(__file__).resolve().parents[2]
    package = root / "onboard_ros2_ws/src/sensor_visualization"
    params = str(package / "config/nav2_day2.yaml")
    tree = str(package / "config/navigate_to_pose_day2.xml")
    return LaunchDescription([
        LifecycleNode(package="nav2_controller", executable="controller_server",
                      name="controller_server", namespace="", output="screen", parameters=[params],
                      remappings=[("cmd_vel", "/autonomy_validation/cmd_vel")]),
        LifecycleNode(package="nav2_planner", executable="planner_server",
                      name="planner_server", namespace="", output="screen", parameters=[params]),
        LifecycleNode(package="nav2_bt_navigator", executable="bt_navigator",
                      name="bt_navigator", namespace="", output="screen",
                      parameters=[params, {"default_nav_to_pose_bt_xml": tree}],
                      remappings=[("goal_pose", "/autonomy_validation/disabled_goal_pose")]),
        Node(package="nav2_lifecycle_manager", executable="lifecycle_manager",
             name="lifecycle_manager_navigation", output="screen", parameters=[params]),
        ExecuteProcess(cmd=["/usr/bin/python3", str(package / "scripts/plan_from_rviz_goal.py")],
                       output="screen"),
    ])
