#!/usr/bin/env bash
set -euo pipefail

readonly supervisor="${LITE3_XBOX_SUPERVISOR:-/home/abx/ros2_ws/install/sensor_visualization/lib/sensor_visualization/lite3_xbox_reconnect_supervisor}"
exec "$supervisor"
