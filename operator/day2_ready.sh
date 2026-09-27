#!/usr/bin/env bash
# Read-only remote Nav2 go/no-go check. Never acquires a lease or publishes.
set -euo pipefail

readonly robot="${LITE3_ROBOT_SSH:-abx@192.168.2.32}"
set +e
output="$(ssh -o BatchMode=yes -o ConnectTimeout=4 "$robot" \
  'export FASTDDS_BUILTIN_TRANSPORTS=UDPv4; \
   source /opt/ros/jazzy/setup.bash; \
   source /home/abx/Desktop/robotdog_ws/install/setup.bash; \
   exec /home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/sensor_visualization/lite3_nav2_preflight' 2>&1)"
rc=$?
set -e
if [[ "$rc" -eq 255 ]]; then
    echo "MINI-PC OFFLINE"
    exit 2
fi
printf '%s\n' "$output"
exit "$rc"
