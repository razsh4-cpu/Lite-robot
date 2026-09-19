#!/usr/bin/env bash
set -u

PLAN="state_machine/supported_body_shift_plan.hpp"
BACKUP="/tmp/fr_lift_sweep_original_$$.hpp"

cp "$PLAN" "$BACKUP" || exit 1

restore() {
    cp "$BACKUP" "$PLAN"
}
trap restore EXIT INT TERM

set_lift() {
    python3 - "$PLAN" "$1" <<'PY'
from pathlib import Path
import re, sys

p = Path(sys.argv[1])
lift = float(sys.argv[2])
s = p.read_text()

s, n = re.subn(
    r'(kUnloadM\s*=\s*)[-+0-9.eE]+',
    rf'\g<1>{lift:.3f}',
    s,
    count=1
)

if n != 1:
    raise SystemExit("Could not change kUnloadM")

p.write_text(s)
PY
}

echo "===================================================="
echo " FR LIFT SWEEP — SHIFT FIXED AT CURRENT 60/50"
echo "===================================================="
echo

printf "%-8s %-12s %-12s\n" "LIFT" "PLAN" "INERT"
printf "%-8s %-12s %-12s\n" "----" "----" "-----"

for LIFT in 0.010 0.020 0.030; do

    restore
    set_lift "$LIFT"

    MM=$(python3 -c "print(int(round($LIFT*1000)))")

    if ! cmake --build build -j"$(nproc)" \
        --target supported_body_shift_plan_test supported_body_shift_once_test \
        >/dev/null 2>&1; then
        printf "%-8s %-12s %-12s\n" "${MM}mm" "BUILD_FAIL" "-"
        continue
    fi

    PLAN_OUT=$(./build/supported_body_shift_plan_test 2>&1)
    PLAN_RC=$?

    if [ "$PLAN_RC" -ne 0 ]; then
        printf "%-8s %-12s %-12s\n" "${MM}mm" "FAIL" "-"
        echo "  $PLAN_OUT" | grep -E 'MEASURED|FAIL' || true
        continue
    fi

    INERT_OUT=$(./build/supported_body_shift_once_test 2>&1)
    INERT_RC=$?

    if [ "$INERT_RC" -eq 0 ]; then
        printf "%-8s %-12s %-12s\n" "${MM}mm" "PASS" "PASS"
    else
        printf "%-8s %-12s %-12s\n" "${MM}mm" "PASS" "FAIL"
        echo "$INERT_OUT" | grep -E \
        'BODY_SHIFT_BOUND_FAIL|FAIL|INVALID_COMMAND' | tail -3
    fi
done

echo
echo "Restoring baseline..."
restore

cmake --build build -j"$(nproc)" \
    --target supported_body_shift_plan_test supported_body_shift_once_test \
    >/dev/null 2>&1

echo
echo "Baseline restored:"
grep -nE \
'kShiftXM|kShiftYM|kUnloadM|kShiftSeconds|kRecenterSeconds|kMaxJointDeltaRad|kMaxTargetSpeedRadS' \
"$PLAN"

echo
echo "DONE"
