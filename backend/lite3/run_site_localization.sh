#!/usr/bin/env bash
set -eo pipefail
: "${LITE3_SITE_MAP:?existing site map required}"
: "${LITE3_SITE_POSE:?existing per-map hypothesis path required}"
exec ros2 launch lite3_state_estimation day1_localization.launch.py \
  map:="$LITE3_SITE_MAP" pose_file:="$LITE3_SITE_POSE" minimum_match_fraction:=0.80
