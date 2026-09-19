#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

ROOT = Path.home() / "ros-robot-cc" / "Lite-robot"
RUNNER = ROOT / "tools" / "run_one_leg_lift_sim.sh"
MODEL = ROOT / "third_party/deep_robotics_model/Lite3/Lite3_mjcf/mjcf/Lite3.xml"
OUT = ROOT / "artifacts" / "single_leg_sensitivity"

# Same motion for every test. Only ONE uncertainty dimension changes.
MOTION = [
    "--shift-x-mm", "60",
    "--shift-y-mm", "60",
    "--shift-s", "2.0",
    "--hold-s", "0.0",
    "--lift-mm", "15",
    "--lift-s", "1.5",
    "--lower-s", "1.5",
    "--kp", "180",
    "--kd", "3.5",
]

BASE = {
    "payload": "0",
    "comx": "0",
    "comy": "0",
    "friction": "1",
    "compliance": "1",
    "offset": "0",
    "noise": "0",
    "delay": "0",
}

# Baseline + low/high test for each uncertainty family.
TESTS = [
    ("baseline", {}),

    ("payload_0p5kg", {"payload": "0.5"}),
    ("payload_1kg", {"payload": "1.0"}),

    ("com_x_plus5mm", {"comx": "5"}),
    ("com_x_minus5mm", {"comx": "-5"}),
    ("com_y_plus5mm", {"comy": "5"}),
    ("com_y_minus5mm", {"comy": "-5"}),
    ("com_xy_10mm", {"comx": "10", "comy": "10"}),

    ("friction_0p9", {"friction": "0.9"}),
    ("friction_0p8", {"friction": "0.8"}),
    ("friction_1p2", {"friction": "1.2"}),

    ("compliance_0p9", {"compliance": "0.9"}),
    ("compliance_1p1", {"compliance": "1.1"}),
    ("compliance_1p2", {"compliance": "1.2"}),

    ("joint_offset_0p005", {"offset": "0.005"}),
    ("joint_offset_0p010", {"offset": "0.010"}),

    ("noise_0p002", {"noise": "0.002"}),
    ("noise_0p004", {"noise": "0.004"}),

    ("delay_5ms", {"delay": "5"}),
    ("delay_10ms", {"delay": "10"}),
    ("delay_15ms", {"delay": "15"}),
]

def value(d, key):
    try:
        return float(d.get(key))
    except (TypeError, ValueError):
        return float("nan")

def run_test(index, name, changes):
    p = dict(BASE)
    p.update(changes)

    directory = OUT / f"{index:02d}_{name}"
    directory.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(RUNNER),
        "--model", str(MODEL),
        "--output-dir", str(directory),
        *MOTION,

        "--payload-kg", p["payload"],
        "--com-offset-x-mm", p["comx"],
        "--com-offset-y-mm", p["comy"],
        "--friction-scale", p["friction"],
        "--compliance-scale", p["compliance"],
        "--joint-offset-rad", p["offset"],
        "--sensor-noise-rad", p["noise"],
        "--delay-ms", p["delay"],
        "--seed", "20260918",
    ]

    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    summary_file = directory / "summary.json"

    if not summary_file.exists():
        return {
            "name": name,
            "completed": False,
            "reason": "NO_SUMMARY",
        }

    d = json.loads(summary_file.read_text())

    return {
        "name": name,
        "completed": bool(d.get("completed")),
        "reason": d.get("abort_reason", ""),
        "clearance_mm": value(d, "max_measured_fr_lift_m") * 1000,
        "margin_mm": value(d, "minimum_support_margin_during_lift_m") * 1000,
        "roll_deg": value(d, "max_abs_roll_during_lift_deg"),
        "pitch_deg": value(d, "max_abs_pitch_during_lift_deg"),
        "tracking": value(d, "max_tracking_error_rad"),
        "rate": value(d, "max_joint_rate_rad_s"),
        "touchdown": value(d, "touchdown_velocity_m_s"),
        "final_error": value(d, "final_joint_error_rad"),
    }

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    results = []

    print("===== SINGLE-PARAMETER SENSITIVITY =====")
    print(f"Tests: {len(TESTS)}")
    print()

    for i, (name, changes) in enumerate(TESTS):
        r = run_test(i, name, changes)
        results.append(r)

        status = "PASS" if r["completed"] else "FAIL"

        print(
            f"[{i+1:02d}/{len(TESTS)}] "
            f"{name:<23} {status:<4} "
            f"clear={r.get('clearance_mm', float('nan')):6.2f}mm "
            f"margin={r.get('margin_mm', float('nan')):7.2f}mm "
            f"roll={r.get('roll_deg', float('nan')):5.2f} "
            f"pitch={r.get('pitch_deg', float('nan')):5.2f} "
            f"reason={r.get('reason','')}"
        )

    print()
    print("===== DIAGNOSIS =====")

    baseline = results[0]

    if not baseline["completed"]:
        print("BASELINE FAILED.")
        print("Do not interpret perturbation sensitivity yet.")
        print("The patched runner itself must be investigated first.")
        return

    print("Baseline: PASS")
    print()

    failures = [r for r in results[1:] if not r["completed"]]

    if not failures:
        print("All isolated perturbations completed.")
        print("The previous Monte Carlo failures are likely caused by")
        print("COMBINATIONS of perturbations rather than one variable alone.")
    else:
        print("Isolated perturbations that caused runner failure:")
        for r in failures:
            print(f"  - {r['name']}: {r['reason']}")

    (OUT / "sensitivity_results.json").write_text(
        json.dumps(results, indent=2)
    )

    print()
    print("Saved:")
    print(OUT / "sensitivity_results.json")

if __name__ == "__main__":
    main()
