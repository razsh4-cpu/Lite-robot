#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "run with sudo" >&2
    exit 2
fi

stop_if_loaded() {
    local unit="$1"
    if systemctl list-unit-files "$unit" --no-legend 2>/dev/null | grep -q "$unit"; then
        systemctl stop "$unit"
    fi
}

case "${1:-}" in
    NONE)
        stop_if_loaded lite3-local-xbox-control.service
        stop_if_loaded lite3-laptop-xbox-control.service
        stop_if_loaded lite3-autonomy.service
        ;;
    LOCAL_XBOX)
        stop_if_loaded lite3-autonomy.service
        stop_if_loaded lite3-laptop-xbox-control.service
        systemctl start lite3-local-xbox-control.service
        ;;
    AUTONOMY)
        stop_if_loaded lite3-local-xbox-control.service
        stop_if_loaded lite3-laptop-xbox-control.service
        systemctl start lite3-autonomy.service
        ;;
    LAPTOP_XBOX)
        stop_if_loaded lite3-local-xbox-control.service
        stop_if_loaded lite3-autonomy.service
        systemctl start lite3-laptop-xbox-control.service
        ;;
    *)
        echo "usage: $0 NONE|AUTONOMY|LOCAL_XBOX|LAPTOP_XBOX" >&2
        exit 2
        ;;
esac
