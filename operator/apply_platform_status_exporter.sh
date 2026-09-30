#!/usr/bin/env bash
set -euo pipefail

readonly stage="${1:-/home/abx/platform-status-exporter-stage}"
readonly target=/home/abx/ros2_ws/install/sensor_visualization/lib/sensor_visualization
readonly unit=/etc/systemd/system/lite3-platform-status-exporter.service

test "$(id -u)" -eq 0 || { echo 'Run with sudo' >&2; exit 2; }
install -d -o abx -g abx -m 0755 "$target"
install -o abx -g abx -m 0755 \
  "$stage/lite3_platform_status_exporter.py" \
  "$target/lite3_platform_status_exporter"
install -o root -g root -m 0644 \
  "$stage/lite3-platform-status-exporter.service" "$unit"
systemctl daemon-reload
systemctl enable --now lite3-platform-status-exporter.service
echo 'PLATFORM STATUS EXPORTER INSTALLED — READ ONLY, NO ROBOT COMMANDS'
