#!/usr/bin/env python3

import argparse
import csv
import json
import math
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "tools" / "run_one_leg_lift_sim.sh"
MODEL = ROOT / "third_party/deep_robotics_model/Lite3/Lite3_mjcf/mjcf/Lite3.xml"
OUTROOT = ROOT / "artifacts" / "single_leg_sweep"

# ---------------------------------------------------------------------
# Acceptance limits - simulation research limits, NOT hardware settings.
# Existing runner already enforces its own stability/contact limits.
# ---------------------------------------------------------------------
MIN_CLEARANCE_M = 0.005
MIN_SUPPORT_MARGIN_M = 0.0
MAX_ROLL_DEG = 12.0
MAX_PITCH_DEG = 12.0
MAX_TORQUE_NM = 30.0

# Additional sweep acceptance limits.
MAX_TOUCHDOWN_SPEED_M_S = 0.20
MAX_FINAL_JOINT_ERROR_RAD = 0.10
MAX_TRACKING_ERROR_RAD = 0.20
MAX_JOINT_RATE_RAD_S = 4.0

# A candidate must pass at least this fraction of MC trials.
MIN_SUCCESS_RATE = 0.95

# "Clear margin" for ranking/selection.
CLEAR_SUPPORT_MARGIN_M = 0.020
CLEAR_CLEARANCE_M = 0.006


def fail(msg):
    print(f"\nSTOP: {msg}", file=sys.stderr)
    raise SystemExit(2)


def ensure_environment():
    if not RUNNER.exists():
        fail(f"runner missing: {RUNNER}")
    if not MODEL.exists():
        fail(f"model missing: {MODEL}")

    source = (ROOT / "tools" / "one_leg_lift_sim.cpp").read_text(errors="replace")

    required = [
        "--shift-x-mm", "--shift-y-mm", "--shift-s", "--hold-s",
        "--lift-mm", "--lift-s", "--lower-s", "--kp", "--kd",
        "--payload-kg", "--com-offset-x-mm", "--com-offset-y-mm",
        "--friction-scale", "--compliance-scale",
        "--joint-offset-rad", "--sensor-noise-rad",
        "--delay-ms", "--seed",
    ]

    missing = [x for x in required if x not in source]
    if missing:
        fail("runner missing CLI options: " + ", ".join(missing))


def candidate_args(c):
    return [
        "--shift-x-mm", str(c["shift_x_mm"]),
        "--shift-y-mm", str(c["shift_y_mm"]),
        "--shift-s", str(c["shift_s"]),
        "--hold-s", str(c["hold_s"]),
        "--lift-mm", str(c["lift_mm"]),
        "--lift-s", str(c["lift_s"]),
        "--lower-s", str(c["lower_s"]),
        "--kp", str(c["kp"]),
        "--kd", str(c["kd"]),
    ]


def mc_args(mc):
    return [
        "--payload-kg", str(mc["payload_kg"]),
        "--com-offset-x-mm", str(mc["com_offset_x_mm"]),
        "--com-offset-y-mm", str(mc["com_offset_y_mm"]),
        "--friction-scale", str(mc["friction_scale"]),
        "--compliance-scale", str(mc["compliance_scale"]),
        "--joint-offset-rad", str(mc["joint_offset_rad"]),
        "--sensor-noise-rad", str(mc["sensor_noise_rad"]),
        "--delay-ms", str(mc["delay_ms"]),
        "--seed", str(mc["seed"]),
    ]


def sample_mc(rng, seed):
    """
    Initial simulation robustness envelope.
    These are research perturbations, not claims about measured Lite3
    hardware uncertainty.
    """
    return {
        "seed": seed,

        # Added torso payload.
        "payload_kg": round(rng.uniform(0.0, 1.0), 6),

        # Torso inertial CoM perturbation.
        "com_offset_x_mm": round(rng.uniform(-10.0, 10.0), 6),
        "com_offset_y_mm": round(rng.uniform(-10.0, 10.0), 6),

        # Contact-model perturbations.
        "friction_scale": round(rng.uniform(0.80, 1.20), 6),
        "compliance_scale": round(rng.uniform(0.80, 1.20), 6),

        # Controller observation perturbations.
        "joint_offset_rad": round(rng.uniform(0.0, 0.010), 7),
        "sensor_noise_rad": round(rng.uniform(0.0, 0.004), 7),
        "delay_ms": round(rng.uniform(0.0, 15.0), 4),
    }


