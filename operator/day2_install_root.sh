#!/usr/bin/env bash
""":"
Root-only install step for the already-staged Lite3 Day-2 bundle.
Installs packages and units, but deliberately leaves Nav2 and AUTONOMY stopped.
":"""
set -euo pipefail

[[ "$(hostname)" == "abx-fit-001" ]] || {
    echo "REFUSING: expected abx-fit-001" >&2
    exit 2
}

readonly bundle=/home/abx/day2-nav2-debs
readonly units=/home/abx/day2-systemd

cd "$bundle"
sha256sum -c SHA256SUMS
dpkg -i \
  ./ros-jazzy-costmap-queue_*.deb \
  ./ros-jazzy-dwb-core_*.deb \
  ./ros-jazzy-dwb-critics_*.deb \
  ./ros-jazzy-dwb-msgs_*.deb \
  ./ros-jazzy-dwb-plugins_*.deb \
  ./ros-jazzy-nav2-bt-navigator_*.deb \
  ./ros-jazzy-nav2-controller_*.deb \
  ./ros-jazzy-nav-2d-msgs_*.deb \
  ./ros-jazzy-nav-2d-utils_*.deb \
  ./ros-jazzy-nav2-navfn-planner_*.deb

install -m 0644 "$units/lite3-nav2.service" /etc/systemd/system/lite3-nav2.service
install -m 0644 "$units/lite3-nav2-safety-monitor.service" /etc/systemd/system/lite3-nav2-safety-monitor.service
install -m 0644 "$units/lite3-autonomy-command-source.service" /etc/systemd/system/lite3-autonomy-command-source.service

systemctl daemon-reload
systemctl disable lite3-nav2.service 2>/dev/null || true
systemctl stop lite3-nav2.service lite3-autonomy-command-source.service 2>/dev/null || true

echo "DAY2 ROOT INSTALL COMPLETE — NAV2/AUTONOMY STOPPED"
