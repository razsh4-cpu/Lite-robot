#!/usr/bin/env python3
"""Deterministic offline campaign. No robot imports, sockets, or SDK binaries."""
import argparse
import concurrent.futures
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "third_party/deep_robotics_model/Lite3/Lite3_mjcf/mjcf/Lite3.xml"
BIN = ROOT / "build-robust-fr/robust_fr_sim"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def run(job):
    name, params, out = job
    command = [str(BIN), "--model", str(MODEL), "--out", str(out / name)]
    for key, value in params.items():
        command += ["--" + key, str(value)]
    dump(out / (name + "_input.json"), {"parameters": params, "command": command})
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{name}: {result.stderr}")
    record = json.loads((out / (name + ".json")).read_text())
    record.update(name=name, parameters=params)
    record["failure"] = (record["first_failure"] if not record["safe"] else
                         "unload_not_verified" if not record["unload_pass"] else
                         "lift_not_verified" if params.get("lift", 0) and not record["lift_pass"] else "none")
    # Ranking is subordinate to hard acceptance gates; a good score cannot
    # turn a failure into PASS. Units/scales are published in README.
    record["score"] = (100*record["min_fr_fraction"] +
        1000*max(0, .001-record["min_triangle_margin_verify_m"]) +
        10*(record["max_roll_rad"]+record["max_pitch_rad"]+record["max_tracking_rad"]) +
        record["max_dq_rad_s"] + .1*record["max_target_acceleration_rad_s2"] +
        .001*record["max_force_slew_n_s"] +
        100*max(0, record["max_friction_ratio"]-1) +
        10*max(0, .05-record["min_joint_limit_distance_rad"]) -
        100*record["fr_lift_clearance_m"] +
        10000*(not record["safe"]) + 10000*(not record["plan_pass"]))
    return record


def batch(jobs, workers):
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        results = []
        for result in pool.map(run, jobs):
            results.append(result)
            if len(results) % 25 == 0:
                print(f"completed {len(results)}/{len(jobs)}", flush=True)
        return results


def audit(out):
    root = ET.parse(MODEL).getroot()
    data = {
        "source": str(MODEL.relative_to(ROOT)),
        "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "source_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob("*") if p.is_file()},
        "bodies": [{"name": b.get("name"), "inertial": b.find("inertial").attrib} for b in root.iter("body") if b.find("inertial") is not None],
        "joints": [j.attrib for j in root.iter("joint") if j.get("name")],
        "actuators": [a.attrib for a in root.find("actuator")],
        "defaults": ET.tostring(root.find("default"), encoding="unicode"),
        "payload_components": {p: "NOT EXPLICITLY REPRESENTED; actual mass/pose unknown" for p in ["computer", "D455", "RPLIDAR S2", "mounts/cables"]},
        "unknowns": ["physical link mass/inertia and their measurement provenance", "actual payload mass, inertia and attachment pose", "real foot shape/compliance and shank-ground collision accuracy", "ground friction", "motor torque-speed curve, saturation, gearbox friction, backlash", "physical damping", "actual command/measurement delay and jitter", "real controller gains/effective gain calibration", "contact-force channel calibration (historically all zero)", "initial physical pose/support forces"],
        "simulation": {"engine": "bundled MuJoCo 2.3.7", "dt_s": .001, "control_hz": 1000, "trace_hz": 100, "criteria_hz": 1000, "settle_s": 3, "evaluation_start_s": 2.5, "stand_q": [0, -.7729795255029084, 1.5005003509817765], "nominal_gains": [100, 2.5], "torque_model": "ideal motor, external simulated PD only, zero feed-forward, +/-30 Nm saturation", "native_contact": "unchanged MJCF", "sphere_only": "disable only SHANK collision geoms in private runtime model; explicit unvalidated alternative"},
        "thresholds": {"max_target_delta_rad": .03, "max_target_speed_rad_s": .10, "max_measured_speed_rad_s": .50, "max_tracking_rad": .15, "max_roll_pitch_deg": 3, "min_joint_limit_distance_rad": .01, "max_friction_utilization": 1.05, "max_nonfoot_force_n": 1, "support_contact_n": 2, "unload_fraction_max": .05, "unload_continuous_s": .5, "unload_fr_height_abs_m": .002, "min_triangle_margin_m": .001, "lift_clearance_min_m": .003, "lift_hold_s": .5, "lift_fr_force_max_n": 1},
    }
    dump(out / "model_audit.json", data)


