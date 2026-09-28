#!/usr/bin/env bash
# Idempotent crash/stop cleanup for the optional AUTONOMY adapter.
set -euo pipefail

readonly state_dir="${LITE3_STATE_DIR:-/run/lite3-control}"
readonly source_file="$state_dir/COMMAND_SOURCE"
readonly lock_file="$state_dir/owner.lock"
readonly test_override="$state_dir/NAV_TEST_OVERRIDE.json"

# Every service stop/failure restores the normal 80% x3 gate.
rm -f -- "$test_override"

[[ -d "$state_dir" && -e "$source_file" && -e "$lock_file" ]] || exit 0

# A live owner holds this lock. Never alter its selected source.
exec 9<>"$lock_file"
flock -n 9 || exit 0
if [[ "$(head -n 1 "$source_file" 2>/dev/null || true)" == "AUTONOMY" ]]; then
    printf 'NONE\n' >"$source_file"
    printf 'AUTONOMY cleanup: COMMAND_SOURCE=NONE\n'
fi
