#!/usr/bin/env bash
set -u

state_dir="${LITE3_STATE_DIR:-/run/lite3-control}"
for key in SYSTEM_READY HIGH_LEVEL_RUNTIME_READY HEARTBEAT_READY TELEMETRY_FRESH \
    ODOM_READY TF_READY LIDAR_READY LOCALIZATION_READY REALSENSE_READY \
    ROBOT_LINK_READY LAPTOP_REACHABLE AUTONOMY_READY \
    MANUAL_CONTROL_AVAILABLE COMMAND_SOURCE; do
    if [[ -r "$state_dir/$key" ]]; then
        printf '%s=%s\n' "$key" "$(<"$state_dir/$key")"
    else
        printf '%s=UNKNOWN\n' "$key"
    fi
done

service_status() {
    systemctl --quiet is-active "$1" \
        && printf '%s=active\n' "$2" || printf '%s=inactive\n' "$2"
}
service_status lite3-high-level-runtime.service HIGH_LEVEL_RUNTIME
service_status lite3-lidar.service LIDAR_SERVICE
service_status lite3-localization.service LOCALIZATION_SERVICE
service_status lite3-realsense.service REALSENSE_SERVICE
service_status lite3-xbox.service XBOX_SUPERVISOR
service_status lite3-high-level-xbox.service XBOX_INPUT_RUNTIME
service_status lite3-system-health.service HEALTH_MONITOR

receiver_count="$(ss -uan 2>/dev/null | awk '$4 ~ /:43897$/ {count++} END {print count+0}')"
printf 'UDP_43897_RECEIVERS=%s\n' "$receiver_count"
