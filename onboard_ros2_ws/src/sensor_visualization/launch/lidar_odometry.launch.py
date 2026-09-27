"""Read-only 2D LiDAR odometry for the Lite3 RPLIDAR S2.

The scan is transformed from ``lidar_link`` into the robot-convention
``base_link`` frame using the static mount transform from LiDAR bringup.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    icp_odometry = Node(
        package='rtabmap_odom',
        executable='icp_odometry',
        name='lidar_icp_odometry',
        output='screen',
        parameters=[{
            # Scan-to-scan planar odometry only. No map is created or loaded.
            'frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'publish_tf': True,
            'scan_cloud_is_2d': True,
            'scan_downsampling_step': 1,
            # Exclude near-field self-returns and weak far-range returns. The
            # remaining indoor structure is used for scan matching.
            'scan_range_min': 0.20,
            'scan_range_max': 8.0,
            'scan_voxel_size': 0.03,
            # Conservative 2D ICP settings for slow, manually controlled
            # Lite3 motion. Each limit is deliberately below the old setting,
            # so a poor registration is rejected instead of becoming a jump.
            'Icp/PointToPlane': 'false',
            'Icp/Iterations': '30',
            'Icp/MaxCorrespondenceDistance': '0.15',
            'Icp/CorrespondenceRatio': '0.50',
            'Icp/OutlierRatio': '0.75',
            'Icp/MaxTranslation': '0.10',
            'Icp/MaxRotation': '0.175',
            'Icp/ReciprocalCorrespondences': 'true',
            'Icp/VoxelSize': '0.03',
            'Icp/RangeMin': '0.20',
            'Icp/RangeMax': '8.0',
            # This Jazzy build uses libpointmatcher (Icp/Strategy=1), so the
            # CC* settings are not selected. Keep scan deskewing off: the
            # RPLIDAR scan has no verified time-synchronised IMU/extrinsic
            # source available to this node.
            'Odom/Deskewing': 'false',
            # Use frame-to-frame ICP for this short validation. It avoids the
            # frame-to-map null-guess cascade observed after the prior loss
            # and lets the next real scan be evaluated independently.
            'Odom/Strategy': '1',
            # libpointmatcher requires a registration guess. This is only the
            # previous accepted ICP transform (not IMU/dead-reckoning); failed
            # matches remain explicit because null odometry is disabled.
            'Odom/GuessMotion': 'true',
            # A rejected registration makes the motion guess null. Recover
            # after three consecutive failed scans instead of remaining lost
            # indefinitely (the upstream default 0 disables auto-reset).
            'Odom/ResetCountdown': '3',
            'deskewing': False,
            # Do not emit a zero/null Odometry sample after a failed match;
            # consumers and the recorder can then detect the loss explicitly.
            'publish_null_when_lost': False,
        }],
        remappings=[('scan', '/scan'), ('odom', '/odom')],
    )

    return LaunchDescription([icp_odometry])
