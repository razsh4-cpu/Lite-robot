#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    echo "Run with sudo: sudo /home/abx/apply_lite3_headless.sh" >&2
    exit 2
fi

readonly staging_dir="/home/abx/lite3-headless-staging"
install -m 0755 "$staging_dir/lite3_headless_admin.sh" /usr/local/sbin/lite3-headless
install -m 0644 "$staging_dir/lite3-realsense.service" /etc/systemd/system/lite3-realsense.service
systemctl daemon-reload
/usr/local/sbin/lite3-headless apply

echo "ROLLBACK: sudo lite3-headless graphical-default"
echo "DO NOT REBOOT UNTIL THE OPERATOR APPROVES THE CONTROLLED REBOOT"
