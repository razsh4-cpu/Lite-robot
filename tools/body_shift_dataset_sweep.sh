#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

PLAN="state_machine/supported_body_shift_plan.hpp"
BACKUP="/tmp/body_shift_dataset_original_$$.hpp"
RESULTS="/tmp/body_shift_dataset_$(date +%Y%m%d_%H%M%S).csv"

cp "$PLAN" "$BACKUP" || exit 1

restore() {
    cp "$BACKUP" "$PLAN"
}

cleanup() {
    restore
}
trap cleanup EXIT INT TERM

X_VALUES=(0.040 0.050 0.055 0.060 0.065)
Y_VALUES=(0.020 0.030 0.040 0.050 0.060 0.065)
LIFTS=(0.000 0.010 0.020 0.030)

echo "x_mm,y_mm,lift_mm,plan,inert,max_delta,delta_limit,max_speed,speed_limit,bound_fail" > "$RESULTS"

TOTAL=$((${#X_VALUES[@]} * ${#Y_VALUES[@]} * ${#LIFTS[@]}))
N=0
PASS_COUNT=0

set_case() {
python3 - "$PLAN" "$1" "$2" "$3" <<'PY'
from pathlib import Path
import re, sys

p = Path(sys.argv[1])
x, y, lift = map(float, sys.argv[2:5])
s = p.read_text()

changes = {
    "kShiftXM": x,
    "kShiftYM": y,
    "kUnloadM": lift,
}

for name, value in changes.items():
    pattern = rf'(static\s+constexpr\s+double\s+{name}\s*=\s*)[-+0-9.eE]+(\s*;)'
    s, n = re.subn(pattern, rf'\g<1>{value:.3f}\2', s, count=1)
    if n != 1:
        raise SystemExit(f"Could not update {name}")

p.write_text(s)
PY
}

for X in "${X_VALUES[@]}"; do
for Y in "${Y_VALUES[@]}"; do
for LIFT in "${LIFTS[@]}"; do

    N=$((N+1))

    XMM=$(python3 -c "print(int(round($X*1000)))")
    YMM=$(python3 -c "print(int(round($Y*1000)))")
    LMM=$(python3 -c "print(int(round($LIFT*1000)))")

    printf "[%3d/%3d] %2d/%2d lift=%2d mm  " \
        "$N" "$TOTAL" "$XMM" "$YMM" "$LMM"

    restore

    if ! set_case "$X" "$Y" "$LIFT"; then
        echo "CONFIG_FAIL"
        echo "$XMM,$YMM,$LMM,CONFIG_FAIL,-,-,-,-,-,-" >> "$RESULTS"
        continue
    fi

    if ! cmake --build build -j"$(nproc)" \
        --target supported_body_shift_plan_test supported_body_shift_once_test \
        >/dev/null 2>&1; then

        echo "BUILD_FAIL"
        echo "$XMM,$YMM,$LMM,BUILD_FAIL,-,-,-,-,-,-" >> "$RESULTS"
        continue
    fi

    PLAN_OUT=$(./build/supported_body_shift_plan_test 2>&1)
    PLAN_RC=$?

    LINE=$(echo "$PLAN_OUT" | grep 'MEASURED' | tail -1)

    DELTA=$(echo "$LINE" | sed -n 's/.*max_delta=\([^ ]*\).*/\1/p')
    DLIM=$(echo "$LINE" | sed -n 's/.*limits: delta=\([^ ]*\).*/\1/p')
    SPEED=$(echo "$LINE" | sed -n 's/.*max_speed=\([^ ]*\).*/\1/p')
    SLIM=$(echo "$LINE" | sed -n 's/.*speed=\([^ ]*\)$/\1/p')

    if [ "$PLAN_RC" -ne 0 ]; then
        echo "PLAN_FAIL  d=${DELTA:-?} v=${SPEED:-?}"
        echo "$XMM,$YMM,$LMM,FAIL,-,$DELTA,$DLIM,$SPEED,$SLIM,-" >> "$RESULTS"
        continue
    fi

    INERT_OUT=$(./build/supported_body_shift_once_test 2>&1)
    INERT_RC=$?

    if [ "$INERT_RC" -eq 0 ]; then
        echo "PASS       d=${DELTA:-?} v=${SPEED:-?}"
        echo "$XMM,$YMM,$LMM,PASS,PASS,$DELTA,$DLIM,$SPEED,$SLIM,-" >> "$RESULTS"
        PASS_COUNT=$((PASS_COUNT+1))
    else
        BOUND=$(echo "$INERT_OUT" | grep 'BODY_SHIFT_BOUND_FAIL' | tail -1)
        SAFE_BOUND=$(echo "$BOUND" | tr ',' ';')

        echo "INERT_FAIL d=${DELTA:-?} v=${SPEED:-?}"
        echo "$XMM,$YMM,$LMM,PASS,FAIL,$DELTA,$DLIM,$SPEED,$SLIM,\"$SAFE_BOUND\"" >> "$RESULTS"
    fi

done
done
done

restore

echo
echo "============================================================"
echo " DATASET SWEEP COMPLETE"
echo "============================================================"
echo "Total: $TOTAL"
echo "Full PASS: $PASS_COUNT"
echo "Results: $RESULTS"
echo

python3 - "$RESULTS" <<'PY'
import csv, sys

with open(sys.argv[1], newline="") as f:
    rows=list(csv.DictReader(f))

good=[r for r in rows if r["plan"]=="PASS" and r["inert"]=="PASS"]
plan_fail=[r for r in rows if r["plan"]=="FAIL"]
inert_fail=[r for r in rows if r["plan"]=="PASS" and r["inert"]=="FAIL"]

print(f"FULL PASS : {len(good)}")
print(f"PLAN FAIL : {len(plan_fail)}")
print(f"INERT FAIL: {len(inert_fail)}")

print("\nFULL-PASS CONFIGURATIONS:")
for r in good:
    print(
        f"  shift={r['x_mm']}/{r['y_mm']} mm"
        f"  lift={r['lift_mm']} mm"
        f"  delta={r['max_delta']}"
        f"  speed={r['max_speed']}"
    )
PY

echo
echo "Restoring original configuration + build..."

cmake --build build -j"$(nproc)" \
    --target supported_body_shift_plan_test supported_body_shift_once_test \
    >/dev/null 2>&1 || true

trap - EXIT INT TERM

echo "DONE"