def get_number(d, key, default=float("nan")):
    v = d.get(key, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def evaluate(summary):
    reasons = []

    if not summary.get("completed", False):
        reasons.append(summary.get("abort_reason") or "runner aborted")

    clearance = get_number(summary, "max_measured_fr_lift_m")
    support = get_number(summary, "minimum_support_margin_during_lift_m")
    roll = get_number(summary, "max_abs_roll_during_lift_deg")
    pitch = get_number(summary, "max_abs_pitch_during_lift_deg")
    torque = get_number(summary, "peak_pd_torque_nm")
    tracking = get_number(summary, "max_tracking_error_rad")
    rate = get_number(summary, "max_joint_rate_rad_s")
    touchdown = get_number(summary, "touchdown_velocity_m_s")
    final_error = get_number(summary, "final_joint_error_rad")

    if not math.isfinite(clearance) or clearance < MIN_CLEARANCE_M:
        reasons.append("clearance<5mm")

    if not math.isfinite(support) or support <= MIN_SUPPORT_MARGIN_M:
        reasons.append("support_margin<=0")

    if not math.isfinite(roll) or roll > MAX_ROLL_DEG:
        reasons.append("roll_limit")

    if not math.isfinite(pitch) or pitch > MAX_PITCH_DEG:
        reasons.append("pitch_limit")

    if not math.isfinite(torque) or torque > MAX_TORQUE_NM + 1e-9:
        reasons.append("torque_limit")

    if not math.isfinite(tracking) or tracking > MAX_TRACKING_ERROR_RAD:
        reasons.append("tracking_error")

    if not math.isfinite(rate) or rate > MAX_JOINT_RATE_RAD_S:
        reasons.append("joint_rate")

    if not math.isfinite(touchdown) or abs(touchdown) > MAX_TOUCHDOWN_SPEED_M_S:
        reasons.append("touchdown_velocity")

    if not math.isfinite(final_error) or final_error > MAX_FINAL_JOINT_ERROR_RAD:
        reasons.append("return_pose_error")

    return len(reasons) == 0, reasons


def run_one(candidate_id, trial_id, candidate, mc):
    run_dir = OUTROOT / "runs" / f"c{candidate_id:03d}_r{trial_id:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(RUNNER),
        "--model", str(MODEL),
        "--output-dir", str(run_dir),
    ] + candidate_args(candidate) + mc_args(mc)

    p = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    summary_path = run_dir / "summary.json"

    if not summary_path.exists():
        return {
            **candidate,
            **mc,
            "candidate_id": candidate_id,
            "trial_id": trial_id,
            "success": False,
            "reasons": "no_summary",
            "returncode": p.returncode,
        }

    try:
        summary = json.loads(summary_path.read_text())
    except Exception:
        return {
            **candidate,
            **mc,
            "candidate_id": candidate_id,
            "trial_id": trial_id,
            "success": False,
            "reasons": "invalid_summary",
            "returncode": p.returncode,
        }

    success, reasons = evaluate(summary)

    return {
        **candidate,
        **mc,
        "candidate_id": candidate_id,
        "trial_id": trial_id,
        "success": success,
        "reasons": "|".join(reasons),
        "returncode": p.returncode,

        "clearance_m":
            get_number(summary, "max_measured_fr_lift_m"),

        "support_margin_m":
            get_number(summary, "minimum_support_margin_during_lift_m"),

        "roll_deg":
            get_number(summary, "max_abs_roll_during_lift_deg"),

        "pitch_deg":
            get_number(summary, "max_abs_pitch_during_lift_deg"),

        "torque_nm":
            get_number(summary, "peak_pd_torque_nm"),

        "tracking_error_rad":
            get_number(summary, "max_tracking_error_rad"),

        "joint_rate_rad_s":
            get_number(summary, "max_joint_rate_rad_s"),

        "touchdown_velocity_m_s":
            get_number(summary, "touchdown_velocity_m_s"),

        "final_joint_error_rad":
            get_number(summary, "final_joint_error_rad"),
    }


