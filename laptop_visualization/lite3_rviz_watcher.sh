#!/usr/bin/env bash
set -eo pipefail

readonly ros_setup="${LITE3_ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
readonly root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export LITE3_RVIZ_CONFIG="${LITE3_RVIZ_CONFIG:-$root/lite3_remote_lidar.rviz}"
readonly config="$LITE3_RVIZ_CONFIG"
readonly session="$root/lite3_nav2_rviz_session.sh"
readonly retry_seconds="${LITE3_RVIZ_RETRY_SECONDS:-10}"
# Remote DDS discovery can take several seconds immediately after either host
# boots. Give one scan enough time to arrive so a healthy robot is not
# repeatedly reported unavailable while preserving the retry loop.
readonly scan_timeout="${LITE3_RVIZ_SCAN_TIMEOUT_SECONDS:-8}"

source "$ros_setup"
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-SUBNET}"
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"

rviz_pid=""
last_availability="unknown"

log() { printf 'lite3-rviz-watcher: %s\n' "$*"; }

stop_rviz() {
    if [[ -n "$rviz_pid" ]] && kill -0 "$rviz_pid" 2>/dev/null; then
        kill -TERM "$rviz_pid" 2>/dev/null || true
        wait "$rviz_pid" 2>/dev/null || true
    fi
}
trap 'stop_rviz; exit 0' INT TERM

scan_is_live() {
    timeout "$scan_timeout" ros2 topic echo /scan --once \
        --qos-reliability best_effort --qos-durability volatile \
        >/dev/null 2>&1
}

rviz_already_running() {
    pgrep -u "$(id -u)" -f "rviz2.*${config}" >/dev/null 2>&1
}

[[ -r "$config" ]] || { log "configuration missing: $config"; exit 2; }
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    log "no graphical session; waiting for service restart in a graphical session"
    exit 0
fi

log "started; waiting quietly for a live /scan"
while true; do
    if scan_is_live; then
        if [[ "$last_availability" != "available" ]]; then
            log "robot LiDAR is available"
            last_availability="available"
        fi
        if [[ -z "$rviz_pid" ]] || ! kill -0 "$rviz_pid" 2>/dev/null; then
            if rviz_already_running; then
                log "Lite3 RViz is already running; not opening another window"
            else
                log "starting one Lite3 RViz instance"
                "$session" &
                rviz_pid=$!
            fi
        fi
    else
        if [[ "$last_availability" != "unavailable" ]]; then
            log "robot LiDAR unavailable; RViz will not be opened"
            last_availability="unavailable"
        fi
        # If RViz was already opened, deliberately leave it open. This keeps
        # the UI predictable while never restarting or touching robot services.
    fi

    if [[ -n "$rviz_pid" ]] && ! kill -0 "$rviz_pid" 2>/dev/null; then
        wait "$rviz_pid" 2>/dev/null || true
        rviz_pid=""
        log "RViz exited; returning to availability watch"
    fi
    sleep "$retry_seconds"
done
