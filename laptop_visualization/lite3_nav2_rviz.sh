#!/usr/bin/env bash
set -eo pipefail

readonly root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly config="${LITE3_RVIZ_CONFIG:-$root/lite3_remote_lidar.rviz}"
source "${LITE3_ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
set -u
export ROS_DOMAIN_ID=0
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4

[[ -r "$config" ]] || { echo "Nav2 RViz config missing: $config" >&2; exit 2; }

# Reuse the established single graphical unit. Stop the Day-1 view first so
# there can never be two RViz processes competing for the operator's attention.
systemctl --user stop lite3-rviz-watcher.service >/dev/null 2>&1 || true
pkill -u "$(id -u)" -f 'rviz2.*lite3_remote_lidar.rviz' >/dev/null 2>&1 || true
systemctl --user stop --no-block lite3-rviz-session.service >/dev/null 2>&1 || true
sleep 1
# RViz/Qt can occasionally hang while handling SIGTERM.  Bound shutdown so a
# stale visualization can never prevent the one intended instance starting.
systemctl --user kill --kill-whom=all --signal=SIGKILL \
  lite3-rviz-session.service >/dev/null 2>&1 || true
systemctl --user reset-failed lite3-rviz-session.service >/dev/null 2>&1 || true
exec systemd-run --user --unit=lite3-rviz-session --collect \
  --setenv=ROS_DOMAIN_ID=0 --setenv=ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET \
  --setenv=FASTDDS_BUILTIN_TRANSPORTS=UDPv4 \
  --setenv=LITE3_RVIZ_CONFIG="$config" \
  --setenv=LITE3_ROS_SETUP="${LITE3_ROS_SETUP:-/opt/ros/jazzy/setup.bash}" \
  "$root/lite3_nav2_rviz_session.sh"
