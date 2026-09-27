#!/usr/bin/env bash
set -u

joystick="${1:-/dev/input/js0}"
[[ -c "$joystick" ]] || exit 1
properties="$(udevadm info --query=property --name="$joystick" 2>/dev/null)" || exit 1
grep -q '^ID_INPUT_JOYSTICK=1$' <<<"$properties" || exit 1
if grep -Eiq '^(ID_MODEL|NAME)=.*Xbox.*Controller' <<<"$properties"; then
    exit 0
fi
# hid-xpadneo/uhid may omit ID_MODEL; the kernel input name is authoritative.
sys_input="${LITE3_SYS_CLASS_INPUT:-/sys/class/input}"
name_file="$sys_input/$(basename "$joystick")/device/name"
[[ -r "$name_file" ]] || exit 1
[[ "$(<"$name_file")" == *"Xbox Wireless Controller"* ]]