def smoke_candidates():
    # Baseline + two nearby candidates.
    return [
        {
            "shift_x_mm": 60,
            "shift_y_mm": 60,
            "shift_s": 2.0,
            "hold_s": 0.0,
            "lift_mm": 15,
            "lift_s": 1.5,
            "lower_s": 1.5,
            "kp": 180,
            "kd": 3.5,
        },
        {
            "shift_x_mm": 55,
            "shift_y_mm": 55,
            "shift_s": 2.5,
            "hold_s": 0.5,
            "lift_mm": 15,
            "lift_s": 1.75,
            "lower_s": 1.75,
            "kp": 170,
            "kd": 3.5,
        },
        {
            "shift_x_mm": 65,
            "shift_y_mm": 60,
            "shift_s": 2.5,
            "hold_s": 0.5,
            "lift_mm": 17,
            "lift_s": 2.0,
            "lower_s": 2.0,
            "kp": 180,
            "kd": 4.0,
        },
    ]


def random_candidate(rng):
    # Search around the already successful simulation primitive.
    return {
        "shift_x_mm": round(rng.uniform(45, 70), 2),
        "shift_y_mm": round(rng.uniform(45, 70), 2),
        "shift_s": round(rng.uniform(1.75, 3.0), 3),
        "hold_s": round(rng.uniform(0.0, 1.0), 3),
        "lift_mm": round(rng.uniform(12, 20), 2),
        "lift_s": round(rng.uniform(1.25, 2.25), 3),
        "lower_s": round(rng.uniform(1.25, 2.25), 3),
        "kp": round(rng.uniform(150, 190), 2),
        "kd": round(rng.uniform(2.8, 4.5), 3),
    }


def write_csv(rows, path):
    if not rows:
        return

    fields = list(rows[0].keys())

    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def aggregate(rows, candidates):
    result = []

    for cid, candidate in enumerate(candidates):
        rr = [r for r in rows if r["candidate_id"] == cid]

        successes = sum(bool(r["success"]) for r in rr)
        rate = successes / len(rr) if rr else 0.0

        def finite_values(key):
            out = []
            for r in rr:
                try:
                    v = float(r[key])
                    if math.isfinite(v):
                        out.append(v)
                except Exception:
                    pass
            return out

        supports = finite_values("support_margin_m")
        clearances = finite_values("clearance_m")
        rolls = finite_values("roll_deg")
        pitches = finite_values("pitch_deg")
        torques = finite_values("torque_nm")
        touchdowns = [abs(v) for v in finite_values("touchdown_velocity_m_s")]
        finals = finite_values("final_joint_error_rad")

        item = {
            "candidate_id": cid,
            **candidate,
            "runs": len(rr),
            "successes": successes,
            "success_rate": rate,
            "worst_support_margin_m": min(supports) if supports else float("nan"),
            "worst_clearance_m": min(clearances) if clearances else float("nan"),
            "worst_roll_deg": max(rolls) if rolls else float("nan"),
            "worst_pitch_deg": max(pitches) if pitches else float("nan"),
            "worst_torque_nm": max(torques) if torques else float("nan"),
            "worst_touchdown_speed_m_s": max(touchdowns) if touchdowns else float("nan"),
            "worst_final_joint_error_rad": max(finals) if finals else float("nan"),
        }

        item["clear_margin"] = (
            rate >= MIN_SUCCESS_RATE
            and math.isfinite(item["worst_support_margin_m"])
            and item["worst_support_margin_m"] >= CLEAR_SUPPORT_MARGIN_M
            and math.isfinite(item["worst_clearance_m"])
            and item["worst_clearance_m"] >= CLEAR_CLEARANCE_M
        )

        result.append(item)

    # No fake scalar physics score. Rank first by empirical success,
    # then by worst-case support and clearance.
    result.sort(
        key=lambda x: (
            x["success_rate"],
            x["worst_support_margin_m"]
                if math.isfinite(x["worst_support_margin_m"]) else -999,
            x["worst_clearance_m"]
                if math.isfinite(x["worst_clearance_m"]) else -999,
        ),
        reverse=True,
    )

    return result


