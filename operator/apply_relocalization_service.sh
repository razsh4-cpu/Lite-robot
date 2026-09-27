#!/usr/bin/env bash
set -euo pipefail
[[ "$(hostname)" == "abx-fit-001" ]] || { echo "WRONG HOST"; exit 2; }
[[ "$(cat /run/lite3-control/COMMAND_SOURCE 2>/dev/null || true)" == "NONE" ]] || {
  echo "BLOCKED: COMMAND_SOURCE is not NONE"; exit 2;
}
remote_pkg=/home/abx/Desktop/robotdog_ws/src/src/sensor_visualization
install -m 0644 "$remote_pkg/systemd/lite3-relocalization-motion.service" /etc/systemd/system/lite3-relocalization-motion.service
cat >/etc/sudoers.d/lite3-relocalization-control <<'RULES'
abx ALL=(root) NOPASSWD: /usr/bin/systemctl start lite3-relocalization-motion.service
abx ALL=(root) NOPASSWD: /usr/bin/systemctl stop lite3-relocalization-motion.service
RULES
chmod 0440 /etc/sudoers.d/lite3-relocalization-control
visudo -cf /etc/sudoers.d/lite3-relocalization-control
systemctl daemon-reload
systemctl disable lite3-relocalization-motion.service 2>/dev/null || true
systemctl restart lite3-nav2-safety-monitor.service
echo "RELOCALIZATION SERVICE INSTALLED — NOT STARTED"
echo "HARDWARE MOTION COMMANDS SENT: NONE"