def variations(seed, count):
    rng = random.Random(seed)
    result = []
    for i in range(count):
        p = {"mass": rng.uniform(.9, 1.1), "payload": rng.uniform(0, 1.5),
             "com-x": rng.uniform(-.08, .08), "com-y": rng.uniform(-.06, .06), "com-z": rng.uniform(.05,.18),
             "friction": rng.uniform(.35, 1), "strength": rng.uniform(.85, 1),
             "kp-scale": rng.uniform(.9,1.1), "kd-scale": rng.uniform(.9,1.1),
             "damping": rng.uniform(0,.15), "joint-friction": rng.uniform(0,.1),
             "qerr": rng.uniform(-.01,.01), "roll": rng.uniform(-.01,.01), "pitch": rng.uniform(-.01,.01),
             "delay": rng.choice([0,.001,.002,.004]), "contact": rng.uniform(.75,1.5),
             "sphere-only": 0 if i%5==0 else 1}
        for b in range(2,18):
            p["link"+str(b)] = rng.uniform(.95,1.05)
        result.append(p)
    return result


def perturb(candidate, variation):
    params={**candidate, **variation}
    params["kp"]=min(100,max(60,candidate["kp"]*params.pop("kp-scale")))
    params["kd"]=min(2.5,max(.7,candidate["kd"]*params.pop("kd-scale")))
    return params