def write_summary(agg, mode, total_runs):
    path = OUTROOT / "summary.md"

    qualified = [
        x for x in agg
        if x["success_rate"] >= MIN_SUCCESS_RATE and x["clear_margin"]
    ]

    lines = [
        "# Lite3 FR Single-Leg Simulation Sweep",
        "",
        f"Mode: **{mode}**",
        f"Total simulations: **{total_runs}**",
        "",
        "This is simulation-only evidence. It does not approve hardware gains or motion.",
        "",
        "## Acceptance",
        "",
        f"- Minimum success rate: {MIN_SUCCESS_RATE:.0%}",
        f"- Clearance: >= {MIN_CLEARANCE_M*1000:.1f} mm",
        f"- Clear-margin clearance: >= {CLEAR_CLEARANCE_M*1000:.1f} mm",
        f"- Clear support margin: >= {CLEAR_SUPPORT_MARGIN_M*1000:.1f} mm",
        f"- Touchdown speed: <= {MAX_TOUCHDOWN_SPEED_M_S:.3f} m/s",
        f"- Final joint error: <= {MAX_FINAL_JOINT_ERROR_RAD:.3f} rad",
        "",
        "## Top candidates",
        "",
    ]

    for rank, x in enumerate(agg[:5], 1):
        lines += [
            f"### {rank}. Candidate {x['candidate_id']}",
            "",
            f"- Success: {x['successes']}/{x['runs']} ({x['success_rate']:.1%})",
            f"- Shift: X={x['shift_x_mm']} mm, Y={x['shift_y_mm']} mm",
            f"- Shift/hold: {x['shift_s']} s / {x['hold_s']} s",
            f"- Lift: {x['lift_mm']} mm over {x['lift_s']} s",
            f"- Lower: {x['lower_s']} s",
            f"- PD: kp={x['kp']}, kd={x['kd']}",
            f"- Worst support margin: {x['worst_support_margin_m']*1000:.2f} mm",
            f"- Worst clearance: {x['worst_clearance_m']*1000:.2f} mm",
            f"- Worst roll/pitch: {x['worst_roll_deg']:.2f} / {x['worst_pitch_deg']:.2f} deg",
            f"- Worst torque: {x['worst_torque_nm']:.2f} Nm",
            f"- Worst touchdown speed: {x['worst_touchdown_speed_m_s']:.3f} m/s",
            f"- Clear margin: {'YES' if x['clear_margin'] else 'NO'}",
            "",
        ]

    lines += [
        "## Selection gate",
        "",
    ]

    if qualified:
        lines.append(
            f"{len(qualified)} candidate(s) satisfy both >=95% success "
            "and the configured clear-margin gate."
        )
    else:
        lines.append(
            "No candidate currently satisfies both >=95% success and "
            "the configured clear-margin gate."
        )

    lines += [
        "",
        "## Remaining sim-to-real gaps",
        "",
        "- Payload model is represented as additional torso mass, not a measured payload inertia model.",
        "- CoM uncertainty ranges are simulation assumptions, not measured Lite3 identification data.",
        "- Contact friction/compliance ranges are not calibrated against the real floor/feet.",
        "- Joint-zero, sensor-noise and delay ranges are not yet based on hardware characterization.",
        "- Motor/gearbox dynamics, backlash, battery-voltage effects and thermal effects are not identified here.",
        "- Simulation success must therefore not be interpreted as permission to copy these parameters directly to hardware.",
        "",
    ]

    path.write_text("\n".join(lines))


