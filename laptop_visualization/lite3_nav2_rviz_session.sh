#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
set -u
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-SUBNET}"
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"
readonly root=/home/raz/ros-robot-cc/laptop_visualization
python3 "$root/lite3_robot_marker.py" &
marker_pid=$!
cleanup() {
  kill "$marker_pid" 2>/dev/null || true
  wait "$marker_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
rviz2 -d "$root/lite3_remote_lidar.rviz" --ros-args -r __node:=lite3_nav2_rviz &
rviz_pid=$!
wait "$rviz_pid"
