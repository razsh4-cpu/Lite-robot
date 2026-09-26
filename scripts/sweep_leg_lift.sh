#!/usr/bin/env bash
set -u

SIM="./build-mujoco/one_leg_lift_sim"
ROOT="artifacts/leg_lift_sweep"
CSV="$ROOT/results.csv"

mkdir -p "$ROOT"

echo "shift_x_mm,shift_y_mm,lift_mm,completed,abort_reason,actual_lift_mm,fr_unloaded,stance_loaded,support_margin_mm,roll_deg,pitch_deg,tracking_error_rad,max_joint_rate_rad_s,peak_torque_nm" > "$CSV"

TOTAL=$((7 * 7 * 3))
COUNT=0

for X in 20 30 40 50 60 70 80; do
  for Y in 20 30 40 50 60 70 80; do
    for LIFT in 5 10 15; do

      COUNT=$((COUNT + 1))
      DIR="$ROOT/x${X}_y${Y}_l${LIFT}"

      echo "[$COUNT/$TOTAL] X=${X}mm Y=${Y}mm lift=${LIFT}mm"

      rm -rf "$DIR"

      "$SIM" \
        --output-dir "$DIR" \
        --shift-x-mm "$X" \
        --shift-y-mm "$Y" \
        --shift-s 4.0 \
        --hold-s 1.0 \
        --lift-mm "$LIFT" \
        --lift-s 1.5 \
        --lower-s 1.5 \
        --forward-mm 0 \
        --kp 60 \
        --kd 0.7 \
        >/dev/null 2>&1 || true

      SUMMARY="$DIR/summary.json"

      if [[ ! -f "$SUMMARY" ]]; then
        echo "$X,$Y,$LIFT,false,no_summary,,,,,,,,," >> "$CSV"
        continue
      fi

      python3 - "$SUMMARY" "$X" "$Y" "$LIFT" >> "$CSV" <<'PY'
import json
import sys

path, x, y, lift = sys.argv[1:]

with open(path) as f:
    d = json.load(f)

def n(key, scale=1.0):
    v = d.get(key)
    if v is None:
        return ""
    return v * scale

reason = str(d.get("abort_reason", "")).replace(",", ";")

print(",".join(map(str, [
    x,
    y,
    lift,
    d.get("completed", False),
    reason,
    n("max_measured_fr_lift_m", 1000),
    n("fr_unloaded_fraction_during_hold"),
    n("all_stance_feet_loaded_fraction_during_lift"),
    n("minimum_support_margin_during_lift_m", 1000),
    n("max_abs_roll_during_lift_deg"),
    n("max_abs_pitch_during_lift_deg"),
    n("max_tracking_error_rad"),
    n("max_joint_rate_rad_s"),
    n("peak_pd_torque_nm"),
])))
PY

    done
  done
done

echo
echo "DONE"
echo "Results: $CSV"

python3 - "$CSV" <<'PY'
import csv
import sys

path = sys.argv[1]

with open(path, newline="") as f:
    rows = list(csv.DictReader(f))

def val(r, key, default=-1e99):
    try:
        return float(r[key])
    except:
        return default

successful = [
    r for r in rows
    if r["completed"].lower() == "true"
]

print()
print("=== SWEEP SUMMARY ===")
print("Total runs:", len(rows))
print("Completed:", len(successful))
print("Failed:", len(rows) - len(successful))

print()
print("=== TOP 20 BY FR CLEARANCE ===")

ranked = sorted(
    rows,
    key=lambda r: val(r, "actual_lift_mm"),
    reverse=True
)

for r in ranked[:20]:
    print(
        f'X={r["shift_x_mm"]:>2} '
        f'Y={r["shift_y_mm"]:>2} '
        f'L={r["lift_mm"]:>2} | '
        f'actual={val(r,"actual_lift_mm"):6.2f} mm | '
        f'FR_unload={val(r,"fr_unloaded"):5.2f} | '
        f'margin={val(r,"support_margin_mm"):6.1f} mm | '
        f'roll={val(r,"roll_deg"):5.2f} | '
        f'pitch={val(r,"pitch_deg"):5.2f} | '
        f'track={val(r,"tracking_error_rad"):6.3f} | '
        f'dq={val(r,"max_joint_rate_rad_s"):6.3f} | '
        f'{"PASS" if r["completed"].lower()=="true" else "FAIL"}'
    )
PY
