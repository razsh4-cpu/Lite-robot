from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    share = get_package_share_directory('sensor_visualization')
    params = os.path.join(share, 'config', 'planner_only.yaml')
    return LaunchDescription([
        LifecycleNode(
            package='nav2_planner', executable='planner_server',
            name='planner_server', namespace='', output='screen',
            parameters=[params],
        ),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='planner_only_lifecycle_manager', output='screen',
            parameters=[{
                'use_sim_time': False,
                'autostart': True,
                'node_names': ['planner_server'],
            }],
        ),
        Node(
            package='sensor_visualization', executable='plan_from_rviz_goal',
            name='plan_from_rviz_goal', output='screen',
        ),
    ])
