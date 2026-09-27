#!/usr/bin/env bash
""":"
Deploy the prepared Day-2 layer without using Mini-PC internet.

This script installs packages/builds/services but deliberately does not enable
or start Nav2 or AUTONOMY and never publishes a goal or velocity.
":"""
set -euo pipefail

readonly root="/home/raz/ros-robot-cc"
readonly package="$root/onboard_ros2_ws/src/sensor_visualization"
readonly state_package="$root/onboard_ros2_ws/src/lite3_state_estimation"
readonly bundle="$root/.offline/nav2-jazzy-amd64"
readonly robot="${LITE3_ROBOT_SSH:-abx@192.168.2.32}"
readonly remote_pkg="/home/abx/Desktop/robotdog_ws/src/src/sensor_visualization"
readonly remote_state_pkg="/home/abx/Desktop/robotdog_ws/src/src/lite3_state_estimation"
readonly remote_bundle="/home/abx/day2-nav2-debs"

[[ -d "$bundle" && -s "$bundle/SHA256SUMS" ]] || {
    echo "Offline Nav2 bundle missing: $bundle" >&2; exit 2;
}
(cd "$bundle" && sha256sum -c SHA256SUMS)

host="$(ssh -o BatchMode=yes -o ConnectTimeout=4 "$robot" hostname)"
[[ "$host" == "abx-fit-001" ]] || {
    echo "Wrong SSH target: $host" >&2; exit 2;
}

ssh "$robot" "mkdir -p '$remote_bundle' '$remote_pkg/scripts' '$remote_pkg/config' '$remote_pkg/launch' '$remote_pkg/test' '$remote_state_pkg/config' '$remote_state_pkg/launch' '$remote_state_pkg/lite3_state_estimation' '$remote_state_pkg/resource' '$remote_state_pkg/test'"
scp "$bundle"/*.deb "$bundle/SHA256SUMS" "$robot:$remote_bundle/"
scp "$package/CMakeLists.txt" "$package/package.xml" "$robot:$remote_pkg/"
scp "$package/config/nav2_day2.yaml" \
    "$package/config/navigate_to_pose_day2.xml" \
    "$package/config/named_locations.yaml" "$robot:$remote_pkg/config/"
scp "$package/launch/nav2_day2.launch.py" "$robot:$remote_pkg/launch/"
scp "$package/scripts/lite3_nav2_preflight.py" \
    "$package/scripts/lite3_nav2_safety_monitor.py" \
    "$package/scripts/lite3_relocalization_motion.py" \
    "$package/scripts/lite3_relocalization_run.sh" \
    "$package/scripts/lite3_localization_gate.py" \
    "$package/scripts/lite3_high_level_ros_watchdog.py" \
    "$package/scripts/lite3_autonomy_command_source.py" \
    "$package/scripts/lite3_ros_inputs_ready.py" \
    "$package/scripts/lite3_localization_start.sh" \
    "$package/scripts/lite3_localization_supervisor.sh" \
    "$package/scripts/lite3_localization_lifecycle_ready.py" \
    "$package/scripts/lite3_map_manager.py" \
    "$package/scripts/lite3_mission_manager.py" \
    "$package/scripts/lite3_release_autonomy.sh" \
    "$package/scripts/plan_from_rviz_goal.py" \
    "$package/scripts/xbox_lite3_motion_host_bridge.py" "$robot:$remote_pkg/scripts/"
scp "$package/systemd/lite3-nav2.service" \
    "$package/systemd/lite3-nav2-safety-monitor.service" \
    "$package/systemd/lite3-relocalization-motion.service" \
    "$package/systemd/lite3-autonomy-command-source.service" \
    "$package/systemd/lite3-localization.service" \
    "$robot:$remote_pkg/systemd/"
scp "$package/test/test_day2_nav2_static.py" \
    "$package/test/test_localization_startup_supervisor.py" \
    "$package/test/test_day3_mission_registry.py" "$robot:$remote_pkg/test/"
scp "$state_package/package.xml" "$state_package/setup.py" \
    "$state_package/setup.cfg" "$robot:$remote_state_pkg/"
scp "$state_package/config/amcl.yaml" "$robot:$remote_state_pkg/config/"
scp "$state_package/launch/day1_localization.launch.py" \
    "$robot:$remote_state_pkg/launch/"
scp "$state_package/lite3_state_estimation/"*.py \
    "$robot:$remote_state_pkg/lite3_state_estimation/"
scp "$state_package/resource/lite3_state_estimation" \
    "$robot:$remote_state_pkg/resource/"
scp "$state_package/test/"test_*.py "$robot:$remote_state_pkg/test/"

# A TTY is intentional: sudo may request the operator's Mini-PC password once.
ssh -t "$robot" "set -e; \
  cd '$remote_bundle'; sha256sum -c SHA256SUMS; \
  sudo apt-get install -y ./*.deb; \
  cd /home/abx/Desktop/robotdog_ws; \
  source /opt/ros/jazzy/setup.bash; \
  colcon build --symlink-install --packages-select lite3_state_estimation sensor_visualization; \
  colcon test --packages-select lite3_state_estimation sensor_visualization --pytest-args -q; \
  sudo install -m 0644 '$remote_pkg/systemd/lite3-nav2.service' /etc/systemd/system/lite3-nav2.service; \
  sudo install -m 0644 '$remote_pkg/systemd/lite3-localization.service' /etc/systemd/system/lite3-localization.service; \
  sudo install -m 0644 '$remote_pkg/systemd/lite3-nav2-safety-monitor.service' /etc/systemd/system/lite3-nav2-safety-monitor.service; \
  sudo install -m 0644 '$remote_pkg/systemd/lite3-relocalization-motion.service' /etc/systemd/system/lite3-relocalization-motion.service; \
  sudo install -m 0644 '$remote_pkg/systemd/lite3-autonomy-command-source.service' /etc/systemd/system/lite3-autonomy-command-source.service; \
  printf '%s\n' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl start lite3-nav2.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl stop lite3-nav2.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl restart lite3-nav2.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl start lite3-autonomy-command-source.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl stop lite3-autonomy-command-source.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl start lite3-relocalization-motion.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl stop lite3-relocalization-motion.service' \
    | sudo tee /etc/sudoers.d/lite3-day2-control >/dev/null; \
  sudo chmod 0440 /etc/sudoers.d/lite3-day2-control; \
  sudo visudo -cf /etc/sudoers.d/lite3-day2-control; \
  sudo systemctl daemon-reload; \
  sudo systemctl disable lite3-nav2.service 2>/dev/null || true; \
  sudo systemctl stop lite3-nav2.service lite3-autonomy-command-source.service 2>/dev/null || true; \
  echo 'DAY2 OFFLINE DEPLOYED — SERVICES STOPPED'"
