#!/usr/bin/env python3
"""Fit a trace-derived loaded-posture model and propose Force_opt3 offline.

The tool deliberately separates commanded posture from the posture measured under
load.  It only reads completed JSONL traces and never imports or opens MotionSDK.
Bulk traces remain local evidence under /tmp and are not copied into Git.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


STAND = np.tile(np.array([0.0, -0.7729795255029084, 1.5005003509817765]), 4)
MASS = 11.9376
G = 9.81
WEIGHT = MASS * G
TORQUE_LIMIT = np.tile(np.array([16.8, 16.8, 25.2]), 4)
L, BODY_HALF_WIDTH, HIP_OFFSET = 0.1745, 0.062, 0.09735
THIGH, SHANK = 0.20, 0.21012
DAMPING = 1e-4


def rotation(angle: float, axis: tuple[float, float, float]) -> np.ndarray:
    x, y, z = axis
    c, s, one_c = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
    return np.array([
        [c + x*x*one_c, x*y*one_c-z*s, x*z*one_c+y*s],
        [y*x*one_c+z*s, c+y*y*one_c, y*z*one_c-x*s],
        [z*x*one_c-y*s, z*y*one_c+x*s, c+z*z*one_c],
    ])


def foot_position(leg: int, q: np.ndarray) -> np.ndarray:
    front, left = leg < 2, leg in (0, 2)
    r = rotation(float(q[0]), (-1.0, 0.0, 0.0))
    p = np.array([L if front else -L,
                  BODY_HALF_WIDTH if left else -BODY_HALF_WIDTH, 0.0])
    p += r @ np.array([0.0, HIP_OFFSET if left else -HIP_OFFSET, 0.0])
    r = r @ rotation(float(q[1]), (0.0, -1.0, 0.0))
    p += r @ np.array([0.0, 0.0, -THIGH])
    r = r @ rotation(float(q[2]), (0.0, -1.0, 0.0))
    return p + r @ np.array([0.0, 0.0, -SHANK])


def jacobian(leg: int, q: np.ndarray) -> np.ndarray:
    result = np.zeros((3, 3))
    epsilon = 1e-6
    for joint in range(3):
        high, low = q.copy(), q.copy()
        high[joint] += epsilon
        low[joint] -= epsilon
        result[:, joint] = (
            foot_position(leg, high) - foot_position(leg, low)) / (2.0 * epsilon)
    return result


def load_proxy(q: np.ndarray, torque: np.ndarray) -> np.ndarray:
    result = np.zeros(4)
    for leg in range(4):
        jt = jacobian(leg, q[3*leg:3*leg+3]).T
        force = np.linalg.solve(
            jt.T @ jt + DAMPING*DAMPING*np.eye(3),
            jt.T @ (-torque[3*leg:3*leg+3]))
        result[leg] = force[2]
    return result


@dataclass
class Run:
    path: str
    name: str
    target: np.ndarray
    actual: np.ndarray
    settle_actual: np.ndarray
    torque: np.ndarray
    baseline_proxy: np.ndarray
    hold_proxy: np.ndarray
    load_percent: np.ndarray
    roll: float
    pitch: float


def discover_traces(directory: str) -> list[tuple[str, str]]:
    traces: list[tuple[str, str]] = []
    for path in glob.glob(os.path.join(directory, "lite3-stand-trace-*.jsonl")):
        # Inert state-machine traces are much smaller and have synthetic timing.
        if os.path.getsize(path) < 10_000_000:
            continue
        hold = ""
        with open(path, encoding="utf-8") as stream:
            for line in stream:
                if "BODY_SHIFT_" not in line or "_HOLD" not in line:
                    continue
                match = re.search(r'"phase":"([^"]+_HOLD)"', line)
                if match:
                    hold = match.group(1)
                    break
        if hold:
            traces.append((path, hold))
    return sorted(traces, key=lambda item: os.path.getmtime(item[0]))


def median_rows(rows: list[dict], key: str) -> np.ndarray:
    return np.median(np.asarray([row[key] for row in rows], dtype=float), axis=0)


def read_run(path: str, hold_phase: str) -> Run | None:
    settle_phase = hold_phase[:-4] + "SETTLE"
    selected = {settle_phase: [], hold_phase: []}
    end_reason = ""
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            phase = row.get("phase")
            if (phase in selected and row.get("reason") == "SENT" and
                    isinstance(row.get("position"), list)):
                selected[phase].append(row)
            end_reason = row.get("end_reason", end_reason)
    if len(selected[hold_phase]) < 100:
        return None
    if end_reason not in ("body shift calibration complete",
                          "send guard rejected output"):
        return None

    settle_rows, hold_rows = selected[settle_phase], selected[hold_phase]
    target = median_rows(hold_rows, "target")
    actual = median_rows(hold_rows, "position")
    settle_actual = (median_rows(settle_rows, "position") if settle_rows
                     else np.full(12, np.nan))
    torque = median_rows(hold_rows, "torque")
    baseline_proxy = (np.median(np.asarray([
        load_proxy(np.asarray(row["position"]), np.asarray(row["torque"]))
        for row in settle_rows]), axis=0) if settle_rows
        else np.full(4, np.nan))
    hold_proxy = np.median(np.asarray([
        load_proxy(np.asarray(row["position"]), np.asarray(row["torque"]))
        for row in hold_rows]), axis=0)
    load_percent = 100.0 * (hold_proxy-baseline_proxy) / baseline_proxy
    name = hold_phase.removeprefix("BODY_SHIFT_").removesuffix("_HOLD")
    return Run(path, name, target, actual, settle_actual, torque,
               baseline_proxy, hold_proxy, load_percent,
               float(np.median([row["roll"] for row in hold_rows])),
               float(np.median([row["pitch"] for row in hold_rows])))


class Ridge:
    def __init__(self, alpha: float):
        self.alpha = alpha
        self.mean = np.empty(0)
        self.scale = np.empty(0)
        self.coef = np.empty((0, 0))
        self.inverse = np.empty((0, 0))
        self.residual_std = np.empty(0)

    def fit(self, x: np.ndarray, y: np.ndarray) -> "Ridge":
        self.mean = x.mean(axis=0)
        self.scale = x.std(axis=0)
        self.scale[self.scale < 1e-10] = 1.0
        z = (x-self.mean)/self.scale
        design = np.c_[np.ones(len(z)), z]
        penalty = np.eye(design.shape[1])
        penalty[0, 0] = 0.0
        normal = design.T @ design + self.alpha*penalty
        self.inverse = np.linalg.inv(normal)
        self.coef = self.inverse @ design.T @ y
        residual = y-design @ self.coef
        self.residual_std = np.sqrt(np.sum(residual*residual, axis=0) /
                                    max(1, len(x)-design.shape[1]))
        return self

    def predict(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z = (np.atleast_2d(x)-self.mean)/self.scale
        design = np.c_[np.ones(len(z)), z]
        mean = design @ self.coef
        leverage = np.sum((design @ self.inverse)*design, axis=1)
        sigma = np.sqrt(1.0+leverage[:, None])*self.residual_std
        return mean, sigma


def choose_ridge(x: np.ndarray, y: np.ndarray) -> tuple[Ridge, float]:
    if y.ndim == 1:
        y = y[:, None]
    best_alpha, best_error = 0.0, float("inf")
    for alpha in (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0):
        errors = []
        for held in range(len(x)):
            mask = np.arange(len(x)) != held
            model = Ridge(alpha).fit(x[mask], y[mask])
            prediction, _ = model.predict(x[held])
            errors.append(prediction[0]-y[held])
        rmse = float(np.sqrt(np.mean(np.asarray(errors)**2)))
        if rmse < best_error:
            best_alpha, best_error = alpha, rmse
    return Ridge(best_alpha).fit(x, y), best_error


class ComplianceModel:
    """Per-joint hold error from that joint's target displacement and torque."""
    def __init__(self, runs: list[Run]):
        self.models: list[Ridge] = []
        self.cv_rmse = np.zeros(12)
        for joint in range(12):
            x = np.array([[run.target[joint]-STAND[joint], run.torque[joint]]
                          for run in runs])
            y = np.array([run.actual[joint]-run.target[joint] for run in runs])
            model, rmse = choose_ridge(x, y)
            self.models.append(model)
            self.cv_rmse[joint] = rmse

    def invert(self, desired_actual: np.ndarray,
               torque: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        target = np.zeros(12)
        sigma = np.zeros(12)
        for joint, model in enumerate(self.models):
            # Convert the standardized two-feature model to raw coefficients.
            intercept = model.coef[0, 0] - np.sum(
                model.coef[1:, 0]*model.mean/model.scale)
            target_gain = model.coef[1, 0]/model.scale[0]
            torque_gain = model.coef[2, 0]/model.scale[1]
            denominator = 1.0 + target_gain
            target[joint] = (desired_actual[joint]-intercept+
                             target_gain*STAND[joint]-
                             torque_gain*torque[joint])/denominator
            _, predicted_sigma = model.predict(np.array([
                target[joint]-STAND[joint], torque[joint]]))
            sigma[joint] = max(self.cv_rmse[joint], predicted_sigma[0, 0])
        return target, sigma

    def forward(self, target: np.ndarray,
                torque: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        actual, sigma = np.zeros(12), np.zeros(12)
        for joint, model in enumerate(self.models):
            error, predicted_sigma = model.predict(np.array([
                target[joint]-STAND[joint], torque[joint]]))
            actual[joint] = target[joint]+error[0, 0]
            sigma[joint] = max(self.cv_rmse[joint], predicted_sigma[0, 0])
        return actual, sigma


def equilibrium_forces(actual: np.ndarray, shares: np.ndarray,
                       com_offset: np.ndarray | None = None,
                       weight: float = WEIGHT) -> tuple[np.ndarray, np.ndarray]:
    shares = np.maximum(shares, 0.02)
    shares /= shares.sum()
    com_offset = np.zeros(3) if com_offset is None else com_offset
    feet = np.array([foot_position(leg, actual[3*leg:3*leg+3])-com_offset
                     for leg in range(4)])
    # Equality-constrained weighted least squares over all 12 force components.
    # The measured torque/Jacobian proxy is not calibrated force, so its shares
    # are a soft reference rather than an inconsistent hard Fz assignment.
    matrix = np.zeros((6, 12))
    for leg, (x, y, z) in enumerate(feet):
        base = 3*leg
        matrix[0, base] = 1.0
        matrix[1, base+1] = 1.0
        matrix[2, base+2] = 1.0
        matrix[3, base+1], matrix[3, base+2] = -z, y
        matrix[4, base], matrix[4, base+2] = z, -x
        matrix[5, base], matrix[5, base+1] = -y, x
    rhs = np.array([0.0, 0.0, weight, 0.0, 0.0, 0.0])
    reference = np.zeros(12)
    reference[2::3] = shares*weight
    # Permit the equilibrium projection to correct proxy-derived vertical
    # shares, while penalizing unnecessary tangential force more strongly.
    inverse_weight = np.diag(np.tile([0.35, 0.35, 1.0], 4))
    correction = (inverse_weight @ matrix.T @ np.linalg.solve(
        matrix @ inverse_weight @ matrix.T,
        rhs-matrix @ reference))
    forces = (reference+correction).reshape(4, 3)
    residual = np.r_[forces.sum(axis=0)-np.array([0.0, 0.0, weight]),
                     np.cross(feet, forces).sum(axis=0)]
    return forces, residual


def torques(actual: np.ndarray, forces: np.ndarray) -> np.ndarray:
    return np.concatenate([
        -jacobian(leg, actual[3*leg:3*leg+3]).T @ forces[leg]
        for leg in range(4)])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace-dir", default="/tmp")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--seed", type=int, default=1709)
    args = parser.parse_args()

    cache_path = Path("/tmp/force_opt3_physical_dataset_v4.npz")
    if cache_path.exists():
        cached = np.load(cache_path, allow_pickle=True)
        runs = [Run(str(cached["path"][i]), str(cached["name"][i]),
                    cached["target"][i], cached["actual"][i],
                    cached["settle_actual"][i], cached["torque"][i],
                    cached["baseline_proxy"][i], cached["hold_proxy"][i],
                    cached["load_percent"][i], float(cached["roll"][i]),
                    float(cached["pitch"][i]))
                for i in range(len(cached["name"]))]
    else:
        runs = [run for path, hold in discover_traces(args.trace_dir)
                if (run := read_run(path, hold)) is not None]
        np.savez(cache_path,
                 path=np.array([run.path for run in runs]),
                 name=np.array([run.name for run in runs]),
                 target=np.array([run.target for run in runs]),
                 actual=np.array([run.actual for run in runs]),
                 settle_actual=np.array([run.settle_actual for run in runs]),
                 torque=np.array([run.torque for run in runs]),
                 baseline_proxy=np.array([run.baseline_proxy for run in runs]),
                 hold_proxy=np.array([run.hold_proxy for run in runs]),
                 load_percent=np.array([run.load_percent for run in runs]),
                 roll=np.array([run.roll for run in runs]),
                 pitch=np.array([run.pitch for run in runs]))
    if len(runs) < 8:
        raise RuntimeError("fewer than eight completed physical traces")

    compliance = ComplianceModel(runs)
    response_runs = [run for run in runs if np.all(np.isfinite(run.load_percent))]
    movement = np.array([run.actual-run.settle_actual for run in response_runs])
    response = np.array([np.r_[run.load_percent, run.roll, run.pitch]
                         for run in response_runs])
    load_model, load_cv_rmse = choose_ridge(movement, response)
    measured_torque = np.array([run.torque for run in response_runs])
    torque_model, torque_cv_rmse = choose_ridge(movement, measured_torque)
    baseline_actual = np.median(
        np.array([run.settle_actual for run in response_runs]), axis=0)
    baseline_proxy = np.median(
        np.array([run.baseline_proxy for run in response_runs]), axis=0)

    centered = movement-movement.mean(axis=0)
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    # Four measured principal directions retain a compact, data-supported local
    # search space and avoid optimistic motion in poorly observed dimensions.
    components = vt[:min(4, len(runs)-1)]
    scales = singular[:len(components)]/math.sqrt(max(1, len(runs)-1))
    mean_movement = movement.mean(axis=0)

    def evaluate(z: np.ndarray) -> dict:
        actual = baseline_actual + mean_movement + (z*scales) @ components
        predicted, uncertainty = load_model.predict(actual-baseline_actual)
        percent = predicted[0, :4]
        hold_proxy = baseline_proxy*(1.0+percent/100.0)
        shares = np.maximum(hold_proxy, 0.1)
        shares /= shares.sum()
        forces, residual = equilibrium_forces(actual, shares)
        static_tau = torques(actual, forces)
        motor_tau, motor_tau_sigma = torque_model.predict(
            actual-baseline_actual)
        target, q_sigma = compliance.invert(actual, motor_tau[0])
        target_high_tau, _ = compliance.invert(
            actual, motor_tau[0]+motor_tau_sigma[0])
        target_sigma = np.sqrt(q_sigma*q_sigma+
                               (target_high_tau-target)**2)
        mu_required = np.linalg.norm(forces[:, :2], axis=1)/forces[:, 2]
        return {"actual": actual, "percent": percent,
                "response_sigma": uncertainty[0], "shares": shares,
                "forces": forces, "residual": residual,
                "torque": static_tau,
                "predicted_motor_torque": motor_tau[0],
                "motor_torque_sigma": motor_tau_sigma[0],
                "target": target, "q_sigma": q_sigma,
                "target_sigma": target_sigma,
                "mu_required": mu_required,
                "roll": predicted[0, 4], "pitch": predicted[0, 5]}

    def objective(z: np.ndarray) -> float:
        result = evaluate(z)
        p = result["percent"]
        support_penalty = sum(max(0.0, -p[leg])**2 for leg in (0, 2, 3))
        # Conservative FR score, support preservation, and modest extrapolation.
        return (p[1] + 1.25*result["response_sigma"][1] +
                0.20*support_penalty + 0.12*np.dot(z, z) +
                2500.0*(result["roll"]**2+result["pitch"]**2))

    def constraints(z: np.ndarray) -> np.ndarray:
        result = evaluate(z)
        return np.r_[
            0.03-np.abs(result["target"]-STAND)-2.58*result["target_sigma"],
            0.80*TORQUE_LIMIT-np.abs(result["torque"]),
            0.27-result["mu_required"],
            result["shares"]-0.08,
            0.035-np.abs(result["roll"]),
            0.035-np.abs(result["pitch"]),
        ]

    rng = np.random.default_rng(args.seed)
    candidates = []
    starts = [np.zeros(len(components))]
    # A compact deterministic multi-start is sufficient for one candidate and
    # prevents this safety preflight from turning into an open-ended sweep.
    starts += [rng.normal(0.0, 0.25, len(components)) for _ in range(2)]
    bounds = [(-2.25, 2.25)]*len(components)
    for start in starts:
        solved = minimize(objective, start, method="SLSQP", bounds=bounds,
                          constraints={"type": "ineq", "fun": constraints},
                          options={"maxiter": 180, "ftol": 1e-9})
        if solved.success and constraints(solved.x).min() >= -1e-7:
            result = evaluate(solved.x)
            result["z"] = solved.x
            result["objective"] = solved.fun
            candidates.append(result)
    if not candidates:
        zero = evaluate(np.zeros(len(components)))
        raise RuntimeError(
            "no compliance-aware candidate satisfies constraints; "
            f"zero_max_dq={np.max(np.abs(zero['target']-STAND)):.6f} "
            f"zero_max_tau={np.max(np.abs(zero['torque'])):.6f} "
            f"zero_max_mu={np.max(zero['mu_required']):.6f} "
            f"zero_min_share={np.min(zero['shares']):.6f} "
            f"zero_roll={zero['roll']:.6f} zero_pitch={zero['pitch']:.6f}")
    best = min(candidates, key=lambda item: item["objective"])

    # Monte Carlo rechecks compliance residuals, q, CoM, mass and friction.
    mc = []
    for _ in range(1000):
        actual = best["actual"] + rng.normal(0.0, best["q_sigma"])
        percent = best["percent"] + rng.normal(0.0, best["response_sigma"][:4])
        shares = np.maximum(baseline_proxy*(1.0+percent/100.0), 0.1)
        shares /= shares.sum()
        com = rng.uniform(-0.003, 0.003, 3)
        mass = MASS*rng.uniform(0.95, 1.05)
        forces, residual = equilibrium_forces(actual, shares, com, mass*G)
        static_tau = torques(actual, forces)
        motor_tau = (best["predicted_motor_torque"] +
                     rng.normal(0.0, best["motor_torque_sigma"]))
        target, _ = compliance.invert(actual, motor_tau)
        mu_required = np.max(np.linalg.norm(forces[:, :2], axis=1)/forces[:, 2])
        friction = rng.uniform(0.3, 0.5)
        valid = (np.max(np.abs(target-STAND)) <= 0.03 and
                 np.all(np.abs(static_tau) <= TORQUE_LIMIT) and
                 mu_required <= friction and
                 np.max(np.abs(residual)) < 1e-8)
        mc.append((valid, percent[1], mu_required,
                   np.max(np.abs(static_tau)), np.max(np.abs(target-STAND))))
    mc_array = np.asarray(mc, dtype=float)

    predicted_forward, forward_sigma = compliance.forward(
        best["target"], best["predicted_motor_torque"])
    report = {
        "physical_run_count": len(runs),
        "runs": [{"name": run.name, "path": run.path,
                  "load_percent": run.load_percent.tolist(),
                  "max_hold_error_rad": float(np.max(np.abs(run.actual-run.target)))}
                 for run in runs],
        "compliance_loocv_rmse_rad": compliance.cv_rmse.tolist(),
        "load_model_loocv_rmse_all_outputs": load_cv_rmse,
        "torque_model_loocv_rmse_Nm": torque_cv_rmse,
        "commanded_q_target": best["target"].tolist(),
        "predicted_loaded_q_actual": best["actual"].tolist(),
        "forward_check_loaded_q_actual": predicted_forward.tolist(),
        "predicted_tracking_offset": (best["actual"]-best["target"]).tolist(),
        "predicted_tracking_sigma": np.maximum(best["q_sigma"], forward_sigma[0]).tolist(),
        "predicted_command_sigma": best["target_sigma"].tolist(),
        "predicted_load_percent": best["percent"].tolist(),
        "predicted_load_sigma": best["response_sigma"][:4].tolist(),
        "predicted_force_shares": best["shares"].tolist(),
        "forces_N": best["forces"].tolist(),
        "mu_required": best["mu_required"].tolist(),
        "estimated_torque_Nm": best["torque"].tolist(),
        "predicted_motor_torque_Nm": best["predicted_motor_torque"].tolist(),
        "equilibrium_residual": best["residual"].tolist(),
        "predicted_roll_rad": float(best["roll"]),
        "predicted_pitch_rad": float(best["pitch"]),
        "max_joint_delta_rad": float(np.max(np.abs(best["target"]-STAND))),
        "max_target_velocity_rad_s_12s": float(
            1.875*np.max(np.abs(best["target"]-STAND))/12.0),
        "monte_carlo": {
            "trials": len(mc),
            "valid_fraction": float(mc_array[:, 0].mean()),
            "fr_unload_percent_p05_p50_p95": np.quantile(
                mc_array[:, 1], [0.05, 0.5, 0.95]).tolist(),
            "mu_required_p95": float(np.quantile(mc_array[:, 2], 0.95)),
            "max_torque_p95_Nm": float(np.quantile(mc_array[:, 3], 0.95)),
            "max_command_delta_p95_rad": float(np.quantile(mc_array[:, 4], 0.95)),
        },
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
