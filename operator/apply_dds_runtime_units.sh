#!/usr/bin/env bash
# Install already-staged Lite3 DDS/runtime unit files on abx-fit-001.
#
# This script intentionally does not start, stop, restart, or enable services.
# It sends no robot command. Run it as root after stage_dds_runtime_fixes.sh.
set -euo pipefail

[[ "$(hostname)" == "abx-fit-001" ]] || {
    echo "REFUSING: expected abx-fit-001" >&2
    exit 2
}

readonly staged=/home/abx/lite3-dds-systemd
readonly units=(
    lite3-high-level-runtime.service
    lite3-localization.service
    lite3-nav2.service
    lite3-nav2-safety-monitor.service
    lite3-autonomy-command-source.service
    lite3-laptop-xbox-source.service
    lite3-mapping.service
    lite3-system-health.service
)

for unit in "${units[@]}"; do
    [[ -s "$staged/$unit" ]] || {
        echo "MISSING STAGED UNIT: $staged/$unit" >&2
        exit 3
    }
    grep -q '^Environment=FASTDDS_BUILTIN_TRANSPORTS=UDPv4$' "$staged/$unit" || {
        echo "REFUSING: UDPv4 environment missing from $unit" >&2
        exit 4
    }
done

for unit in "${units[@]}"; do
    install -m 0644 "$staged/$unit" "/etc/systemd/system/$unit"
done

readonly sudoers=/etc/sudoers.d/lite3-day2-control
printf '%s\n' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl start lite3-nav2.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl stop lite3-nav2.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl restart lite3-nav2.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl start lite3-autonomy-command-source.service' \
    'abx ALL=(root) NOPASSWD: /usr/bin/systemctl stop lite3-autonomy-command-source.service' \
    > "$sudoers"
chmod 0440 "$sudoers"
visudo -cf "$sudoers" >/dev/null

systemctl daemon-reload
echo "DDS RUNTIME UNITS AND DAY-2 STOP PERMISSIONS INSTALLED"
echo "SERVICES CHANGED: NONE"
echo "HARDWARE COMMANDS SENT: NONE"
