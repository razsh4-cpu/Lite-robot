#!/usr/bin/env bash
set -eo pipefail
state=/run/lite3-control
marker="$state/RELOCALIZATION_ACTIVE"
source /opt/ros/jazzy/setup.bash
source /home/abx/ros2_ws/install/setup.bash
source /home/abx/Desktop/robotdog_ws/install/setup.bash
export ROS_DOMAIN_ID=0 ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET FASTDDS_BUILTIN_TRANSPORTS=UDPv4
export LITE3_RELOCALIZATION_APPROVED=1
cleanup() {
  set +e
  [[ -n "${adapter_pid:-}" ]] && kill -TERM "$adapter_pid" 2>/dev/null
  [[ -n "${adapter_pid:-}" ]] && wait "$adapter_pid" 2>/dev/null
  rm -f "$marker"
  /home/abx/Desktop/robotdog_ws/install/sensor_visualization/lib/sensor_visualization/lite3_release_autonomy
}
trap cleanup EXIT INT TERM
[[ "$(cat "$state/COMMAND_SOURCE" 2>/dev/null || true)" == NONE ]]
printf '%s
' "$$" >"$marker"
ros2 run sensor_visualization lite3_autonomy_command_source --ros-args   -p relocalization_mode:=true   -p input_topic:=/lite3/relocalization/cmd_vel   -p startup_timeout_s:=20.0   -p command_timeout_s:=0.30   -p max_forward:=0.0 -p max_lateral:=0.03 -p max_yaw:=0.0 &
adapter_pid=$!
deadline=$((SECONDS + 12))
while (( SECONDS < deadline )); do
  [[ "$(cat "$state/COMMAND_SOURCE" 2>/dev/null || true)" == AUTONOMY ]] && break
  kill -0 "$adapter_pid" 2>/dev/null || { echo 'RELOCALIZATION BLOCKED: adapter exited'; exit 2; }
  sleep 0.2
done
[[ "$(cat "$state/COMMAND_SOURCE" 2>/dev/null || true)" == AUTONOMY ]] || {
  echo 'RELOCALIZATION BLOCKED: lease unavailable'; exit 2;
}
ros2 run sensor_visualization lite3_relocalization_motion
