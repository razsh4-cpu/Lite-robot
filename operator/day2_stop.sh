#!/usr/bin/env bash
# Operator emergency stop for a Day-2 autonomous run.
set -euo pipefail

readonly robot="${LITE3_ROBOT_SSH:-abx@192.168.2.32}"
ssh -o BatchMode=yes -o ConnectTimeout=3 "$robot" \
  'sudo -n /usr/bin/systemctl stop lite3-autonomy-command-source.service; sleep 1; printf "COMMAND_SOURCE="; cat /run/lite3-control/COMMAND_SOURCE'
