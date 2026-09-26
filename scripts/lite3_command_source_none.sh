#!/usr/bin/env bash
set -u

readonly lock_file="${1:-/run/lite3-control/owner.lock}"
mkdir -p "$(dirname "$lock_file")" 2>/dev/null || true
exec flock -n "$lock_file" true
