#!/usr/bin/env bash
set -u

mac="${LITE3_XBOX_MAC:-78:86:2E:B6:8F:C3}"
joystick="${LITE3_XBOX_DEVICE:-/dev/input/js0}"
state_dir="${LITE3_STATE_DIR:-/run/lite3-control}"
validator="${LITE3_XBOX_VALIDATOR:-/home/abx/ros2_ws/install/sensor_visualization/lib/sensor_visualization/lite3_xbox_device_valid}"

read_state() { [[ -r "$state_dir/$1" ]] && tr -d '\n' <"$state_dir/$1" || printf 'UNKNOWN'; }
bt_info="$(bluetoothctl info "$mac" 2>/dev/null || true)"
connected="$(grep -q 'Connected: yes' <<<"$bt_info" && echo yes || echo no)"
battery="$(sed -n 's/^[[:space:]]*Battery Percentage: //p' <<<"$bt_info" | head -n1)"
[[ -n "$battery" ]] || battery="unknown"
if "$validator" "$joystick" 2>/dev/null; then
    device="valid Xbox joystick"
    device_ok=yes
    identity="$(cat "/sys/class/input/$(basename "$joystick")/device/name" 2>/dev/null || echo Xbox)"
else
    device="missing or wrong identity"
    device_ok=no
    identity="unknown"
fi
manual="$(read_state MANUAL_CONTROL_AVAILABLE)"
source_name="$(read_state COMMAND_SOURCE)"
service_state() {
    local unit="$1" active sub pid
    active="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || echo unknown)"
    sub="$(systemctl show "$unit" -p SubState --value 2>/dev/null || echo unknown)"
    pid="$(systemctl show "$unit" -p MainPID --value 2>/dev/null || echo 0)"
    printf '%s/%s (pid=%s)' "$active" "$sub" "$pid"
}
supervisor_state="$(service_state lite3-xbox.service)"
runtime_state="$(service_state lite3-high-level-xbox.service)"
robot_runtime_state="$(service_state lite3-high-level-runtime.service)"
route="$(ip route get 192.168.1.120 2>/dev/null | head -n1 || true)"
if ping -c 1 -W 1 192.168.1.120 >/dev/null 2>&1; then robot_link=reachable; else robot_link=unreachable; fi
last_event="$(journalctl -u lite3-high-level-xbox.service -u lite3-xbox.service -n 80 --no-pager 2>/dev/null | grep -E 'disconnected|reconnect|recovered|stopped; command source released' | tail -n1)"
[[ -n "$last_event" ]] || last_event="none recorded"

printf 'Bluetooth Xbox connected: %s\n' "$connected"
printf 'Xbox battery: %s\n' "$battery"
printf 'Joystick: %s (%s; %s)\n' "$joystick" "$device" "$identity"
printf 'MANUAL_CONTROL_AVAILABLE: %s\n' "$manual"
printf 'COMMAND_SOURCE: %s\n' "$source_name"
printf 'Reconnect supervisor: %s\n' "$supervisor_state"
printf 'Xbox input runtime: %s\n' "$runtime_state"
printf 'Persistent high-level runtime: %s\n' "$robot_runtime_state"
printf 'Robot link/route: %s | %s\n' "$robot_link" "${route:-no route}"
printf 'Last disconnect/reconnect event: %s\n' "$last_event"

if [[ "$robot_runtime_state" != active/running* ]]; then
    diagnosis='Persistent robot high-level runtime is not healthy; heartbeat, telemetry and odometry need attention.'
elif [[ "$connected" == yes && "$device_ok" == yes && "$runtime_state" != active/running* && "$source_name" == NONE ]]; then
    diagnosis='Xbox connected, but optional LOCAL_XBOX input failed to recover; robot link remains active.'
elif [[ "$connected" == no ]]; then
    diagnosis='Xbox unavailable; robot high-level link remains active with COMMAND_SOURCE=NONE.'
elif [[ "$source_name" != NONE && "$source_name" != LOCAL_XBOX ]]; then
    diagnosis="Xbox is available, but ${source_name} owns control; no takeover attempted."
elif [[ "$runtime_state" == active/running* ]]; then
    diagnosis='Robot runtime and optional Xbox input are healthy; fresh operator authorization is required.'
else
    diagnosis='Xbox input state is incomplete; persistent robot runtime remains independent.'
fi
printf 'Diagnosis: %s\n' "$diagnosis"
