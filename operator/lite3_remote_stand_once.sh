#!/usr/bin/env bash
set -eo pipefail

export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
source /opt/ros/jazzy/setup.bash
set -u

readonly state_dir=/run/lite3-control
readonly request_topic=/c2/robot_01/laptop_xbox/request
readonly heartbeat_topic=/c2/robot_01/laptop_xbox/heartbeat
readonly joy_topic=/c2/robot_01/laptop_xbox/joy
readonly unit=lite3-high-level-runtime.service
readonly neutral='{axes: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], buttons: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}'
readonly stand_edge='{axes: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], buttons: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}'

pids=()
cleanup() {
  for pid in "${pids[@]}"; do
    kill "$pid" >/dev/null 2>&1 || true
  done
  wait >/dev/null 2>&1 || true
  timeout 4 ros2 topic pub --once "$request_topic" std_msgs/msg/Bool \
    '{data: false}' >/dev/null 2>&1 || true
  timeout 4 ros2 topic pub --once "$heartbeat_topic" std_msgs/msg/Bool \
    '{data: false}' >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

[[ "$(cat "$state_dir/COMMAND_SOURCE" 2>/dev/null)" == NONE ]] || {
  echo 'STAND BLOCKED: COMMAND_SOURCE is not NONE' >&2
  exit 2
}
systemctl is-active --quiet "$unit" || {
  echo 'STAND BLOCKED: HIGH-LEVEL runtime is not active' >&2
  exit 2
}

latest="$(journalctl --no-pager --since '20 seconds ago' -u "$unit" \
  | grep 'robot_status=' | tail -1 || true)"
[[ "$latest" == *'robot_status=sitting'* && "$latest" == *'telemetry_fresh=true'* ]] || {
  echo 'STAND BLOCKED: fresh telemetry does not explicitly report sitting' >&2
  exit 3
}

ros2 topic pub -r 20 "$request_topic" std_msgs/msg/Bool '{data: true}' \
  >/dev/null 2>&1 & pids+=("$!")
ros2 topic pub -r 20 "$heartbeat_topic" std_msgs/msg/Bool '{data: true}' \
  >/dev/null 2>&1 & pids+=("$!")
ros2 topic pub -r 20 "$joy_topic" sensor_msgs/msg/Joy "$neutral" \
  >/dev/null 2>&1 & pids+=("$!")

# Fast DDS discovery on the robot Wi-Fi can take 10-15 seconds after boot.
# Keep publishing only request/heartbeat/neutral while waiting; no motion edge
# is sent until the lease is visibly owned.
for _ in $(seq 1 450); do
  [[ "$(cat "$state_dir/COMMAND_SOURCE" 2>/dev/null)" == LAPTOP_XBOX ]] && break
  sleep 0.1
done
[[ "$(cat "$state_dir/COMMAND_SOURCE" 2>/dev/null)" == LAPTOP_XBOX ]] || {
  echo 'STAND BLOCKED: C2 lease was not acquired' >&2
  exit 4
}

# Establish neutral first, then exactly one A rising edge, then neutral again.
sleep 0.5
kill "${pids[2]}" >/dev/null 2>&1 || true
wait "${pids[2]}" >/dev/null 2>&1 || true
timeout 1 ros2 topic pub -r 20 "$joy_topic" sensor_msgs/msg/Joy "$stand_edge" \
  >/dev/null 2>&1 || true
ros2 topic pub -r 20 "$joy_topic" sensor_msgs/msg/Joy "$neutral" \
  >/dev/null 2>&1 & pids[2]="$!"

deadline=$((SECONDS + 20))
while (( SECONDS < deadline )); do
  if journalctl --no-pager --since '25 seconds ago' -u "$unit" \
      | grep -q 'robot_status=standing.*telemetry_fresh=true'; then
    echo 'STAND CONFIRMED: telemetry robot_status=standing'
    exit 0
  fi
  sleep 0.5
done

echo 'STAND FAILED: standing telemetry was not confirmed' >&2
exit 5
