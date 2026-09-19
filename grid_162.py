#!/usr/bin/env python3

import csv
import itertools
import json
import math
import subprocess
from pathlib import Path

ROOT = Path.home() / "ros-robot-cc" / "Lite-robot"
RUNNER = ROOT / "tools" / "run_one_leg_lift_sim.sh"
MODEL = ROOT / "third_party/deep_robotics_model/Lite3/Lite3_mjcf/mjcf/Lite3.xml"
OUT = ROOT / "artifacts" / "grid_162"

SHIFTS = [60, 65, 70]
LIFTS = [14, 15, 16]

GAINS = [
    (140, 2.5),
    (180, 3.5),
]

TIMING_SCALES = [0.75, 1.0, 1.25]
FRICTIONS = [0.5, 1.0, 1.5]

# Baseline timings from the validated primitive.
BASE_SHIFT_S = 2.0
BASE_LIFT_S = 1.5
BASE_LOWER_S = 1.5

MIN_CLEARANCE_M = 0.005
MIN_SUPPORT_MARGIN_M = 0.0
MAX_ROLL_DEG = 12.0
MAX_PITCH_DEG = 12.0
TORQUE_LIMIT_NM = 30.0


def number(d, key):
    try:
        return float(d.get(key))
    except (TypeError, ValueError):
        return float("nan")


