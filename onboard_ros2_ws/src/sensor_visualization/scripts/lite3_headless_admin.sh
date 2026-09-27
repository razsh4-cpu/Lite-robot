#!/usr/bin/env bash
set -euo pipefail

readonly state_dir="/var/lib/lite3-headless"
readonly critical_units=(
    NetworkManager.service
    ssh.service
    lite3-ros-network-ready.service
    lite3-high-level-runtime.service
    lite3-lidar.service
    lite3-localization.service
    lite3-laptop-xbox-source.service
    lite3-system-health.service
)

usage() {
    cat <<'EOF'
Usage: lite3-headless <command>

  status              Show boot target, GUI state and robot service state
  apply               Select headless boot and make RealSense on-demand
  start-gui           Start the installed graphical desktop for recovery
  stop-gui            Return the current boot to headless mode
  graphical-default   Restore graphical boot as the default
  headless-default    Restore headless boot as the default
  realsense-start      Start the optional RealSense service on demand
  realsense-stop       Stop the optional RealSense service
EOF
}

require_root() {
    if [[ "$EUID" -ne 0 ]]; then
        echo "ERROR: this command requires sudo" >&2
        exit 2
    fi
}

unit_enabled_or_static() {
    local state
    state="$(systemctl is-enabled "$1" 2>/dev/null || true)"
    [[ "$state" == "enabled" || "$state" == "static" || "$state" == "indirect" ]]
}

record_snapshot() {
    local destination="$1"
    {
        date --iso-8601=seconds
        echo "DEFAULT_TARGET=$(systemctl get-default)"
        uptime
        free -h
        cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
        ps -eo pid,pcpu,pmem,rss,comm,args --sort=-pcpu | sed -n '1,20p'
        ps -eo pid,pcpu,pmem,rss,comm,args --sort=-rss | sed -n '1,20p'
    } >"$destination"
}

show_status() {
    echo "BOOT_DEFAULT=$(systemctl get-default)"
    if systemctl is-active --quiet graphical.target; then
        echo "GRAPHICAL_SESSION=ACTIVE"
    else
        echo "GRAPHICAL_SESSION=INACTIVE"
    fi
    echo "REALSENSE_AUTOSTART=$(systemctl is-enabled lite3-realsense.service 2>/dev/null || true)"
    echo "REALSENSE_STATE=$(systemctl is-active lite3-realsense.service 2>/dev/null || true)"
    for unit in "${critical_units[@]}"; do
        printf '%-42s %s\n' "$unit" "$(systemctl is-active "$unit" 2>/dev/null || true)"
    done
    echo "GUI_PROCESSES"
    pgrep -af 'Xorg|lightdm|cinnamon|xfce4-session|rviz2|firefox|chromium' || echo "none"
}

apply_headless() {
    require_root
    mkdir -p "$state_dir"
    if [[ ! -e "$state_dir/previous-default-target" ]]; then
        systemctl get-default >"$state_dir/previous-default-target"
    fi
    record_snapshot "$state_dir/before-headless.txt"

    for unit in "${critical_units[@]}"; do
        if ! unit_enabled_or_static "$unit"; then
            echo "ERROR: required unit is not enabled/static: $unit" >&2
            exit 1
        fi
    done

    # Change the next boot only. Do not stop the currently running camera or
    # graphical session before the controlled reboot validation.
    systemctl disable lite3-realsense.service >/dev/null 2>&1 || true
    systemctl set-default multi-user.target
    echo "HEADLESS DEFAULT PREPARED — REBOOT REQUIRED"
    echo "CURRENT SERVICES STOPPED: NONE"
    echo "HARDWARE MOTION COMMANDS SENT: NONE"
}

case "${1:-}" in
    status) show_status ;;
    apply) apply_headless ;;
    start-gui) require_root; systemctl start graphical.target ;;
    stop-gui) require_root; systemctl isolate multi-user.target ;;
    graphical-default) require_root; systemctl set-default graphical.target ;;
    headless-default) require_root; systemctl set-default multi-user.target ;;
    realsense-start) require_root; systemctl start lite3-realsense.service ;;
    realsense-stop) require_root; systemctl stop lite3-realsense.service ;;
    *) usage; exit 2 ;;
esac
