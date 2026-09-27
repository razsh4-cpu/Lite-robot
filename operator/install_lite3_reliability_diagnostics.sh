#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run as root" >&2
    exit 2
fi

install -D -o root -g root -m 0755 \
    /home/abx/lite3_reliability_monitor.py \
    /usr/local/sbin/lite3-reliability-monitor
install -D -o root -g root -m 0644 \
    /home/abx/lite3-reliability-monitor.service \
    /etc/systemd/system/lite3-reliability-monitor.service
install -d -o root -g systemd-journal -m 2755 /var/log/journal
install -d -o root -g root -m 0755 /var/log/lite3-reliability
install -d -o root -g root -m 0755 /etc/systemd/journald.conf.d
install -o root -g root -m 0644 /dev/stdin \
    /etc/systemd/journald.conf.d/lite3-persistent.conf <<'EOF'
[Journal]
Storage=persistent
Compress=yes
SystemMaxUse=256M
RuntimeMaxUse=64M
MaxRetentionSec=14day
EOF
systemctl daemon-reload
systemctl restart systemd-journald.service
systemctl enable --now lite3-reliability-monitor.service
echo "LITE3 RELIABILITY DIAGNOSTICS INSTALLED"
echo "ROBOT MOTION COMMANDS SENT: NONE"
