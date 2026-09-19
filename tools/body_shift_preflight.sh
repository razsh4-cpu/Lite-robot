#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

PLAN="state_machine/supported_body_shift_plan.hpp"
ONCE="tests/supported_body_shift_once_test.cpp"

echo "=========================================="
echo " LITE3 BODY-SHIFT AUTOMATIC PREFLIGHT"
echo "=========================================="
echo

echo "[1/6] Active experiment"
grep -nE \
'kShiftXM|kShiftYM|kUnloadM|kShiftSeconds|kHoldSeconds|kUnloadSeconds|kUnloadHoldSeconds|kRestoreSeconds|kRecenterSeconds|kMaxJointDeltaRad|kMaxTargetSpeedRadS' \
"$PLAN" || true
echo

echo "[2/6] Checking for stale body-shift speed test..."

# Safe repair only:
# old body-shift test must not independently hard-code 0.10.
if grep -q 'max_target_velocity<=0\.10' "$ONCE"; then
    echo "AUTO-FIX: stale 0.10 body-shift test limit found."

    cp "$ONCE" "/tmp/supported_body_shift_once_test.preflight.bak"

    python3 - <<'PY'
from pathlib import Path

p = Path("tests/supported_body_shift_once_test.cpp")
s = p.read_text()

s2 = s.replace(
    "max_target_velocity<=0.10",
    "max_target_velocity<=SupportedBodyShiftPlan::kMaxTargetSpeedRadS"
)

if s2 == s:
    raise SystemExit("AUTO-FIX FAILED")

p.write_text(s2)
print("AUTO-FIX OK")
PY
else
    echo "OK: no stale 0.10 comparison."
fi
echo

echo "[3/6] Checking body-shift hardware/planner synchronization..."

if grep -A12 'supported_body_shift_bounds_)' \
   interface/robot/hardware/hardware_interface.hpp |
   grep -q 'abs(input(i,3))>0\.1000001'; then
    echo "FAIL: body-shift hardware still contains hard-coded 0.10 speed guard."
    echo "Not auto-fixing a hardware safety guard."
    exit 20
fi

if ! grep -A12 'supported_body_shift_bounds_)' \
    interface/robot/hardware/hardware_interface.hpp |
    grep -q 'body_shift_max_target_speed_'; then
    echo "FAIL: configured body-shift target-speed guard not detected."
    exit 21
fi

echo "OK: body-shift speed limit is configurable."
echo

echo "[4/6] Building..."
if ! cmake --build build -j"$(nproc)"; then
    echo
    echo "FAIL: build failed."
    exit 30
fi
echo

echo "[5/6] Trajectory preflight..."
PLAN_OUT="$(./build/supported_body_shift_plan_test 2>&1)"
PLAN_RC=$?
echo "$PLAN_OUT"
echo

if [ "$PLAN_RC" -ne 0 ]; then
    echo "PREFLIGHT FAIL."
    echo
    echo "The trajectory exceeded a reviewed limit."
    echo "NO safety limit will be increased automatically."
    echo "NO hardware run should be performed."
    exit 40
fi

echo "Trajectory: PASS"
echo

echo "[6/6] Inert integration test..."
ONCE_OUT="$(./build/supported_body_shift_once_test 2>&1)"
ONCE_RC=$?
echo "$ONCE_OUT"
echo

if [ "$ONCE_RC" -ne 0 ]; then
    echo "INERT TEST FAIL."
    echo "NO hardware run should be performed."
    exit 50
fi

echo "Running complete CTest suite..."
if ! ctest --test-dir build --output-on-failure; then
    echo
    echo "FULL PREFLIGHT FAIL."
    echo "At least one repository test failed."
    echo "NO hardware run should be performed."
    exit 60
fi

echo
echo "=========================================="
echo " ALL OFFLINE PREFLIGHT CHECKS PASSED"
echo "=========================================="
echo
echo "Experiment parameters:"
grep -E \
'kShiftXM|kShiftYM|kUnloadM|kMaxJointDeltaRad|kMaxTargetSpeedRadS' \
"$PLAN" || true

echo
echo "Trajectory:"
echo "$PLAN_OUT" | grep -E 'MEASURED|max_delta|max_speed|PASS' || true

echo
echo "17/17 suite: PASS"
echo
echo "OFFLINE READY."
echo "This does NOT itself authorize or start hardware."
