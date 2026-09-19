#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

PLAN="state_machine/supported_body_shift_plan.hpp"
BACKUP="/tmp/body_shift_matrix_original_$$.hpp"
RESULTS="/tmp/body_shift_matrix_results_$$.csv"

cp "$PLAN" "$BACKUP" || exit 1

restore() {
    cp "$BACKUP" "$PLAN"
}

cleanup() {
    restore
    cmake --build build -j"$(nproc)" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

# X,Y configurations in meters.
CASES=(
    "0.060 0.050"
    "0.060 0.060"
    "0.065 0.050"
    "0.065 0.060"
    "0.065 0.065"
)

# FR lift heights in meters.
LIFTS=(
    "0.010"
    "0.020"
    "0.030"
)

echo "x_mm,y_mm,lift_mm,result,max_delta_rad,delta_limit_rad,max_speed_rad_s,speed_limit_rad_s" > "$RESULTS"

echo "=============================================================="
echo " LITE3 BODY-SHIFT + FR-LIFT OFFLINE MATRIX"
echo "=============================================================="
echo
echo "15 configurations:"
echo "  shifts: 60/50  60/60  65/50  65/60  65/65 mm"
echo "  lifts : 10  20  30 mm"
echo
echo "NO HARDWARE"
echo "NO SAFETY LIMIT CHANGES"
echo "=============================================================="
echo

set_case() {
    local X="$1"
    local Y="$2"
    local LIFT="$3"

    # Always start from the exact original file so changes cannot accumulate.
    cp "$BACKUP" "$PLAN"

    python3 - "$PLAN" "$X" "$Y" "$LIFT" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
x = float(sys.argv[2])
y = float(sys.argv[3])
lift = float(sys.argv[4])

s = path.read_text()

patterns = [
    (
        r'(static\s+constexpr\s+double\s+kShiftXM\s*=\s*)[-+0-9.eE]+(\s*;)',
        rf'\g<1>{x:.3f}\2'
    ),
    (
        r'(static\s+constexpr\s+double\s+kShiftYM\s*=\s*)[-+0-9.eE]+(\s*;)',
        rf'\g<1>{y:.3f}\2'
    ),
    (
        r'(static\s+constexpr\s+double\s+kUnloadM\s*=\s*)[-+0-9.eE]+(\s*;)',
        rf'\g<1>{lift:.3f}\2'
    ),
]

for pattern, replacement in patterns:
    s2, n = re.subn(pattern, replacement, s, count=1)
    if n != 1:
        raise SystemExit(f"Could not update: {pattern}")
    s = s2

path.write_text(s)
PY
}

run_case() {
    local X="$1"
    local Y="$2"
    local LIFT="$3"

    local XMM YMM LMM
    XMM="$(python3 -c "print(int(round(float('$X')*1000)))")"
    YMM="$(python3 -c "print(int(round(float('$Y')*1000)))")"
    LMM="$(python3 -c "print(int(round(float('$LIFT')*1000)))")"

    printf "%-18s" "${XMM}/${YMM} lift=${LMM}:"

    if ! set_case "$X" "$Y" "$LIFT"; then
        echo " CONFIG FAIL"
        echo "$XMM,$YMM,$LMM,CONFIG_FAIL,,,,">>"$RESULTS"
        return
    fi

    # Build only the two relevant offline test targets.
    if ! cmake --build build -j"$(nproc)" \
        --target supported_body_shift_plan_test supported_body_shift_once_test \
        >/tmp/body_shift_matrix_build.log 2>&1; then

        echo " BUILD FAIL"
        echo "$XMM,$YMM,$LMM,BUILD_FAIL,,,,">>"$RESULTS"
        return
    fi

    local OUT RC
    OUT="$(./build/supported_body_shift_plan_test 2>&1)"
    RC=$?

    local LINE
    LINE="$(echo "$OUT" | grep 'MEASURED' | tail -1)"

    local DELTA DLIM SPEED SLIM
    DELTA="$(echo "$LINE" | sed -n 's/.*max_delta=\([^ ]*\).*/\1/p')"
    SPEED="$(echo "$LINE" | sed -n 's/.*max_speed=\([^ ]*\).*/\1/p')"
    DLIM="$(echo "$LINE" | sed -n 's/.*limits: delta=\([^ ]*\).*/\1/p')"
    SLIM="$(echo "$LINE" | sed -n 's/.*speed=\([^ ]*\)$/\1/p')"

    if [ "$RC" -ne 0 ]; then
        echo " FAIL  delta=${DELTA:-?}/${DLIM:-?} speed=${SPEED:-?}/${SLIM:-?}"
        echo "$XMM,$YMM,$LMM,PLAN_FAIL,$DELTA,$DLIM,$SPEED,$SLIM" >> "$RESULTS"
        return
    fi

    # Plan passed; now test the inert state-machine path as well.
    local ONCE RC2
    ONCE="$(./build/supported_body_shift_once_test 2>&1)"
    RC2=$?

    if [ "$RC2" -ne 0 ]; then
        echo " INERT FAIL  delta=${DELTA:-?}/${DLIM:-?} speed=${SPEED:-?}/${SLIM:-?}"
        echo "$XMM,$YMM,$LMM,INERT_FAIL,$DELTA,$DLIM,$SPEED,$SLIM" >> "$RESULTS"
        return
    fi

    echo " PASS  delta=${DELTA}/${DLIM} speed=${SPEED}/${SLIM}"
    echo "$XMM,$YMM,$LMM,PASS,$DELTA,$DLIM,$SPEED,$SLIM" >> "$RESULTS"
}

for CASE in "${CASES[@]}"; do
    read -r X Y <<< "$CASE"

    for LIFT in "${LIFTS[@]}"; do
        run_case "$X" "$Y" "$LIFT"
    done
done

echo
echo "=============================================================="
echo " RESULTS"
echo "=============================================================="

python3 - "$RESULTS" <<'PY'
import csv
import sys

path = sys.argv[1]

with open(path, newline="") as f:
    rows = list(csv.DictReader(f))

print()
print(f"{'SHIFT':<10} {'LIFT':<8} {'RESULT':<12} {'DELTA':<17} {'SPEED':<17}")
print("-" * 70)

for r in rows:
    shift = f"{r['x_mm']}/{r['y_mm']}"
    lift = f"{r['lift_mm']}mm"
    delta = (
        f"{r['max_delta_rad']}/{r['delta_limit_rad']}"
        if r['max_delta_rad'] else "-"
    )
    speed = (
        f"{r['max_speed_rad_s']}/{r['speed_limit_rad_s']}"
        if r['max_speed_rad_s'] else "-"
    )

    print(
        f"{shift:<10} "
        f"{lift:<8} "
        f"{r['result']:<12} "
        f"{delta:<17} "
        f"{speed:<17}"
    )

passed = [r for r in rows if r["result"] == "PASS"]

print()
print(f"PASS: {len(passed)}/{len(rows)}")

if passed:
    print()
    print("Offline-valid configurations:")
    for r in passed:
        print(
            f"  {r['x_mm']}/{r['y_mm']} mm "
            f"+ FR lift {r['lift_mm']} mm"
        )
PY

echo
echo "CSV: $RESULTS"
echo
echo "Restoring original experiment..."

restore
trap - EXIT INT TERM

cmake --build build -j"$(nproc)" \
    --target supported_body_shift_plan_test supported_body_shift_once_test \
    >/dev/null 2>&1 || {
        echo "WARNING: original source restored, but restore build failed."
        exit 70
    }

echo "Original source + build restored."
echo
echo "=============================================================="
echo " SWEEP COMPLETE — NO HARDWARE WAS USED"
echo "=============================================================="
