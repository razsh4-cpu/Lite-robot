#!/usr/bin/env bash
set -u

PLAN="state_machine/supported_body_shift_plan.hpp"
BACKUP="/tmp/body_shift_65_65_15_original_$$.hpp"

cp "$PLAN" "$BACKUP" || exit 1

restore() {
    cp "$BACKUP" "$PLAN"
}

trap restore EXIT INT TERM

set_case() {
    local T="$1"

    cp "$BACKUP" "$PLAN"

    python3 - "$PLAN" "$T" <<'PY'
from pathlib import Path
import re, sys

p = Path(sys.argv[1])
t = float(sys.argv[2])
s = p.read_text()

values = {
    "kShiftXM": 0.065,
    "kShiftYM": 0.065,
    "kUnloadM": 0.015,
    "kShiftSeconds": t,
    "kRecenterSeconds": t,
}

for name, value in values.items():
    pattern = rf'(static\s+constexpr\s+double\s+{name}\s*=\s*)[-+0-9.eE]+(\s*;)'
    s, n = re.subn(
        pattern,
        rf'\g<1>{value:.3f}\2',
        s,
        count=1
    )
    if n != 1:
        raise SystemExit(f"Could not update {name}")

p.write_text(s)
PY
}

echo "======================================================"
echo " TARGET TEST: SHIFT 65/65 mm + FR LIFT 15 mm"
echo " Limits remain unchanged: delta=0.30 speed=0.12"
echo "======================================================"
echo

for T in 4.6 5.0 5.5 6.0; do

    echo "------------------------------------------------------"
    echo "Testing shift/recenter = ${T}s"
    echo "------------------------------------------------------"

    set_case "$T"

    if ! cmake --build build -j"$(nproc)" \
        --target supported_body_shift_plan_test supported_body_shift_once_test \
        >/dev/null 2>&1; then
        echo "BUILD FAIL"
        continue
    fi

    PLAN_OUT="$(./build/supported_body_shift_plan_test 2>&1)"
    PLAN_RC=$?

    echo "$PLAN_OUT" | grep -E 'MEASURED|FAIL|PASS' || true

    if [ "$PLAN_RC" -ne 0 ]; then
        echo "RESULT: PLAN FAIL"
        echo
        continue
    fi

    INERT_OUT="$(./build/supported_body_shift_once_test 2>&1)"
    INERT_RC=$?

    if [ "$INERT_RC" -eq 0 ]; then
        echo "RESULT: PLAN PASS + INERT PASS"
        echo
        echo "*** 65/65/15 OFFLINE CANDIDATE FOUND at ${T}s ***"
        echo
        break
    else
        echo "$INERT_OUT" | grep -E \
            'BODY_SHIFT_BOUND_FAIL|FAIL|INVALID_COMMAND' | tail -5
        echo "RESULT: INERT FAIL"
        echo
    fi
done

echo
echo "Restoring original configuration..."
restore

cmake --build build -j"$(nproc)" \
    --target supported_body_shift_plan_test supported_body_shift_once_test \
    >/dev/null 2>&1 || true

echo "Original configuration restored."
echo "DONE"
