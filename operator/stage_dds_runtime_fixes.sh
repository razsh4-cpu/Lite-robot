#!/usr/bin/env bash
# Stage and build the prepared DDS/runtime fixes on the Lite3 Mini-PC.
#
# No sudo is used, no service is changed, and no robot command is published.
set -euo pipefail

readonly root=/home/raz/ros-robot-cc
readonly package="$root/onboard_ros2_ws/src/sensor_visualization"
readonly robot="${LITE3_ROBOT_SSH:-abx@192.168.2.32}"
readonly remote_pkg=/home/abx/Desktop/robotdog_ws/src/src/sensor_visualization
readonly staged=/home/abx/lite3-dds-systemd
readonly units=(
    lite3-high-level-runtime.service
    lite3-localization.service
    lite3-nav2.service
    lite3-nav2-safety-monitor.service
    lite3-autonomy-command-source.service
    lite3-laptop-xbox-source.service
    lite3-mapping.service
    lite3-system-health.service
)

host="$(ssh -o BatchMode=yes -o ConnectTimeout=4 "$robot" hostname)"
[[ "$host" == "abx-fit-001" ]] || {
    echo "REFUSING: SSH target is '${host:-unreachable}', expected abx-fit-001" >&2
    exit 2
}

for unit in "${units[@]}"; do
    grep -q '^Environment=FASTDDS_BUILTIN_TRANSPORTS=UDPv4$' \
        "$package/systemd/$unit" || {
        echo "REFUSING: UDPv4 environment missing from $unit" >&2
        exit 3
    }
done

ssh "$robot" "mkdir -p '$remote_pkg/scripts' '$remote_pkg/launch' '$remote_pkg/config' '$remote_pkg/systemd' '$staged'"
scp "$package/scripts/lite3_high_level_runtime.sh" \
    "$package/scripts/xbox_lite3_motion_host_bridge.py" \
    "$package/scripts/lite3_ros_inputs_ready.py" \
    "$package/scripts/lite3_localization_start.sh" \
    "$package/scripts/lite3_autonomy_command_source.py" \
    "$package/scripts/lite3_nav2_preflight.py" \
    "$package/scripts/lite3_nav2_safety_monitor.py" \
    "$package/scripts/lite3_laptop_xbox_source.py" \
    "$package/scripts/lite3_system_health.sh" \
    "$robot:$remote_pkg/scripts/"
scp "$package/launch/nav2_day2.launch.py" "$robot:$remote_pkg/launch/"
scp "$package/config/nav2_day2.yaml" \
    "$package/config/navigate_to_pose_day2.xml" "$robot:$remote_pkg/config/"
for unit in "${units[@]}"; do
    scp "$package/systemd/$unit" "$robot:$remote_pkg/systemd/$unit"
    scp "$package/systemd/$unit" "$robot:$staged/$unit"
done
scp "$root/operator/apply_dds_runtime_units.sh" \
    "$robot:/home/abx/apply_dds_runtime_units.sh"

ssh "$robot" "set -e; chmod 0755 /home/abx/apply_dds_runtime_units.sh; \
  source /opt/ros/jazzy/setup.bash; \
  cd /home/abx/Desktop/robotdog_ws; \
  colcon build --symlink-install --packages-select sensor_visualization"

echo "DDS FIXES STAGED AND BUILT — SERVICES UNCHANGED"
echo "Tomorrow install the units with:"
echo "  ssh -t $robot 'sudo /home/abx/apply_dds_runtime_units.sh'"
echo "HARDWARE COMMANDS SENT: NONE"
