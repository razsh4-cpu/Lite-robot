#!/usr/bin/env bash
# Stage/build the tested Day-2 files, then install units. Starts no service.
set -euo pipefail

readonly project=/home/raz/ros-robot-cc
readonly robot="${LITE3_ROBOT_SSH:-abx@192.168.2.32}"

"$project/operator/stage_dds_runtime_fixes.sh"
ssh -t "$robot" 'sudo /home/abx/apply_dds_runtime_units.sh'
echo "DAY-2 PREPARATION INSTALLED — NO SERVICE STARTED; NO MOTION SENT"