def run_one(index, shift, lift, kp, kd, timing, friction):
    run_dir = OUT / "runs" / f"run_{index:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(RUNNER),
        "--model", str(MODEL),
        "--output-dir", str(run_dir),

        # Diagonal shift: rearward + left for FR.
        "--shift-x-mm", str(shift),
        "--shift-y-mm", str(shift),

        "--shift-s", str(BASE_SHIFT_S * timing),
        "--hold-s", "0",

        "--lift-mm", str(lift),
        "--lift-s", str(BASE_LIFT_S * timing),
        "--lower-s", str(BASE_LOWER_S * timing),

        "--kp", str(kp),
        "--kd", str(kd),

        # This grid changes only friction.
        # Other robustness perturbations remain disabled.
        "--payload-kg", "0",
        "--com-offset-x-mm", "0",
        "--com-offset-y-mm", "0",
        "--friction-scale", str(friction),
        "--compliance-scale", "1",
        "--joint-offset-rad", "0",
        "--sensor-noise-rad", "0",
        "--delay-ms", "0",
        "--seed", "20260918",
    ]

    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    summary_file = run_dir / "summary.json"

    base = {
        "run": index,
        "shift_mm": shift,
        "lift_mm": lift,
        "kp": kp,
        "kd": kd,
        "timing_scale": timing,
        "friction_scale": friction,
        "returncode": proc.returncode,
    }

    if not summary_file.exists():
        return {
            **base,
            "pass": False,
            "reason": "NO_SUMMARY",
        }

    try:
        d = json.loads(summary_file.read_text())
    except Exception:
        return {
            **base,
            "pass": False,
            "reason": "INVALID_SUMMARY",
        }

    clearance = number(d, "max_measured_fr_lift_m")
    margin = number(d, "minimum_support_margin_during_lift_m")
    roll = number(d, "max_abs_roll_during_lift_deg")
    pitch = number(d, "max_abs_pitch_during_lift_deg")
    torque = number(d, "peak_pd_torque_nm")

    reasons = []

    if not d.get("completed", False):
        reasons.append(d.get("abort_reason") or "not_completed")

    if not math.isfinite(clearance) or clearance < MIN_CLEARANCE_M:
        reasons.append("clearance")

    if not math.isfinite(margin) or margin <= MIN_SUPPORT_MARGIN_M:
        reasons.append("support_margin")

    if not math.isfinite(roll) or roll > MAX_ROLL_DEG:
        reasons.append("roll")

    if not math.isfinite(pitch) or pitch > MAX_PITCH_DEG:
        reasons.append("pitch")

    # Do not accept a run that reaches the controller clamp.
    if not math.isfinite(torque) or torque >= TORQUE_LIMIT_NM - 1e-6:
        reasons.append("torque_saturation")

    return {
        **base,
        "pass": len(reasons) == 0,
        "reason": "|".join(reasons),
        "clearance_mm": clearance * 1000,
        "support_margin_mm": margin * 1000,
        "roll_deg": roll,
        "pitch_deg": pitch,
        "peak_torque_nm": torque,
        "tracking_error_rad": number(d, "max_tracking_error_rad"),
        "joint_rate_rad_s": number(d, "max_joint_rate_rad_s"),
        "touchdown_velocity_m_s": number(d, "touchdown_velocity_m_s"),
        "final_joint_error_rad": number(d, "final_joint_error_rad"),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    combinations = list(itertools.product(
        SHIFTS,
        LIFTS,
        GAINS,
        TIMING_SCALES,
        FRICTIONS,
    ))

    print("===== LITE3 FR GRID =====")
    print("Total runs:", len(combinations))
    print("Expected: 162")
    print()

    rows = []

    for i, (shift, lift, gains, timing, friction) in enumerate(combinations, 1):
        kp, kd = gains

        r = run_one(
            i,
            shift,
            lift,
            kp,
            kd,
            timing,
            friction,
        )

        rows.append(r)

        status = "PASS" if r["pass"] else "FAIL"

        print(
            f"[{i:03d}/162] {status:4s} "
            f"shift={shift:2d} "
            f"lift={lift:2d} "
            f"PD={kp}/{kd} "
            f"time={timing:.2f}x "
            f"mu={friction:.1f} "
            f"clear={r.get('clearance_mm', float('nan')):6.2f}mm "
            f"margin={r.get('support_margin_mm', float('nan')):7.2f}mm "
            f"tau={r.get('peak_torque_nm', float('nan')):5.2f} "
            f"{r.get('reason','')}"
        )

    fields = []
    for row in rows:
        for k in row:
            if k not in fields:
                fields.append(k)

    csv_path = OUT / "results.csv"

    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    passed = [r for r in rows if r["pass"]]

    print()
    print("===== GRID RESULT =====")
    print(f"PASS: {len(passed)}/162")
    print(f"FAIL: {162-len(passed)}/162")

    # Group by shift/lift so we look for regions, not a magic point.
    print()
    print("===== SHIFT/LIFT REGIONS =====")

    regions = []

    for shift in SHIFTS:
        for lift in LIFTS:
            group = [
                r for r in rows
                if r["shift_mm"] == shift
                and r["lift_mm"] == lift
            ]

            ok = [r for r in group if r["pass"]]
            rate = len(ok) / len(group)

            if ok:
                min_clear = min(r["clearance_mm"] for r in ok)
                min_margin = min(r["support_margin_mm"] for r in ok)
                max_tau = max(r["peak_torque_nm"] for r in ok)
            else:
                min_clear = float("nan")
                min_margin = float("nan")
                max_tau = float("nan")

            regions.append({
                "shift": shift,
                "lift": lift,
                "passes": len(ok),
                "runs": len(group),
                "rate": rate,
                "min_clear": min_clear,
                "min_margin": min_margin,
                "max_tau": max_tau,
            })

    regions.sort(
        key=lambda x: (
            x["rate"],
            x["min_margin"] if math.isfinite(x["min_margin"]) else -999,
            x["min_clear"] if math.isfinite(x["min_clear"]) else -999,
        ),
        reverse=True,
    )

    for x in regions:
        print(
            f"shift={x['shift']:2d}mm "
            f"lift={x['lift']:2d}mm : "
            f"{x['passes']:2d}/{x['runs']:2d} "
            f"({x['rate']*100:5.1f}%) "
            f"min_clear={x['min_clear']:6.2f}mm "
            f"min_margin={x['min_margin']:7.2f}mm "
            f"max_tau={x['max_tau']:5.2f}Nm"
        )

    print()
    print("===== MODEL-ONLY CENTER =====")

    center = [
        r for r in rows
        if r["shift_mm"] == 65
        and r["lift_mm"] == 15
        and r["kp"] == 180
        and r["kd"] == 3.5
    ]

    center_pass = sum(r["pass"] for r in center)

    print(
        f"65/65 shift + 15mm lift + PD 180/3.5: "
        f"{center_pass}/{len(center)} PASS"
    )

    if center:
        good = [r for r in center if r["pass"]]
        if good:
            print(
                "PASS envelope: "
                f"clearance {min(r['clearance_mm'] for r in good):.2f}"
                f"-{max(r['clearance_mm'] for r in good):.2f}mm, "
                f"minimum support margin "
                f"{min(r['support_margin_mm'] for r in good):.2f}mm, "
                f"peak torque <= "
                f"{max(r['peak_torque_nm'] for r in good):.2f}Nm"
            )

    print()
    print("Saved:", csv_path)
    print()
    print("SIMULATION ONLY.")
    print("No hardware values are approved by this test.")


if __name__ == "__main__":
    main()
