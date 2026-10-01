#!/usr/bin/env bash
set -euo pipefail

action="${1:-}"
root="${LITE3_REPO_ROOT:-/home/abx/Lite-robot}"
state_dir=/var/lib/lite3-control/phase3c
runtime_dir=/run/lite3-control
unit=lite3-nomad-teleop-adapter.service
legacy=lite3-laptop-xbox-source.service
blocked=nomad-bipolix-teleop-validator.service

[[ $EUID -eq 0 ]] || { echo "run as root" >&2; exit 2; }

assert_idle() {
  local source
  source="$(tr -d '[:space:]' <"$runtime_dir/COMMAND_SOURCE" 2>/dev/null || echo MISSING)"
  [[ "$source" == NONE ]] || { echo "BLOCKED: COMMAND_SOURCE=$source" >&2; exit 1; }
  /usr/bin/flock -n "$runtime_dir/owner.lock" true || {
    echo "BLOCKED: command-source lease is held" >&2; exit 1; }
}

record_state() {
  install -d -m 0755 "$state_dir"
  {
    echo "legacy_enabled=$(systemctl is-enabled --quiet "$legacy" && echo yes || echo no)"
    echo "legacy_active=$(systemctl is-active --quiet "$legacy" && echo yes || echo no)"
    echo "blocked_enabled=$(systemctl is-enabled --quiet "$blocked" && echo yes || echo no)"
    echo "blocked_active=$(systemctl is-active --quiet "$blocked" && echo yes || echo no)"
  } >"$state_dir/previous-services"
}

install_profile() {
  assert_idle
  record_state
  test -x /home/abx/ros2_ws/install/sensor_visualization/lib/sensor_visualization/lite3_nomad_teleop_adapter
  install -m 0644 "$root/onboard_ros2_ws/src/sensor_visualization/systemd/$unit" "/etc/systemd/system/$unit"
  install -d -m 0755 /etc/nomad
  {
    echo 'NOMAD_BIPOLIX_ROBOT_ID=robodog_01'
    echo 'NOMAD_BIPOLIX_MQTT_HOST=127.0.0.1'
    echo 'NOMAD_BIPOLIX_MQTT_PORT=1885'
    echo 'NOMAD_BIPOLIX_PHYSICAL_OUTPUT_ENABLED=false'
  } >/etc/nomad/bipolix-phase3c.env
  systemctl disable --now "$legacy" "$blocked" 2>/dev/null || true
  systemctl daemon-reload
  systemctl enable --now "$unit"
  systemctl is-active --quiet "$legacy" && { echo "legacy relay still active" >&2; exit 1; } || true
  systemctl is-active --quiet "$blocked" && { echo "motion-blocked validator still active" >&2; exit 1; } || true
  grep -q -- '--physical-output-enabled false' "/etc/systemd/system/$unit"
  echo 'PHASE 3C ADAPTER INSTALLED — PHYSICAL OUTPUT DISABLED'
}

restore_if_needed() {
  local name="$1" enabled="$2" active="$3"
  [[ "$enabled" == yes ]] && systemctl enable "$name" || true
  [[ "$active" == yes ]] && systemctl start "$name" || true
}

rollback_profile() {
  systemctl disable --now "$unit" 2>/dev/null || true
  sleep 1
  assert_idle
  # shellcheck disable=SC1091
  [[ -r "$state_dir/previous-services" ]] && source "$state_dir/previous-services"
  restore_if_needed "$legacy" "${legacy_enabled:-no}" "${legacy_active:-no}"
  restore_if_needed "$blocked" "${blocked_enabled:-no}" "${blocked_active:-no}"
  assert_idle
  echo 'PHASE 3C ROLLED BACK — COMMAND_SOURCE=NONE'
}

case "$action" in
  --install) install_profile ;;
  --rollback) rollback_profile ;;
  *) echo "usage: $0 --install|--rollback" >&2; exit 2 ;;
esac
