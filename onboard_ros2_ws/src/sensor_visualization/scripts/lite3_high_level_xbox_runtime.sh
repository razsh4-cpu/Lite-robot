#!/usr/bin/env bash
set -eo pipefail

readonly state_dir="${LITE3_STATE_DIR:-/run/lite3-control}"
readonly joystick="${LITE3_XBOX_DEVICE:-/dev/input/js0}"
readonly validator="${LITE3_XBOX_VALIDATOR:-/home/abx/ros2_ws/install/sensor_visualization/lib/sensor_visualization/lite3_xbox_device_valid}"

mkdir -p "$state_dir"
"$validator" "$joystick"
exec 9>"$state_dir/owner.lock"
if ! flock -n 9; then
    echo "lite3-local-xbox-input: command-source lease is already owned" >&2
    exit 3
fi

printf 'LOCAL_XBOX\n' >"$state_dir/COMMAND_SOURCE"
printf 'true\n' >"$state_dir/MANUAL_CONTROL_AVAILABLE"
echo "lite3-local-xbox-input: lease acquired; robot transport remains independent"

child=""
cleanup() {
    printf 'false\n' >"$state_dir/MANUAL_CONTROL_AVAILABLE"
    printf 'NONE\n' >"$state_dir/COMMAND_SOURCE"
    if [[ -n "$child" ]] && kill -0 "$child" 2>/dev/null; then
        kill -TERM "$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
    fi
    echo "lite3-local-xbox-input: stopped; command source released; robot runtime retained"
}
trap cleanup EXIT INT TERM

source /opt/ros/jazzy/setup.bash
source /home/abx/ros2_ws/install/setup.bash
set -u
ros2 launch sensor_visualization lite3_local_xbox_input.launch.py device_id:=0 &
child=$!

while kill -0 "$child" 2>/dev/null; do
    if ! "$validator" "$joystick"; then
        echo "lite3-local-xbox-input: Xbox disconnected; releasing LOCAL_XBOX" >&2
        exit 0
    fi
    sleep 0.10
done
wait "$child"
