#!/usr/bin/env bash
set -euo pipefail

[[ "$(hostname)" == "abx-fit-001" ]] || {
    echo "REFUSING: run only on abx-fit-001" >&2
    exit 2
}

readonly source_unit=/home/abx/Desktop/robotdog_ws/src/src/sensor_visualization/systemd/lite3-localization.service
readonly target_unit=/etc/systemd/system/lite3-localization.service

install -m 0644 "$source_unit" "$target_unit"
systemctl daemon-reload

echo "LOCALIZATION STARTUP UNIT INSTALLED"
echo "SERVICE RESTARTED: NO"
echo "HARDWARE MOTION COMMANDS SENT: NONE"
