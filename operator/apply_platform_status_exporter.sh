#!/usr/bin/env bash
set -euo pipefail

readonly stage="${1:-/home/abx/platform-status-exporter-stage}"
readonly robot_id="${2:-robot_01}"
readonly target=/home/abx/ros2_ws/install/sensor_visualization/lib/sensor_visualization
readonly unit=/etc/systemd/system/lite3-platform-status-exporter.service
readonly env_dir=/etc/lite3-control
readonly env_file=$env_dir/platform-status-exporter.env

test "$(id -u)" -eq 0 || { echo 'Run with sudo' >&2; exit 2; }
[[ "$robot_id" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$ ]] || { echo 'Invalid robot_id' >&2; exit 2; }
install -d -o abx -g abx -m 0755 "$target"
install -d -o root -g root -m 0755 "$env_dir"
printf 'LITE3_ROBOT_ID=%s\n' "$robot_id" > "$env_file"
chmod 0644 "$env_file"
install -o abx -g abx -m 0755 \
  "$stage/lite3_platform_status_exporter.py" \
  "$target/lite3_platform_status_exporter"
install -o root -g root -m 0644 \
  "$stage/lite3-platform-status-exporter.service" "$unit"
systemctl daemon-reload
systemctl enable lite3-platform-status-exporter.service
systemctl restart lite3-platform-status-exporter.service
echo 'PLATFORM STATUS EXPORTER INSTALLED — READ ONLY, NO ROBOT COMMANDS'
