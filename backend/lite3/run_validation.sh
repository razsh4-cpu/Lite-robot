#!/usr/bin/env bash
# Runs navigation only; never starts a robot runtime, AUTONOMY or a GUI.
set -eo pipefail
root="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
source /opt/ros/jazzy/setup.bash
source /home/abx/ros2_ws/install/setup.bash
source /home/abx/Desktop/robotdog_ws/install/setup.bash
source "$root/ros_ws/install/setup.bash"
# This existing ament_python package installs a resource marker but no AMENT
# prefix hook; preserve the established localization wrapper's explicit prefix.
export AMENT_PREFIX_PATH="$root/ros_ws/install/lite3_state_estimation:${AMENT_PREFIX_PATH:-}"
export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET FASTDDS_BUILTIN_TRANSPORTS=UDPv4
cd "$root"
source "$root/site.env"
python3 -m backend.lite3.validation_profile
scripts="$root/onboard_ros2_ws/src/sensor_visualization/scripts"
export LITE3_SKIP_ROS_ENV=true LITE3_INPUT_GATE_ROS_ENV=1
export LITE3_INPUT_GATE="$scripts/lite3_ros_inputs_ready.py"
export LITE3_LIFECYCLE_GATE="$scripts/lite3_localization_lifecycle_ready.py"
export LITE3_LOCALIZATION_LAUNCH="$root/backend/lite3/run_site_localization.sh"
pids=()
cleanup() { trap - EXIT INT TERM; for pid in "${pids[@]}"; do kill -INT "$pid" 2>/dev/null || true; done; wait || true; }
trap cleanup EXIT INT TERM
ros2 launch "$root/onboard_ros2_ws/src/sensor_visualization/launch/lite3_lidar_bringup.launch.py" use_rviz:=false &
pids+=("$!")
bash "$scripts/lite3_localization_supervisor.sh" &
pids+=("$!")
ros2 launch "$root/backend/lite3/validation_navigation.launch.py" &
pids+=("$!")
wait -n "${pids[@]}"
exit 1
