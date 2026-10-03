#!/usr/bin/env bash
# Bounded, motion-free supervisor for deterministic saved-map localization.
set -eo pipefail

readonly state_dir="${LITE3_STATE_DIR:-/run/lite3-control}"
readonly workspace="${LITE3_WORKSPACE:-/home/abx/Desktop/robotdog_ws}"
readonly executables="$workspace/install/sensor_visualization/lib/sensor_visualization"
readonly input_gate="${LITE3_INPUT_GATE:-$executables/lite3_ros_inputs_ready}"
readonly launch_stack="${LITE3_LOCALIZATION_LAUNCH:-$executables/lite3_localization_start}"
readonly lifecycle_gate="${LITE3_LIFECYCLE_GATE:-$executables/lite3_localization_lifecycle_ready}"
readonly attempts="${LITE3_LOCALIZATION_ATTEMPTS:-3}"
readonly dds_cleanup_seconds="${LITE3_DDS_CLEANUP_SECONDS:-10}"

if [[ "${LITE3_SKIP_ROS_ENV:-false}" != true ]]; then
    source "${LITE3_ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
    source "$workspace/install/setup.bash"
    export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
    export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-SUBNET}"
    export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"
fi

child=""
stopping=false

write_state() {
    local name value path temporary
    name="$1"
    value="$2"
    path="$state_dir/$name"
    mkdir -p "$state_dir"
    temporary="$state_dir/.$name.$$"
    printf '%s\n' "$value" >"$temporary"
    mv -f "$temporary" "$path"
}

stop_child() {
    if [[ -n "$child" ]] && kill -0 "$child" 2>/dev/null; then
        kill -INT "$child" 2>/dev/null || true
        for _ in $(seq 1 30); do
            kill -0 "$child" 2>/dev/null || break
            sleep 0.1
        done
        kill -TERM "$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
    fi
    child=""
}

shutdown() {
    stopping=true
    stop_child
    exit 0
}
trap shutdown INT TERM

for attempt in $(seq 1 "$attempts"); do
    write_state LOCALIZATION_STARTUP_STATE STARTING
    write_state LOCALIZATION_STARTUP_ERROR "attempt $attempt/$attempts"
    echo "localization startup attempt $attempt/$attempts"

    if ! "$input_gate"; then
        reason="input readiness failed on attempt $attempt/$attempts"
        write_state LOCALIZATION_STARTUP_STATE STARTUP_FAILED
        write_state LOCALIZATION_STARTUP_ERROR "$reason"
    else
        write_state LOCALIZATION_STARTUP_ERROR ""
        "$launch_stack" &
        child=$!
        if "$lifecycle_gate"; then
            echo "localization lifecycle and TF ready; monitoring launch"
            wait "$child" || launch_rc=$?
            launch_rc="${launch_rc:-0}"
            child=""
            [[ "$stopping" == true ]] && exit 0
            reason="localization launch exited unexpectedly (rc=$launch_rc)"
            write_state LOCALIZATION_STARTUP_STATE STARTUP_FAILED
            write_state LOCALIZATION_STARTUP_ERROR "$reason"
        else
            gate_rc=$?
            reason="$(cat "$state_dir/LOCALIZATION_STARTUP_ERROR" 2>/dev/null || true)"
            [[ -n "$reason" ]] || reason="lifecycle readiness failed (rc=$gate_rc)"
            stop_child
        fi
    fi

    if (( attempt < attempts )); then
        echo "localization recovery: waiting ${dds_cleanup_seconds}s for DDS cleanup"
        sleep "$dds_cleanup_seconds"
    fi
done

write_state LOCALIZATION_STARTUP_STATE STARTUP_FAILED
write_state LOCALIZATION_STARTUP_ERROR "${reason:-localization startup retries exhausted}"
echo "LOCALIZATION STARTUP FAILED: ${reason:-unknown error}" >&2
exit 1
