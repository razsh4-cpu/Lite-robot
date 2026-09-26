#!/usr/bin/env bash
set -u

readonly controller_mac="${LITE3_XBOX_MAC:-78:86:2E:B6:8F:C3}"
readonly joystick="${LITE3_XBOX_DEVICE:-/dev/input/js0}"
readonly state_file="${LITE3_XBOX_STATE_FILE:-/run/lite3-control/MANUAL_CONTROL_AVAILABLE}"
readonly status_file="${LITE3_XBOX_STATUS_FILE:-/run/lite3-control/XBOX_STATUS}"
readonly bluetooth_state_file="${LITE3_XBOX_BLUETOOTH_STATE_FILE:-/run/lite3-control/XBOX_BLUETOOTH_CONNECTED}"
readonly device_present_file="${LITE3_XBOX_DEVICE_PRESENT_FILE:-/run/lite3-control/XBOX_DEVICE_PRESENT}"
readonly device_valid_file="${LITE3_XBOX_DEVICE_VALID_FILE:-/run/lite3-control/XBOX_DEVICE_VALID}"
readonly validator="${LITE3_XBOX_VALIDATOR:-/home/abx/Lite-robot/scripts/lite3_xbox_device_valid.sh}"
readonly bluetoothctl_bin="${LITE3_BLUETOOTHCTL:-/usr/bin/bluetoothctl}"
readonly max_attempts="${LITE3_XBOX_MAX_ATTEMPTS:-6}"
readonly retry_seconds="${LITE3_XBOX_RETRY_SECONDS:-5}"

log() { printf 'lite3-xbox: %s\n' "$*"; }
write_state() { printf '%s\n' "$2" >"$1"; }
set_available() {
    local value="$1"
    printf '%s\n' "$value" >"$state_file"
    log "MANUAL_CONTROL_AVAILABLE=${value}"
}
set_unavailable() {
    set_available false
    write_state "$bluetooth_state_file" false
    write_state "$device_valid_file" false
}
interrupted() {
    set_unavailable
    write_state "$status_file" UNAVAILABLE
    exit 0
}
trap interrupted INT TERM

set_unavailable
write_state "$status_file" WAITING
for ((attempt=1; attempt<=max_attempts; ++attempt)); do
    write_state "$status_file" CONNECTING
    [[ -c "$joystick" ]] &&
        write_state "$device_present_file" true ||
        write_state "$device_present_file" false
    if "$validator" "$joystick"; then
        write_state "$bluetooth_state_file" true
        write_state "$device_present_file" true
        write_state "$device_valid_file" true
        write_state "$status_file" AVAILABLE
        set_available true
        log "Xbox ready on ${joystick} (attempt ${attempt}/${max_attempts})"
        exit 0
    fi

    log "Xbox unavailable; connect attempt ${attempt}/${max_attempts}"
    "$bluetoothctl_bin" connect "$controller_mac" >/dev/null 2>&1 || true
    if (( retry_seconds > 0 )); then sleep "$retry_seconds"; fi
done

if "$validator" "$joystick"; then
    write_state "$bluetooth_state_file" true
    write_state "$device_present_file" true
    write_state "$device_valid_file" true
    write_state "$status_file" AVAILABLE
    set_available true
    log "Xbox ready on ${joystick} at end of startup window"
else
    set_unavailable
    [[ -c "$joystick" ]] &&
        write_state "$device_present_file" true ||
        write_state "$device_present_file" false
    write_state "$status_file" UNAVAILABLE
    log "Xbox not available after startup window; no background retries"
fi
exit 0
