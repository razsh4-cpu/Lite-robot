#!/usr/bin/env bash
set -u
printf 'false\n' >"${LITE3_XBOX_STATE_FILE:-/run/lite3-control/MANUAL_CONTROL_AVAILABLE}"
printf 'STOPPED\n' >"${LITE3_XBOX_RUNTIME_STATE_FILE:-/run/lite3-control/LOCAL_XBOX_RUNTIME_STATE}"
printf 'UNAVAILABLE\n' >"${LITE3_XBOX_STATUS_FILE:-/run/lite3-control/XBOX_STATUS}"
printf 'false\n' >"${LITE3_XBOX_BLUETOOTH_STATE_FILE:-/run/lite3-control/XBOX_BLUETOOTH_CONNECTED}"
printf 'false\n' >"${LITE3_XBOX_DEVICE_PRESENT_FILE:-/run/lite3-control/XBOX_DEVICE_PRESENT}"
printf 'false\n' >"${LITE3_XBOX_DEVICE_VALID_FILE:-/run/lite3-control/XBOX_DEVICE_VALID}"
