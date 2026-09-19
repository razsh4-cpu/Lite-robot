#!/usr/bin/env bash
set -u

FILE="state_machine/supported_body_shift_plan.hpp"
BACKUP="/tmp/supported_body_shift_plan_true_pitch_$$.hpp"

cp "$FILE" "$BACKUP" || exit 1

restore() {
    echo
    echo "=============================================="
    echo "RESTORING ORIGINAL CONFIGURATION"
    echo "=============================================="
    cp "$BACKUP" "$FILE"
    rm -f "$BACKUP"
}
trap restore EXIT INT TERM

set_value() {
    local NAME="$1"
    local VALUE="$2"

    sed -i -E \
      "s/(static constexpr double ${NAME} *= *)[-+0-9.eE]+;/\1${VALUE};/" \
      "$FILE"
}

set_pitch() {
    local DEG="$1"

    python3 - "$DEG" <<'PY'
from pathlib import Path
import sys

deg = float(sys.argv[1])
rad = deg * 3.141592653589793 / 180.0

p = Path("state_machine/supported_body_shift_plan.hpp")
s = p.read_text()

old = """            const double pitch_z =
                front_leg ? -0.5 * kFrontRiseM
                          :  0.5 * kFrontRiseM;

            const Eigen::Vector3d shifted_target =
                nominal +
                Eigen::Vector3d(
                    kShiftXM,
                    -kShiftYM,
                    pitch_z);
"""

new = f"""            const Eigen::Vector3d shifted_nominal =
                nominal +
                Eigen::Vector3d(
                    kShiftXM,
                    -kShiftYM,
                    0.0);

            // True body-pose pitch.
            constexpr double kPitchRad = {rad:.12f};

            const double c = std::cos(kPitchRad);
            const double sn = std::sin(kPitchRad);

            Eigen::Matrix3d R_pitch;
            R_pitch <<
                c,  0.0, sn,
                0.0, 1.0, 0.0,
               -sn, 0.0, c;

            const Eigen::Vector3d shifted_target =
                R_pitch.transpose() * shifted_nominal;
"""

if old not in s:
    print("ERROR: expected current differential-Z block was not found")
    sys.exit(2)

s = s.replace(old, new, 1)
p.write_text(s)
print(f"Pitch configured: {deg} deg")
PY
}

echo "=============================================================="
echo " LITE3 TRUE BODY-PITCH IK SWEEP"
echo "=============================================================="
echo
echo "X shift = 40 mm"
echo "Y shift = 40 mm"
echo "FR lift = 15 mm"
echo "Pitch sweep = -2 to +2 deg"
echo
echo "NO HARDWARE"
echo "NO SAFETY LIMIT CHANGES"
echo "=============================================================="

# Fixed experiment.
set_value kShiftXM 0.040
set_value kShiftYM 0.040
set_value kUnloadM 0.015

# The old differential-Z parameter is no longer used by the pitch implementation.
set_value kFrontRiseM 0.010

# Verify safety limits.
if ! grep -Eq 'kMaxJointDeltaRad *= *0\.30;' "$FILE"; then
    echo "ERROR: joint delta limit changed"
    exit 1
fi

if ! grep -Eq 'kMaxTargetSpeedRadS *= *0\.12;' "$FILE"; then
    echo "ERROR: speed limit changed"
    exit 1
fi

RESULTS="/tmp/lite3_true_pitch_results_$$.csv"
echo "pitch_deg,plan,inert" > "$RESULTS"

for DEG in -2.0 -1.5 -1.0 -0.5 0.0 0.5 1.0 1.5 2.0
do
    echo
    echo "=============================================================="
    echo " PITCH = ${DEG} deg"
    echo "=============================================================="

    cp "$BACKUP" "$FILE"

    set_value kShiftXM 0.040
    set_value kShiftYM 0.040
    set_value kUnloadM 0.015
    set_value kFrontRiseM 0.010

    if ! set_pitch "$DEG"; then
        echo "$DEG,PATCH_FAIL,PATCH_FAIL" >> "$RESULTS"
        continue
    fi

    cmake --build build \
        --target supported_body_shift_plan_test supported_body_shift_once_test \
        -j"$(nproc)" || {
            echo "$DEG,BUILD_FAIL,BUILD_FAIL" >> "$RESULTS"
            continue
        }

    PLAN_OUTPUT="$(./build/supported_body_shift_plan_test 2>&1)"
    PLAN_RC=$?

    echo "$PLAN_OUTPUT"

    if [ "$PLAN_RC" -eq 0 ]; then
        PLAN="PASS"
    else
        PLAN="FAIL"
    fi

    if [ "$PLAN" = "PASS" ]; then
        INERT_OUTPUT="$(./build/supported_body_shift_once_test 2>&1)"
        INERT_RC=$?

        echo "$INERT_OUTPUT"

        if [ "$INERT_RC" -eq 0 ]; then
            INERT="PASS"
        else
            INERT="FAIL"
        fi
    else
        INERT="SKIP"
    fi

    echo "$DEG,$PLAN,$INERT" >> "$RESULTS"

    if [ "$PLAN" = "PASS" ] && [ "$INERT" = "PASS" ]; then
        echo
        echo ">>> CANDIDATE: ${DEG} deg = PASS / PASS <<<"
    fi
done

echo
echo "=============================================================="
echo " FINAL SUMMARY"
echo "=============================================================="
cat "$RESULTS"

echo
echo "RESULT FILE:"
echo "$RESULTS"
echo
echo "NO HARDWARE COMMAND WAS SENT."
echo "=============================================================="
