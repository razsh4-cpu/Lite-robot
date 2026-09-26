#!/usr/bin/env bash
set -u

SIM="./build-mujoco/one_leg_lift_joint_sim"
ROOT="artifacts/joint_angle_sweep"
CSV="$ROOT/results.csv"

rm -rf "$ROOT"
mkdir -p "$ROOT"

echo "thigh_deg,knee_deg,curl_scale,completed,actual_lift_mm,fr_unloaded,support_margin_mm,stance_loaded,roll_deg,pitch_deg,tracking_error_rad,max_joint_rate_rad_s,peak_torque_nm,abort_reason" > "$CSV"

THIGHS=(4 6 8 10 12)
KNEES=(-2 -4 -6 -8 -10 -12)
CURLS=(1.0 1.5 2.0 2.5 3.0 4.0)

TOTAL=$((${#THIGHS[@]} * ${#KNEES[@]} * ${#CURLS[@]}))
COUNT=0

for THIGH in "${THIGHS[@]}"; do
  for KNEE in "${KNEES[@]}"; do
    for CURL in "${CURLS[@]}"; do

      COUNT=$((COUNT+1))
      DIR="$ROOT/t${THIGH}_k${KNEE}_c${CURL}"

      echo "[$COUNT/$TOTAL] thigh=+$THIGH° knee=$KNEE° curl=$CURL"

      "$SIM" \
        --output-dir "$DIR" \
        --shift-thigh-deg "$THIGH" \
        --shift-knee-deg "$KNEE" \
        --fr-curl-scale "$CURL" \
        --joint-shift-scale 1.0 \
        --joint-lift-scale 1.0 \
        --shift-s 4.0 \
        --hold-s 1.0 \
        --lift-s 1.5 \
        --lower-s 1.5 \
        --forward-mm 0 \
        --kp 60 \
        --kd 0.7 \
        >/dev/null 2>&1 || true

      SUMMARY="$DIR/summary.json"

      [[ -f "$SUMMARY" ]] || continue

      python3 - "$SUMMARY" "$THIGH" "$KNEE" "$CURL" >> "$CSV" <<'PY'
import json, sys

path, thigh, knee, curl = sys.argv[1:]

with open(path) as f:
    d=json.load(f)

def g(k, scale=1):
    v=d.get(k)
    return "" if v is None else v*scale

reason=str(d.get("abort_reason","")).replace(",",";")

print(",".join(map(str,[
    thigh,
    knee,
    curl,
    d.get("completed",False),
    g("max_measured_fr_lift_m",1000),
    g("fr_unloaded_fraction_during_hold"),
    g("minimum_support_margin_during_lift_m",1000),
    g("all_stance_feet_loaded_fraction_during_lift"),
    g("max_abs_roll_during_lift_deg"),
    g("max_abs_pitch_during_lift_deg"),
    g("max_tracking_error_rad"),
    g("max_joint_rate_rad_s"),
    g("peak_pd_torque_nm"),
    reason
])))
PY

    done
  done
done

python3 - "$CSV" <<'PY'
import csv,sys

with open(sys.argv[1],newline="") as f:
    rows=list(csv.DictReader(f))

def n(r,k):
    try: return float(r[k])
    except: return -999

# Rank primarily by unloading, but penalize excessive attitude.
rows.sort(
    key=lambda r: (
        n(r,"fr_unloaded"),
        -max(n(r,"roll_deg"), n(r,"pitch_deg")),
        n(r,"support_margin_mm"),
        n(r,"actual_lift_mm")
    ),
    reverse=True
)

print("\n==============================")
print("      TOP ANGLE RESULTS")
print("==============================")

for r in rows[:30]:
    print(
        f'T={float(r["thigh_deg"]):+5.1f}° '
        f'K={float(r["knee_deg"]):+5.1f}° '
        f'C={float(r["curl_scale"]):3.1f} | '
        f'lift={n(r,"actual_lift_mm"):5.2f}mm | '
        f'unload={n(r,"fr_unloaded"):4.2f} | '
        f'margin={n(r,"support_margin_mm"):6.1f}mm | '
        f'roll={n(r,"roll_deg"):5.2f}° | '
        f'pitch={n(r,"pitch_deg"):5.2f}° | '
        f'err={n(r,"tracking_error_rad"):5.3f} | '
        f'tau={n(r,"peak_torque_nm"):5.1f}'
    )

print("\nCSV:",sys.argv[1])
PY
