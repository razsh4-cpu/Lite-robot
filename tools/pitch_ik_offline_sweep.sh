#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

FILE="state_machine/supported_body_shift_plan.hpp"
BACKUP="/tmp/supported_body_shift_plan_pitch_sweep_$$.hpp"

cp "$FILE" "$BACKUP" || exit 1

restore() {
    echo
    echo "=============================================="
    echo "RESTORING ORIGINAL CONFIGURATION"
    echo "=============================================="
    cp "$BACKUP" "$FILE"
    rm -f "$BACKUP"

    cmake --build build \
        --target supported_body_shift_plan_test supported_body_shift_once_test \
        -j"$(nproc)" >/dev/null 2>&1 || true

    echo "Original configuration restored."
}

trap restore EXIT INT TERM

echo "=============================================================="
echo " LITE3 TRUE BODY-PITCH IK OFFLINE SWEEP"
echo "=============================================================="
echo
echo "Base experiment:"
echo "  X shift      = 40 mm"
echo "  Y shift      = 40 mm"
echo "  FR lift      = 15 mm"
echo "  body pitch   = swept"
echo
echo "Safety limits:"
echo "  joint delta  = 0.30 rad"
echo "  target speed = 0.12 rad/s"
echo
echo "NO HARDWARE"
echo "NO SAFETY LIMIT CHANGES"
echo "=============================================================="

set_value() {
    local NAME="$1"
    local VALUE="$2"

    sed -i -E \
      "s/(static constexpr double ${NAME} *= *)[-+0-9.eE]+;/\1${VALUE};/" \
      "$FILE"
}

set_pitch_code() {
python3 - "$1" <<'PY'
from pathlib import Path
import sys
import re

pitch_deg = float(sys.argv[1])
pitch_rad = pitch_deg * 3.141592653589793 / 180.0

p = Path("state_machine/supported_body_shift_plan.hpp")
s = p.read_text()

# Remove old differential-Z implementation if present.
s = re.sub(
    r'\n\s*static constexpr double kFrontRiseM\s*=\s*[-+0-9.eE]+;\n',
    '\n',
    s
)

# Find the current shifted_target block and replace it with
# an actual body-pose pitch rotation before IK.
pattern = re.compile(
    r"""const Eigen::Vector3d shifted_target\s*=
\s*nominal\s*\+
\s*Eigen::Vector3d\(
\s*kShiftXM,\s*
-kShiftYM,\s*
0\.0\);""",
    re.MULTILINE
)

replacement = f"""const Eigen::Vector3d shifted_nominal =
                nominal +
                Eigen::Vector3d(
                    kShiftXM,
                    -kShiftYM,
                    0.0);

            // True body-pose pitch:
            // rotate the desired body-frame foot target around
            // the body Y axis before solving leg IK.
            constexpr double kPitchRad = {pitch_rad:.12f};

            const double c = std::cos(kPitchRad);
            const double sn = std::sin(kPitchRad);

            Eigen::Matrix3d R_pitch;
            R_pitch <<
                c,  0.0, sn,
                0.0, 1.0, 0.0,
               -sn, 0.0, c;

            const Eigen::Vector3d shifted_target =
                R_pitch.transpose() * shifted_nominal;"""

new_s, n = pattern.subn(replacement, s)

if n != 1:
    print(f"ERROR: expected exactly one shifted_target block, found {n}")
    sys.exit(2)

p.write_text(new_s)
PY
}

# Configure fixed experiment.
set_value kShiftXM 0.040
set_value kShiftYM 0.040
set_value kUnloadM 0.015

# Keep the reviewed safety limits untouched.
if ! grep -Eq 'kMaxJointDeltaRad *= *0\.30;' "$FILE"; then
    echo "ERROR: unexpected joint delta limit"
    exit 1
fi

if ! grep -Eq 'kMaxTargetSpeedRadS *= *0\.12;' "$FILE"; then
    echo "ERROR: unexpected speed limit"
    exit 1
fi

echo
echo "Building baseline targets..."
cmake --build build \
    --target supported_body_shift_plan_test supported_body_shift_once_test \
    -j"$(nproc)" >/dev/null || {
        echo "BUILD FAIL"
        exit 1
    }

# Both signs are tested because this determines which direction
# corresponds to nose-up in the robot's actual coordinate convention.
PITCHES=(
    "-2.0"
    "-1.5"
    "-1.0"
    "-0.5"
    "0.0"
    "0.5"
    "1.0"
    "1.5"
    "2.0"
)

RESULTS="/tmp/lite3_pitch_ik_sweep_$$.csv"

echo "pitch_deg,plan,inert" > "$RESULTS"

for PITCH in "${PITCHES[@]}"; do

    echo
    echo "--------------------------------------------------------------"
    echo "TEST BODY PITCH = ${PITCH} deg"
    echo "--------------------------------------------------------------"

    cp "$BACKUP" "$FILE"

    set_value kShiftXM 0.040
    set_value kShiftYM 0.040
    set_value kUnloadM 0.015

    if ! set_pitch_code "$PITCH"; then
        echo "PATCH FAIL"
        echo "$PITCH,PATCH_FAIL,PATCH_FAIL" >> "$RESULTS"
        continue
    fi

    cmake --build build \
        --target supported_body_shift_plan_test supported_body_shift_once_test \
        -j"$(nproc)" >/dev/null 2>&1

    PLAN_OUTPUT="$(./build/supported_body_shift_plan_test 2>&1)"
    PLAN_RC=$?

    echo "$PLAN_OUTPUT"

    if [ "$PLAN_RC" -eq 0 ]; then
        PLAN="PASS"
    else
        PLAN="FAIL"
    fi

    # Only run inert test if plan passed.
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

    echo "$PITCH,$PLAN,$INERT" >> "$RESULTS"

    if [ "$PLAN" = "PASS" ] && [ "$INERT" = "PASS" ]; then
        echo ">>> CANDIDATE: ${PITCH} deg = PLAN PASS / INERT PASS <<<"
    fi
done

echo
echo "=============================================================="
echo "PITCH SWEEP SUMMARY"
echo "=============================================================="
cat "$RESULTS"

echo
echo "RESULT FILE:"
echo "$RESULTS"

echo
echo "IMPORTANT:"
echo "This script restored the original source automatically."
echo "No hardware command was sent."
echo "=============================================================="
