#!/usr/bin/env bash
set -eo pipefail
root="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
source /opt/ros/jazzy/setup.bash
source /home/abx/ros2_ws/install/setup.bash
source "$root/ros_ws/install/setup.bash"
export AMENT_PREFIX_PATH="$root/ros_ws/install/lite3_state_estimation:${AMENT_PREFIX_PATH:-}"
export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET FASTDDS_BUILTIN_TRANSPORTS=UDPv4
exec python3 "$root/onboard_ros2_ws/src/sensor_visualization/scripts/lite3_nav2_safety_monitor.py"
