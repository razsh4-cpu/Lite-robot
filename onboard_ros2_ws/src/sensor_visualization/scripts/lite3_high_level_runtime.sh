#!/usr/bin/env bash
set -eo pipefail

readonly state_dir="${LITE3_STATE_DIR:-/run/lite3-control}"
readonly transmit="${LITE3_HIGH_LEVEL_TRANSMIT:-true}"
readonly zero_only="${LITE3_HIGH_LEVEL_ZERO_ONLY:-false}"
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"

mkdir -p "$state_dir"
[[ -e "$state_dir/COMMAND_SOURCE" ]] || printf 'NONE\n' >"$state_dir/COMMAND_SOURCE"
[[ -e "$state_dir/MANUAL_CONTROL_AVAILABLE" ]] || printf 'false\n' >"$state_dir/MANUAL_CONTROL_AVAILABLE"

source /opt/ros/jazzy/setup.bash
source /home/abx/ros2_ws/install/setup.bash
set -u
readonly watchdog="$(dirname "$0")/lite3_high_level_ros_watchdog"
if [[ -x "$watchdog" ]]; then
    "$watchdog" --parent-pid "$$" &
else
    echo "WARNING: HIGH-LEVEL ROS watchdog is not installed" >&2
fi
exec ros2 launch sensor_visualization lite3_high_level_runtime.launch.py \
    transmit:="$transmit" zero_only:="$zero_only"
