#!/usr/bin/env bash
set -eo pipefail

readonly config_dir="${LITE3_CONFIG_DIR:-/home/abx/.config/lite3}"
readonly maps_dir="${LITE3_MAPS_DIR:-/home/abx/ros2_ws/maps}"
readonly active_file="$config_dir/active_map_yaml"
readonly default_file="$config_dir/default_map"

if [[ -s "$active_file" ]]; then
    map_yaml="$(head -n 1 "$active_file")"
else
    map_name="$(head -n 1 "$default_file" 2>/dev/null || true)"
    [[ "$map_name" =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$ ]] || {
        echo "invalid or missing default map name" >&2; exit 2;
    }
    map_yaml="$maps_dir/$map_name/map.yaml"
fi
[[ "$map_yaml" == "$maps_dir"/* || "$map_yaml" == /home/abx/.local/state/lite3-maps/* ]] || {
    echo "map path outside managed roots: $map_yaml" >&2; exit 2;
}
[[ -r "$map_yaml" ]] || { echo "map yaml missing: $map_yaml" >&2; exit 2; }
pose_file="$(dirname "$map_yaml")/initial_pose.json"

source /opt/ros/jazzy/setup.bash
source /home/abx/Desktop/robotdog_ws/install/setup.bash
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
export AMENT_PREFIX_PATH="/home/abx/Desktop/robotdog_ws/install/lite3_state_estimation:${AMENT_PREFIX_PATH:-}"
source /home/abx/Desktop/robotdog_ws/install/lite3_state_estimation/share/lite3_state_estimation/package.bash
exec ros2 launch lite3_state_estimation day1_localization.launch.py \
    map:="$map_yaml" pose_file:="$pose_file" minimum_match_fraction:=0.80
