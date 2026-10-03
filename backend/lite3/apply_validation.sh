#!/usr/bin/env bash
# Privileged boundary: stop SABLE and install/start NAVIGATION-ONLY services.
set -euo pipefail
[[ "$EUID" == 0 ]] || { echo 'run with sudo'; exit 2; }
root="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
[[ -r "$root/ros_ws/install/setup.bash" && -r "$root/site.env" ]]
[[ "$(cat /run/lite3-control/COMMAND_SOURCE)" == NONE ]]
! systemctl is-active --quiet lite3-autonomy-command-source.service
# Preserve the already running INERT runtime and relay byte-for-byte.
systemctl stop sable-edge.service sable-ros.service
install -d -o abx -g abx -m 2775 /run/lite3-control
unit="$(mktemp)"
trap 'rm -f "$unit"' EXIT
printf '%s\n' '[Unit]' 'Description=Independent Lite3 no-motion navigation validation' \
 'After=lite3-high-level-runtime.service' 'Requires=lite3-high-level-runtime.service' \
 'Conflicts=sable-edge.service sable-ros.service lite3-autonomy-command-source.service' \
 '[Service]' 'Type=simple' 'User=abx' 'Group=abx' "WorkingDirectory=$root" \
 "ExecStart=/bin/bash $root/backend/lite3/run_validation.sh" \
 'KillMode=control-group' 'KillSignal=SIGINT' 'TimeoutStopSec=15' 'Restart=no' >"$unit"
install -m 0644 "$unit" /etc/systemd/system/lite3-autonomy-validation.service
scripts="$root/onboard_ros2_ws/src/sensor_visualization/scripts"
printf '%s\n' '[Unit]' 'Description=Existing Lite3 Nav2 safety monitor' \
 'After=lite3-high-level-runtime.service' '[Service]' 'Type=simple' 'User=abx' 'Group=abx' \
 'Environment=ROS_DOMAIN_ID=0' 'Environment=FASTDDS_BUILTIN_TRANSPORTS=UDPv4' \
 "ExecStart=/bin/bash $root/backend/lite3/run_validation_monitor.sh" \
 'KillMode=control-group' 'KillSignal=SIGINT' 'TimeoutStopSec=10' 'Restart=no' >"$unit"
install -m 0644 "$unit" /etc/systemd/system/lite3-nav2-safety-monitor.service
systemctl daemon-reload
systemctl start lite3-nav2-safety-monitor.service
systemctl start lite3-autonomy-validation.service
echo 'NAVIGATION-ONLY VALIDATION STARTED — AUTONOMY NOT ACQUIRED; TRANSMISSION UNCHANGED/DISABLED'