def plots(out, records):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/lite3-robust-fr-matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    for record in records:
        data=np.genfromtxt(out/(record["name"]+".csv"),delimiter=",",names=True,dtype=None,encoding="utf-8")
        fig, axes=plt.subplots(5,1,figsize=(12,15),sharex=True)
        t=data["time"]
        for leg in ["FL","FR","HL","HR"]: axes[0].plot(t,data[leg+"_fz"],label=leg)
        axes[0].set_ylabel("Foot world Fz (N)")
        for k in ["com_x","com_y","support_margin","triangle_margin"]:
            values=np.where(data[k]<=-.99,np.nan,data[k]) if "margin" in k else data[k]
            axes[1].plot(t,values,label=k)
        axes[1].set_title("Undefined support polygons are gaps, not zero margin",fontsize=9)
        axes[1].set_ylabel("Position / margin (m)")
        for k in ["roll","pitch"]:axes[2].plot(t,np.degrees(data[k]),label=k)
        axes[2].axhline(3,color="red",linestyle=":");axes[2].axhline(-3,color="red",linestyle=":");axes[2].set_ylabel("Attitude (deg)")
        for j in range(12):
            axes[3].plot(t,data["q"+str(j)],alpha=.6,label=f"q{j}")
            axes[3].plot(t,data["target"+str(j)],linestyle="--",alpha=.6)
        axes[3].set_ylabel("q actual / dashed target (rad)")
        axes[4].plot(t,1000*data["fr_clearance"],label="FR sphere surface clearance")
        axes[4].set_ylabel("Clearance (mm)");axes[4].set_xlabel("Time (s)")
        for ax in axes:
            ax.axvspan(0,2.5,color="gray",alpha=.12)
            ax.grid(alpha=.3);ax.legend(loc="upper right",ncol=4,fontsize=7)
        fig.suptitle(record["name"]+": "+record["failure"]);fig.tight_layout();fig.savefig(out/(record["name"]+".png"));plt.close(fig)
        fig,axes=plt.subplots(4,3,figsize=(14,10),sharex=True)
        for j,ax in enumerate(axes.flat):
            ax.plot(t,data["q"+str(j)],label="actual")
            ax.plot(t,data["target"+str(j)],"--",label="target")
            ax.set_title(["FL","FR","HL","HR"][j//3]+" "+["hip","thigh","knee"][j%3]);ax.set_ylabel("rad");ax.grid(alpha=.3);ax.legend(fontsize=8)
        fig.suptitle(record["name"]+": joint tracking");fig.tight_layout();fig.savefig(out/(record["name"]+"_tracking.png"));plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=ROOT/"artifacts/robust_fr_campaign")
    parser.add_argument("--trials",type=int,default=100)
    parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    audit(out)
    stand=batch([("baseline_native",{"duration":2},out),("baseline_sphere",{"duration":2,"sphere-only":1},out)],args.workers)
    dump(out/"stand_results.json",stand)
    if not stand[1]["stand_pass"]:
        dump(out/"blocked.json",{"reason":"stand failed even under explicit sphere-contact hypothesis"});return
    jobs=[]
    for idx,(x,y,duration,gains) in enumerate(itertools.product([-.006,-.004,-.002,0,.002],[0,.002,.004,.006],[2,4],[(100,2.5),(60,.7)])):
        jobs.append((f"shift_{idx:03}",{"x":x,"y":y,"duration":duration,"kp":gains[0],"kd":gains[1],"sphere-only":1},out))
    sweep=batch(jobs,args.workers);dump(out/"shift_results.json",sweep)
    valid=sorted([r for r in sweep if r["stand_pass"] and r["plan_pass"] and r["safe"]],key=lambda r:r["score"])
    selected=[]
    for r in valid:
        if all((r["parameters"]["x"],r["parameters"]["y"])!=(v["parameters"]["x"],v["parameters"]["y"]) for v in selected):selected.append(r)
        if len(selected)==3:break
    scenarios=variations(20260921,args.trials);dump(out/"scenarios.json",scenarios)
    robust=[]
    for idx,candidate in enumerate(selected):
        print(f"Candidate {idx+1}: {candidate['parameters']}; nominal unload={candidate['unload_pass']}",flush=True)
        trials=batch([(f"candidate_{idx+1}_trial_{i:03}",perturb(candidate["parameters"],variation),out) for i,variation in enumerate(scenarios)],args.workers)
        robust.append({"candidate":candidate,"trials":trials,"unload_passed":sum(t["unload_pass"] for t in trials),"safe_passed":sum(t["safe"] for t in trials),"total":len(trials),"interpretation":"robustness of unloading" if candidate["unload_pass"] else "diagnostic variations; nominal unloading failed"})
        dump(out/"robustness_results.json",robust)
    # No lift grid unless Stage 2 really unloaded with the unchanged envelope.
    lift_jobs=[]
    for i,r in enumerate(selected):
        if r["unload_pass"]:
            for height in [.001,.003,.005]:lift_jobs.append((f"lift_{i}_{height}",{**r["parameters"],"lift":height},out))
    lifts=batch(lift_jobs,args.workers) if lift_jobs else []
    dump(out/"lift_results.json",lifts)
    all_records=stand+sweep+[t for r in robust for t in r["trials"]]+lifts
    keys=[k for k in all_records[0] if k!="parameters"]
    with (out/"all_results.csv").open("w") as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows({k:r[k] for k in keys} for r in all_records)
    plots(out,stand+selected)
    summary={"stage1_native_pass":stand[0]["stand_pass"],"stage1_sphere_pass":stand[1]["stand_pass"],"shift_trials":len(sweep),"nominal_unload_passes":sum(r["unload_pass"] for r in sweep),"lift_trials":len(lifts),"lift_passes":sum(r["lift_pass"] for r in lifts),"candidates":[{"nominal":r["candidate"]["name"],"parameters":r["candidate"]["parameters"],"unload_passed":r["unload_passed"],"safe_passed":r["safe_passed"],"total":r["total"]} for r in robust],"status":"NO_ROBUST_LIFT_DEMONSTRATED"}
    dump(out/"summary.json",summary);print(json.dumps(summary,indent=2),flush=True)


if __name__=="__main__":main()