def make_plots(agg):
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        print("[WARN] matplotlib unavailable; plots skipped:", e)
        return

    ids = [x["candidate_id"] for x in agg]
    rates = [x["success_rate"] * 100 for x in agg]

    plt.figure(figsize=(10, 5))
    plt.bar([str(x) for x in ids], rates)
    plt.xlabel("Candidate")
    plt.ylabel("Monte Carlo success [%]")
    plt.ylim(0, 105)
    plt.tight_layout()
    plt.savefig(OUTROOT / "success_rate.png", dpi=150)
    plt.close()

    margins = [x["worst_support_margin_m"] * 1000 for x in agg]

    plt.figure(figsize=(10, 5))
    plt.bar([str(x) for x in ids], margins)
    plt.xlabel("Candidate")
    plt.ylabel("Worst support margin [mm]")
    plt.tight_layout()
    plt.savefig(OUTROOT / "worst_support_margin.png", dpi=150)
    plt.close()

    clearance = [x["worst_clearance_m"] * 1000 for x in agg]

    plt.figure(figsize=(10, 5))
    plt.bar([str(x) for x in ids], clearance)
    plt.xlabel("Candidate")
    plt.ylabel("Worst FR clearance [mm]")
    plt.tight_layout()
    plt.savefig(OUTROOT / "worst_clearance.png", dpi=150)
    plt.close()


def execute(candidates, mc_runs, master_seed, mode):
    rng = random.Random(master_seed)
    rows = []

    OUTROOT.mkdir(parents=True, exist_ok=True)

    total = len(candidates) * mc_runs
    count = 0

    print(f"\n===== {mode.upper()} =====")
    print("Candidates:", len(candidates))
    print("MC runs/candidate:", mc_runs)
    print("Total simulations:", total)
    print("Master seed:", master_seed)
    print()

    # Each trial gets its own deterministic perturbation seed.
    for cid, candidate in enumerate(candidates):
        print(f"Candidate {cid}: {candidate}")

        for trial in range(mc_runs):
            count += 1
            seed = master_seed + cid * 100000 + trial
            local_rng = random.Random(seed)
            mc = sample_mc(local_rng, seed)

            row = run_one(cid, trial, candidate, mc)
            rows.append(row)

            status = "PASS" if row["success"] else "FAIL"
            print(
                f"[{count:4d}/{total}] "
                f"C{cid:03d} R{trial:03d} {status} "
                f"clear={row.get('clearance_m', float('nan'))*1000:.2f}mm "
                f"margin={row.get('support_margin_m', float('nan'))*1000:.2f}mm "
                f"reason={row.get('reasons','')}"
            )

    write_csv(rows, OUTROOT / "results.csv")

    agg = aggregate(rows, candidates)
    write_csv(agg, OUTROOT / "candidates.csv")
    write_summary(agg, mode, len(rows))
    make_plots(agg)

    print("\n===== RESULTS =====")
    for rank, x in enumerate(agg[:5], 1):
        print(
            f"{rank}. C{x['candidate_id']:03d}: "
            f"{x['success_rate']:.1%} "
            f"({x['successes']}/{x['runs']}), "
            f"worst margin={x['worst_support_margin_m']*1000:.2f}mm, "
            f"worst clearance={x['worst_clearance_m']*1000:.2f}mm, "
            f"clear_margin={'YES' if x['clear_margin'] else 'NO'}"
        )

    print("\nSaved:")
    print(" ", OUTROOT / "results.csv")
    print(" ", OUTROOT / "candidates.csv")
    print(" ", OUTROOT / "summary.md")
    print(" ", OUTROOT / "success_rate.png")
    print(" ", OUTROOT / "worst_support_margin.png")
    print(" ", OUTROOT / "worst_clearance.png")

    return agg


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--batch", action="store_true")

    ap.add_argument("--candidates", type=int, default=40)
    ap.add_argument("--mc-runs", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260918)

    args = ap.parse_args()

    ensure_environment()

    if args.smoke and args.batch:
        fail("choose --smoke or --batch")

    if not args.smoke and not args.batch:
        fail("use --smoke first; use --batch only after smoke is reviewed")

    if args.smoke:
        # Exactly 3 x 5 = 15 simulations.
        execute(
            candidates=smoke_candidates(),
            mc_runs=5,
            master_seed=args.seed,
            mode="smoke",
        )
        return

    if args.candidates < 1 or args.mc_runs < 1:
        fail("candidate and MC counts must be >= 1")

    rng = random.Random(args.seed)

    # Always include the known deterministic baseline.
    candidates = [smoke_candidates()[0]]

    while len(candidates) < args.candidates:
        candidates.append(random_candidate(rng))

    execute(
        candidates=candidates,
        mc_runs=args.mc_runs,
        master_seed=args.seed,
        mode="batch",
    )


if __name__ == "__main__":
    main()
