from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node


def generate_launch_description():
    """Serve the saved occupancy map only; no SLAM or map updates occur here."""
    map_file = '/home/abx/ros2_ws/maps/room_map.yaml'
    return LaunchDescription([
        LifecycleNode(
            package='nav2_map_server', executable='map_server',
            name='map_server', namespace='', output='screen',
            parameters=[{'yaml_filename': map_file, 'use_sim_time': False}],
        ),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='map_server_lifecycle_manager', output='screen',
            parameters=[{
                'use_sim_time': False,
                'autostart': True,
                'node_names': ['map_server'],
            }],
        ),
    ])
