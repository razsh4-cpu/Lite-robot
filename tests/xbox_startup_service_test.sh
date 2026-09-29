#!/usr/bin/env bash
set -euo pipefail

readonly root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly temp="$(mktemp -d /tmp/lite3-xbox-startup-test.XXXXXX)"
trap 'rm -rf "$temp"' EXIT

cat >"$temp/validator" <<'EOF'
#!/usr/bin/env bash
[[ -e "${FAKE_XBOX_AVAILABLE}" ]]
EOF
cat >"$temp/bluetoothctl" <<'EOF'
#!/usr/bin/env bash
count=0
[[ -r "${FAKE_CONNECT_COUNT}" ]] && count="$(<"${FAKE_CONNECT_COUNT}")"
count=$((count+1))
printf '%s\n' "$count" >"${FAKE_CONNECT_COUNT}"
if [[ -n "${FAKE_CONNECT_ON_ATTEMPT:-}" ]] && (( count >= FAKE_CONNECT_ON_ATTEMPT )); then
    : >"${FAKE_XBOX_AVAILABLE}"
fi
EOF
chmod 0755 "$temp/validator" "$temp/bluetoothctl"

export FAKE_XBOX_AVAILABLE="$temp/available"
export FAKE_CONNECT_COUNT="$temp/count"
export LITE3_XBOX_DEVICE="$temp/fake-js0"
export LITE3_XBOX_STATE_FILE="$temp/manual"
export LITE3_XBOX_STATUS_FILE="$temp/status"
export LITE3_XBOX_BLUETOOTH_STATE_FILE="$temp/bluetooth"
export LITE3_XBOX_DEVICE_PRESENT_FILE="$temp/present"
export LITE3_XBOX_DEVICE_VALID_FILE="$temp/valid"
export LITE3_XBOX_VALIDATOR="$temp/validator"
export LITE3_BLUETOOTHCTL="$temp/bluetoothctl"
export LITE3_XBOX_MAX_ATTEMPTS=6
export LITE3_XBOX_RETRY_SECONDS=0

export FAKE_CONNECT_ON_ATTEMPT=2
"$root/scripts/lite3_xbox_connection_monitor.sh"
grep -qx true "$temp/manual"
grep -qx AVAILABLE "$temp/status"
grep -qx true "$temp/bluetooth"
grep -qx true "$temp/present"
grep -qx true "$temp/valid"
[[ "$(<"$temp/count")" == 2 ]]

rm -f "$temp/available" "$temp/count"
unset FAKE_CONNECT_ON_ATTEMPT
printf 'true\n' >"$temp/SYSTEM_READY"
"$root/scripts/lite3_xbox_connection_monitor.sh"
grep -qx false "$temp/manual"
grep -qx UNAVAILABLE "$temp/status"
grep -qx false "$temp/bluetooth"
grep -qx false "$temp/valid"
[[ "$(<"$temp/count")" == 6 ]]
grep -qx true "$temp/SYSTEM_READY"

grep -qx "OnSuccess=lite3-local-xbox-control.service" "$root/systemd/lite3-xbox.service"
! grep -q "Restart=always" "$root/systemd/lite3-xbox.service"
grep -qx "Wants=lite3-xbox.service" "$root/systemd/lite3-local-xbox-control.service"
grep -qx "After=lite3-xbox.service" "$root/systemd/lite3-local-xbox-control.service"
! grep -q "LITE3_POLICY_MODEL" "$root/systemd/lite3-local-xbox-control.service"
grep -q "MANUAL_CONTROL_AVAILABLE" "$root/systemd/lite3-local-xbox-control.service"
grep -q "lite3_command_source_none.sh" "$root/systemd/lite3-local-xbox-control.service"
grep -q "lite3_xbox_device_valid.sh" "$root/systemd/lite3-local-xbox-control.service"

cat >"$temp/udevadm" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' 'ID_INPUT_JOYSTICK=1' 'ID_BUS=bluetooth'
EOF
chmod 0755 "$temp/udevadm"
mkdir -p "$temp/sys/class/input/null/device"
printf '%s\n' 'Xbox Wireless Controller' >"$temp/sys/class/input/null/device/name"
LITE3_UDEVADM="$temp/udevadm" \
LITE3_SYS_CLASS_INPUT="$temp/sys/class/input" \
    "$root/scripts/lite3_xbox_device_valid.sh" /dev/null
printf '%s\n' 'Generic Joystick' >"$temp/sys/class/input/null/device/name"
! LITE3_UDEVADM="$temp/udevadm" \
  LITE3_SYS_CLASS_INPUT="$temp/sys/class/input" \
    "$root/scripts/lite3_xbox_device_valid.sh" /dev/null

mkdir -p "$temp/readiness"
printf '%s\n' false >"$temp/readiness/AUTONOMY_READY"
printf '%s\n' true >"$temp/readiness/MANUAL_CONTROL_AVAILABLE"
printf '%s\n' AVAILABLE >"$temp/readiness/XBOX_STATUS"
printf '%s\n' true >"$temp/readiness/XBOX_BLUETOOTH_CONNECTED"
printf '%s\n' true >"$temp/readiness/XBOX_DEVICE_PRESENT"
printf '%s\n' true >"$temp/readiness/XBOX_DEVICE_VALID"
printf '%s\n' 'Idle / WaitingForStand' >"$temp/readiness/LOCAL_XBOX_RUNTIME_STATE"
LITE3_CONTROL_STATE_DIR="$temp/readiness" \
    "$root/scripts/lite3_readiness_status.sh" >"$temp/readiness.out"
grep -qx 'MANUAL_CONTROL_AVAILABLE=true' "$temp/readiness.out"
grep -qx 'XBOX_STATUS=AVAILABLE' "$temp/readiness.out"
grep -qx 'XBOX_DEVICE_VALID=true' "$temp/readiness.out"
grep -qx 'LOCAL_XBOX_RUNTIME_STATE=Idle / WaitingForStand' "$temp/readiness.out"
grep -qx 'COMMAND_SOURCE=NONE' "$temp/readiness.out"

echo "xbox_startup_service_test PASS"
