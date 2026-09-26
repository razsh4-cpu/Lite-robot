#!/usr/bin/env bash
set -u

readonly state_dir="${LITE3_CONTROL_STATE_DIR:-/run/lite3-control}"

if systemctl is-active --quiet multi-user.target; then
    system_ready=true
else
    system_ready=false
fi

read_flag() {
    local file="$1"
    if [[ -r "$file" ]] && grep -qx 'true' "$file"; then
        printf 'true'
    else
        printf 'false'
    fi
}
read_text() {
    local file="$1" fallback="$2"
    if [[ -r "$file" ]]; then
        tr -d '\r\n' <"$file"
    else
        printf '%s' "$fallback"
    fi
}

printf 'SYSTEM_READY=%s\n' "$system_ready"
printf 'AUTONOMY_READY=%s\n' "$(read_flag "$state_dir/AUTONOMY_READY")"
printf 'MANUAL_CONTROL_AVAILABLE=%s\n' "$(read_flag "$state_dir/MANUAL_CONTROL_AVAILABLE")"
printf 'XBOX_STATUS=%s\n' "$(read_text "$state_dir/XBOX_STATUS" UNAVAILABLE)"
printf 'XBOX_BLUETOOTH_CONNECTED=%s\n' "$(read_flag "$state_dir/XBOX_BLUETOOTH_CONNECTED")"
printf 'XBOX_DEVICE_PRESENT=%s\n' "$(read_flag "$state_dir/XBOX_DEVICE_PRESENT")"
printf 'XBOX_DEVICE_VALID=%s\n' "$(read_flag "$state_dir/XBOX_DEVICE_VALID")"
printf 'LOCAL_XBOX_RUNTIME_STATE=%s\n' "$(read_text "$state_dir/LOCAL_XBOX_RUNTIME_STATE" STOPPED)"
if [[ -r "$state_dir/owner.lock" ]] && ! flock -n "$state_dir/owner.lock" true 2>/dev/null; then
    grep '^COMMAND_SOURCE=' "$state_dir/owner.lock" 2>/dev/null || printf 'COMMAND_SOURCE=NONE\n'
else
    printf 'COMMAND_SOURCE=NONE\n'
fi
