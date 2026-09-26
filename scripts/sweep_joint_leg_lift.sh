#!/usr/bin/env bash
set -u

SIM="./build-mujoco/one_leg_lift_joint_sim"
ROOT="artifacts/joint_leg_lift_sweep"
CSV="$ROOT/results.csv"

rm -rf "$ROOT"
mkdir -p "$ROOT"

echo "shift_scale,lift_scale,completed,abort_reason,actual_lift_mm,fr_unloaded,support_margin_mm,stance_loaded,roll_deg,pitch_deg,tracking_error_rad,max_joint_rate_rad_s,peak_torque_nm" > "$CSV"

SHIFTS=(0.50 0.625 0.75 0.875 1.00 1.125 1.25 1.375 1.50)
LIFTS=(0.50 0.75 1.00 1.25 1.50 1.75 2.00 2.50)

TOTAL=$((${#SHIFTS[@]} * ${#LIFTS[@]}))
COUNT=0

for SHIFT in "${SHIFTS[@]}"; do
  for LIFT in "${LIFTS[@]}"; do
    COUNT=$((COUNT+1))

    NAME="s${SHIFT}_l${LIFT}"
    DIR="$ROOT/$NAME"

    echo "[$COUNT/$TOTAL] shift=$SHIFT lift=$LIFT"

    "$SIM" \
      --output-dir "$DIR" \
      --joint-shift-scale "$SHIFT" \
      --joint-lift-scale "$LIFT" \
      --shift-s 4.0 \
      --hold-s 1.0 \
      --lift-s 1.5 \
      --lower-s 1.5 \
      --forward-mm 0 \
      --kp 60 \
      --kd 0.7 \
      >/dev/null 2>&1 || true

    SUMMARY="$DIR/summary.json"

    if [[ ! -f "$SUMMARY" ]]; then
      echo "$SHIFT,$LIFT,false,no_summary,,,,,,,,," >> "$CSV"
      continue
    fi

    python3 - "$SUMMARY" "$SHIFT" "$LIFT" >> "$CSV" <<'PY'
import json, sys

path, shift, lift = sys.argv[1:]

with open(path) as f:
    d = json.load(f)

def get(key, scale=1.0):
    v = d.get(key)
    return "" if v is None else v * scale

reason = str(d.get("abort_reason", "")).replace(",", ";")

print(",".join(map(str, [
    shift,
    lift,
    d.get("completed", False),
    reason,
    get("max_measured_fr_lift_m", 1000),
    get("fr_unloaded_fraction_during_hold"),
    get("minimum_support_margin_during_lift_m", 1000),
    get("all_stance_feet_loaded_fraction_during_lift"),
    get("max_abs_roll_during_lift_deg"),
    get("max_abs_pitch_during_lift_deg"),
    get("max_tracking_error_rad"),
    get("max_joint_rate_rad_s"),
    get("peak_pd_torque_nm"),
])))
PY

  done
done

echo
echo "=============================="
echo "       SWEEP COMPLETE"
echo "=============================="

python3 - "$CSV" <<'PY'
import csv, sys

with open(sys.argv[1], newline="") as f:
    rows = list(csv.DictReader(f))

def f(r, k, default=-999999):
    try:
        return float(r[k])
    except:
        return default

passes = [r for r in rows if r["completed"].lower() == "true"]

print(f"Runs: {len(rows)}")
print(f"PASS: {len(passes)}")
print(f"FAIL: {len(rows)-len(passes)}")

print("\n=== BEST RESULTS ===")

# Prefer actual unloading, then stability margin,
# then smaller joint-space changes.
ranked = sorted(
    rows,
    key=lambda r: (
        f(r,"fr_unloaded"),
        f(r,"support_margin_mm"),
        -f(r,"shift_scale"),
        -f(r,"lift_scale")
    ),
    reverse=True
)

for r in ranked[:20]:
    result = "PASS" if r["completed"].lower()=="true" else "FAIL"

    print(
        f'S={r["shift_scale"]:>5} '
        f'L={r["lift_scale"]:>4} | '
        f'FR={f(r,"actual_lift_mm"):6.2f}mm | '
        f'unload={f(r,"fr_unloaded"):4.2f} | '
        f'margin={f(r,"support_margin_mm"):6.1f}mm | '
        f'roll={f(r,"roll_deg"):5.2f}° | '
        f'pitch={f(r,"pitch_deg"):5.2f}° | '
        f'err={f(r,"tracking_error_rad"):5.3f} | '
        f'dq={f(r,"max_joint_rate_rad_s"):5.2f} | '
        f'tau={f(r,"peak_torque_nm"):5.1f} | '
        f'{result}'
    )
PY

echo
echo "CSV: $CSV"
