#!/usr/bin/env bash
set -o pipefail

readonly state_dir="${LITE3_STATE_DIR:-/run/lite3-control}"
readonly interval="${LITE3_HEALTH_INTERVAL_SECONDS:-10}"
readonly probe_timeout="${LITE3_HEALTH_PROBE_TIMEOUT_SECONDS:-8}"
readonly laptop_ip="${LITE3_LAPTOP_IP:-192.168.2.177}"
mkdir -p "$state_dir"
[[ -e "$state_dir/AUTONOMY_READY" ]] || printf 'false\n' >"$state_dir/AUTONOMY_READY"
[[ -e "$state_dir/COMMAND_SOURCE" ]] || printf 'NONE\n' >"$state_dir/COMMAND_SOURCE"
[[ -e "$state_dir/MANUAL_CONTROL_AVAILABLE" ]] || printf 'false\n' >"$state_dir/MANUAL_CONTROL_AVAILABLE"

source /opt/ros/jazzy/setup.bash
source /home/abx/ros2_ws/install/setup.bash
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"
set -u

stopping=false
trap 'stopping=true' INT TERM

write_state() {
    local key="$1" value="$2" tmp
    tmp="$state_dir/.${key}.$$"
    printf '%s\n' "$value" >"$tmp"
    mv -f "$tmp" "$state_dir/$key"
}

topic_fresh() {
    timeout "$probe_timeout" ros2 topic echo "$1" --once "${@:2}" >/dev/null 2>&1
}

service_active() {
    systemctl --quiet is-active "$1"
}

tf_available() {
    local output
    # tf2_echo is intentionally long-running. Capturing its bounded output
    # avoids pipefail interpreting grep -q's early pipe close as TF failure.
    output="$(timeout "$probe_timeout" ros2 run tf2_ros tf2_echo "$1" "$2" 2>&1 || true)"
    grep -q "Translation:" <<<"$output"
}

lifecycle_active() {
    local output
    output="$(timeout "$probe_timeout" ros2 lifecycle get "$1" 2>&1 || true)"
    grep -q "active \[3\]" <<<"$output"
}

last_signature=""
while [[ "$stopping" == false ]]; do
    runtime=false
    heartbeat=false
    telemetry=false
    odom=false
    tf=false
    lidar=false
    localization=false
    realsense=false
    robot_link=false
    laptop=false

    service_active lite3-high-level-runtime.service && runtime=true
    if [[ "$runtime" == true ]] && timeout "$probe_timeout" ros2 param get \
            /lite3_high_level_runtime heartbeat_enabled 2>/dev/null | grep -q 'True'; then
        heartbeat=true
    fi
    if topic_fresh /odom; then
        telemetry=true
        odom=true
    fi
    if tf_available odom base_link; then
        tf=true
    fi
    if topic_fresh /scan --qos-reliability best_effort --qos-durability volatile; then
        lidar=true
    fi
    if service_active lite3-localization.service \
            && lifecycle_active /map_server \
            && lifecycle_active /amcl \
            && tf_available map base_link; then
        localization=true
    fi
    if service_active lite3-realsense.service \
            && topic_fresh /camera/camera/color/image_raw --qos-reliability best_effort; then
        realsense=true
    fi
    ping -c 1 -W 1 192.168.1.120 >/dev/null 2>&1 && robot_link=true
    ping -c 1 -W 1 "$laptop_ip" >/dev/null 2>&1 && laptop=true

    system_ready=false
    if [[ "$runtime" == true && "$heartbeat" == true && "$telemetry" == true \
            && "$odom" == true && "$tf" == true ]]; then
        system_ready=true
    fi

    write_state SYSTEM_READY "$system_ready"
    write_state HIGH_LEVEL_RUNTIME_READY "$runtime"
    write_state HEARTBEAT_READY "$heartbeat"
    write_state TELEMETRY_FRESH "$telemetry"
    write_state ODOM_READY "$odom"
    write_state TF_READY "$tf"
    write_state LIDAR_READY "$lidar"
    write_state LOCALIZATION_READY "$localization"
    write_state REALSENSE_READY "$realsense"
    write_state ROBOT_LINK_READY "$robot_link"
    write_state LAPTOP_REACHABLE "$laptop"

    signature="system=$system_ready runtime=$runtime heartbeat=$heartbeat telemetry=$telemetry odom=$odom tf=$tf lidar=$lidar localization=$localization realsense=$realsense xbox=$(<"$state_dir/MANUAL_CONTROL_AVAILABLE") source=$(<"$state_dir/COMMAND_SOURCE") laptop=$laptop"
    if [[ "$signature" != "$last_signature" ]]; then
        echo "lite3-health: $signature"
        last_signature="$signature"
    fi

    sleep "$interval" &
    wait $! || true
done

exit 0
