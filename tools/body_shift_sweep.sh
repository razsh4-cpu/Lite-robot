#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

PLAN="state_machine/supported_body_shift_plan.hpp"
BACKUP="/tmp/body_shift_plan_before_sweep_$$.hpp"

cp "$PLAN" "$BACKUP"

restore() {
    cp "$BACKUP" "$PLAN"
}
trap restore EXIT

run_case() {
    X="$1"
    Y="$2"

    cp "$BACKUP" "$PLAN"

    python3 - "$PLAN" "$X" "$Y" <<'PY'
from pathlib import Path
import re, sys

p = Path(sys.argv[1])
x = float(sys.argv[2])
y = float(sys.argv[3])

s = p.read_text()

s, nx = re.subn(
    r'kShiftXM\s*=\s*[0-9.]+',
    f'kShiftXM = {x:.3f}',
    s,
    count=1
)

s, ny = re.subn(
    r'kShiftYM\s*=\s*[0-9.]+',
    f'kShiftYM = {y:.3f}',
    s,
    count=1
)

if nx != 1 or ny != 1:
    raise SystemExit("Failed to update X/Y")

p.write_text(s)
PY

    cmake --build build -j"$(nproc)" >/dev/null 2>&1 || {
        echo "$X/$Y : BUILD FAIL"
        return
    }

    OUT="$(./build/supported_body_shift_plan_test 2>&1)"
    RC=$?

    MEASURED="$(echo "$OUT" | grep 'MEASURED' | tail -1)"

    if [ "$RC" -eq 0 ]; then
        echo "$X/$Y : PASS | $MEASURED"
    else
        echo "$X/$Y : FAIL | $MEASURED"
    fi
}

echo "=============================================="
echo " BODY SHIFT OFFLINE SWEEP — FR LIFT 10 mm"
echo "=============================================="
echo

run_case 0.060 0.050
run_case 0.060 0.060
run_case 0.065 0.050
run_case 0.065 0.060
run_case 0.065 0.065

echo
echo "Restoring current 60/50 configuration..."
restore

cmake --build build -j"$(nproc)" >/dev/null 2>&1

echo "DONE — original plan restored."
