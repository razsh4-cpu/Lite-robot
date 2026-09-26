#!/usr/bin/env bash
set -u

readonly joystick="${1:-/dev/input/js0}"
readonly udevadm_bin="${LITE3_UDEVADM:-/usr/bin/udevadm}"
[[ -c "$joystick" ]] || exit 1
properties="$("$udevadm_bin" info --query=property --name="$joystick" 2>/dev/null)" || exit 1
grep -q '^ID_INPUT_JOYSTICK=1$' <<<"$properties" || exit 1
if grep -Eiq '^(ID_MODEL|NAME)=.*Xbox.*Controller' <<<"$properties"; then
    exit 0
fi

# hid-xpadneo devices are created through uhid. On that path udev may expose
# the joystick capability and Bluetooth bus but omit ID_MODEL/NAME entirely.
# The kernel input device name remains available through the standard sysfs
# input-class entry, so use it as a strict identity fallback.
readonly sys_class_input="${LITE3_SYS_CLASS_INPUT:-/sys/class/input}"
readonly device_name_file="$sys_class_input/$(basename "$joystick")/device/name"
[[ -r "$device_name_file" ]] || exit 1
device_name="$(<"$device_name_file")"
[[ "$device_name" == *"Xbox Wireless Controller"* ]]
