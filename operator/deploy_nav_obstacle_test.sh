#!/usr/bin/env bash
# Deploy the built-in obstacle-test support. Never starts Nav2/AUTONOMY/motion.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd -- "$script_dir/.." && pwd)"
sensor="$repo/onboard_ros2_ws/src/sensor_visualization"
state="$repo/onboard_ros2_ws/src/lite3_state_estimation"
robot="${LITE3_ROBOT_SSH:-abx@192.168.2.32}"
remote_ws="/home/abx/Desktop/robotdog_ws"
remote_sensor="$remote_ws/src/src/sensor_visualization"
remote_state="$remote_ws/src/src/lite3_state_estimation"

host="$(ssh -o BatchMode=yes -o ConnectTimeout=5 "$robot" hostname)"
[[ "$host" == "abx-fit-001" ]] || {
  echo "WRONG TARGET: $host" >&2
  exit 2
}

source_value="$(ssh -o BatchMode=yes "$robot" \
  'cat /run/lite3-control/COMMAND_SOURCE 2>/dev/null || echo UNKNOWN')"
[[ "$source_value" == "NONE" ]] || {
  echo "DEPLOY BLOCKED — COMMAND_SOURCE=$source_value" >&2
  exit 3
}

ssh "$robot" "mkdir -p '$remote_sensor/scripts' '$remote_sensor/test' \
  '$remote_state/lite3_state_estimation'"
scp "$sensor/CMakeLists.txt" "$robot:$remote_sensor/CMakeLists.txt"
scp \
  "$sensor/scripts/lite3_nav_test_override.py" \
  "$sensor/scripts/lite3_localization_gate.py" \
  "$sensor/scripts/lite3_autonomy_command_source.py" \
  "$sensor/scripts/lite3_nav2_preflight.py" \
  "$sensor/scripts/lite3_nav2_safety_monitor.py" \
  "$sensor/scripts/lite3_release_autonomy.sh" \
  "$sensor/scripts/lite3_headless_admin.sh" \
  "$robot:$remote_sensor/scripts/"
scp "$sensor/test/test_nav_test_override.py" \
  "$robot:$remote_sensor/test/"
scp "$state/lite3_state_estimation/localization_guard.py" \
  "$robot:$remote_state/lite3_state_estimation/"

ssh -t "$robot" "set -e; \
  test \"\$(cat /run/lite3-control/COMMAND_SOURCE)\" = NONE; \
  cd '$remote_ws'; \
  source /opt/ros/jazzy/setup.bash; \
  colcon build --symlink-install --packages-select \
    lite3_state_estimation sensor_visualization; \
  '$remote_ws/install/sensor_visualization/lib/sensor_visualization/lite3_nav_test_override' clear; \
  sudo systemctl restart lite3-localization.service \
    lite3-nav2-safety-monitor.service; \
  test \"\$(cat /run/lite3-control/COMMAND_SOURCE)\" = NONE"

"$script_dir/install_nav_obstacle_cli.sh"
echo "OBSTACLE TEST DEPLOYED — NAV2/AUTONOMY NOT STARTED — MOTION SENT: NONE"
