#!/usr/bin/env python3
"""Summarize actual campaign artifacts and paired one-factor diagnostics."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from campaign import ROOT, batch, dump

OUT=ROOT/"artifacts/robust_fr_campaign"


def load(name):return json.loads((OUT/name).read_text())


def main():
    robust=load("robustness_results.json")
    base=robust[0]["candidate"]["parameters"]
    factors=[("reference",{}),("no_y",{"y":0}),("no_x",{"x":0}),
             ("stand_gains",{"kp":100,"kd":2.5}),
             ("friction_low",{"friction":.35}),("friction_high",{"friction":1}),
             ("payload_forward",{"payload":1.5,"com-x":.08,"com-y":0}),
             ("payload_rearward",{"payload":1.5,"com-x":-.08,"com-y":0}),
             ("payload_right",{"payload":1.5,"com-x":0,"com-y":-.06}),
             ("payload_left",{"payload":1.5,"com-x":0,"com-y":.06}),
             ("mass_light",{"mass":.9}),("mass_heavy",{"mass":1.1}),
             ("weak_motor",{"strength":.85}),("delay_4ms",{"delay":.004}),
             ("native_contact",{"sphere-only":0}),
             ("contact_soft",{"contact":1.5}),("contact_stiff",{"contact":.75})]
    ablations=batch([("factor_"+name,{**base,**change},OUT) for name,change in factors],2)
    dump(OUT/"factor_results.json",ablations)
    summary=load("summary.json");nominal=load("stand_results.json")
    rows=[]
    for index,r in enumerate(robust,1):
        c=r["candidate"];trials=r["trials"];sphere=[t for t in trials if t["parameters"]["sphere-only"]]
        native=[t for t in trials if not t["parameters"]["sphere-only"]]
        record={"candidate":chr(64+index),"parameters":c["parameters"],"nominal_fr_fraction":c["min_fr_fraction"],
                "unload_passed":r["unload_passed"],"total":r["total"],"safe_passed":r["safe_passed"],
                "native_safe_passed":sum(t["safe"] for t in native),"native_total":len(native),
                "sphere_safe_passed":sum(t["safe"] for t in sphere),"sphere_total":len(sphere),
                "sphere_min_fr_fraction":min(t["min_fr_fraction"] for t in sphere),
                "sphere_max_fr_fraction":max(t["min_fr_fraction"] for t in sphere),
                "sphere_min_support_margin_m":min(t["min_support_margin_m"] for t in sphere),
                "sphere_min_triangle_margin_m":min(t["min_triangle_margin_verify_m"] for t in sphere),
                "max_roll_deg":np.degrees(max(t["max_roll_rad"] for t in trials)),
                "max_pitch_deg":np.degrees(max(t["max_pitch_rad"] for t in trials)),
                "max_tracking_rad":max(t["max_tracking_rad"] for t in trials),
                "max_dq_rad_s":max(t["max_dq_rad_s"] for t in trials),
                "max_target_delta_rad":max(t["max_target_delta_rad"] for t in trials),
                "max_target_speed_rad_s":max(t["max_target_speed_rad_s"] for t in trials)}
        trace=np.genfromtxt(OUT/(c["name"]+".csv"),delimiter=",",names=True,dtype=None,encoding="utf-8")
        hold=trace[trace["phase"]=="VERIFY_UNLOAD"]
        record["endpoint_q_targets"]=[float(hold[0]["target"+str(j)]) for j in range(12)]
        record["endpoint_q_actual"]=[float(hold[-1]["q"+str(j)]) for j in range(12)]
        record["mean_fr_fraction_during_hold"]=float(np.mean(hold["fr_fraction"]))
        record["mean_fr_force_during_hold_n"]=float(np.mean(hold["FR_fz"]))
        record["nominal_max_actual_joint_delta_rad"]=float(max(np.max(np.abs(trace["q"+str(j)]-[0,-.7729795255029084,1.5005003509817765][j%3])) for j in range(12)))
        rows.append(record)
    dump(OUT/"candidate_comparison.json",rows)
    lines=["# FR simulation campaign — 2026-09-21", "", "Status: **NO ROBUST UNLOAD OR LIFT DEMONSTRATED**. Offline evidence only.", "",
           "The standalone simulator uses unchanged acceptance limits (0.03 rad target delta, 0.10 rad/s commanded speed, 0.50 rad/s measured speed, 0.15 rad tracking, 3 degree attitude). The existing physical-control files and their pre-existing dirty changes were not edited. No hardware commands were sent.", "",
           "## Actual results", "",f"{summary['shift_trials']} nominal body-only candidates; {summary['nominal_unload_passes']} unload passes. Three distinct best candidates each received {rows[0]['total']} paired model variations. No lift search was started because the prerequisite failed. The reported robustness counts below are **unload** counts; lift success is **not evaluated**, not inferred.","",
           "| Candidate | Body x / y (mm) | Nominal FR fraction | Unload | All safety gates | Sphere-only safety | Native safety |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        p=r["parameters"];lines.append(f"| {r['candidate']} | {p['x']*1000:g} / {p['y']*1000:g} | {r['nominal_fr_fraction']*100:.2f}% | {r['unload_passed']}/{r['total']} | {r['safe_passed']}/{r['total']} | {r['sphere_safe_passed']}/{r['sphere_total']} | {r['native_safe_passed']}/{r['native_total']} |")
    lines += ["", "A safety pass does not include successful unloading. Passing rates apply only to the declared synthetic parameter distribution, not to real hardware.","", "| Candidate | Sphere FR fraction range | Worst roll / pitch (deg) | Worst tracking (rad) | Worst dq (rad/s) | Max target delta (rad) | Min sphere triangle margin (mm) |","|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:lines.append(f"| {r['candidate']} | {100*r['sphere_min_fr_fraction']:.2f}–{100*r['sphere_max_fr_fraction']:.2f}% | {r['max_roll_deg']:.3f} / {r['max_pitch_deg']:.3f} | {r['max_tracking_rad']:.4f} | {r['max_dq_rad_s']:.4f} | {r['max_target_delta_rad']:.5f} | {1000*r['sphere_min_triangle_margin_m']:.3f} |")
    lines += ["", "The triangle margin is geometric; it cannot by itself establish unloading. A four-contact spring-supported pose can have its CoM inside the three-foot triangle while FR still carries substantial load.","", "## Model audit and explanation", "",
              f"Source mass is 11.9376 kg; expected weight is {11.9376*9.81:.3f} N. Sphere-only standing foot sum is {nominal[1]['weight_stand_n']:.3f} N; individual FL/FR/HL/HR Fz are "+", ".join(f"{nominal[1][leg+'_stand_fz']:.3f}" for leg in ['FL','FR','HL','HR'])+" N. Native-model foot sum is "+f"{nominal[0]['weight_stand_n']:.3f} N because the shank meshes bear most of the weight. This contact-model ambiguity must be resolved before transfer claims.","",
              "The prior tool aggregated absolute contact-normal magnitudes and associated shank contacts with the leg. That is not identical to world-frame foot Fz. This campaign transforms the signed contact wrench to world coordinates and separates non-foot contact. The old default PD=180/3.5 also exceeds this campaign's approved gain range; its reported nominal result is not comparable to a 60/0.7 or 100/2.5 bounded maneuver.","",
              "The supplied claims about 72 joint-scale and 180 thigh/knee trials are historical context, not freshly reconstructed trace evidence. The present trials support inadequate load transfer in the tested small-displacement family; they do not prove the cause of every historical physical failure or impossibility for every trajectory.","",
              "All source inertials, local COM positions, joint ranges, actuator declarations, runtime solver settings, unknowns, parameter distributions and acceptance thresholds are exported beside the traces; see the standalone tool README for interpretation. Payload components are not explicitly modeled in the source and real values remain unknown.","", "## Controlled one-factor diagnostics", "", "Each row changes only the named factor from nominal candidate A. This separates effects that random joint-angle sweeps mix together.","", "| Factor | Minimum pre-lift FR fraction | Tracking (rad) | Safety pass |","|---|---:|---:|---:|"]
    for r in ablations:lines.append(f"| {r['name'].removeprefix('factor_')} | {100*r['min_fr_fraction']:.2f}% | {r['max_tracking_rad']:.4f} | {bool(r['safe'])} |")
    lines += ["", "Native contact has no meaningful foot-load fraction when shanks carry weight; its foot-only fraction (including the 100% sentinel when total foot force <=1 N) must not be interpreted as whole-robot load distribution. Compare valid sphere-contact rows for force effects. These interventions are causal within this model only. Actual robot friction, payload and actuator behavior remain unidentified.","", "## Exact diagnostic trajectories", "", "Every candidate uses 3 s settle, 4 s quintic body shift, 1 s unload verification, 4 s quintic recenter, 1 s final stand. Nominal PD=60/0.7 throughout simulation initialization and motion. No candidate qualifies for lift or hardware execution. A failed unload request cannot generate a lift target."]
    for r in rows:
        lines += ["",f"Candidate {r['candidate']} targets (FL, FR, HL, HR; hip/thigh/knee; rad):", "", "```json",json.dumps(np.asarray(r["endpoint_q_targets"]).reshape(4,3).tolist()),"```",f"Nominal mean FR force in verify hold: {r['mean_fr_force_during_hold_n']:.3f} N. Actual joint displacement from nominal stand (including PD sag) reaches {r['nominal_max_actual_joint_delta_rad']:.5f} rad; the 0.03 limit here is commanded target displacement, not a claim that loaded joints remain within 0.03 rad."]
    lines += ["", "## Future 25/50/75% model-validation plan — not authorized to execute", "",
              "Keep the planned small supervised body-only experiment. First resolve the contact model and weigh/locate the computer, D455, lidar, mounts and cables. With force channels historically zero, obtain independently calibrated load measurements for all four feet (and quantify any harness/support load); video alone cannot validate unloading. Confirm timing, joint measurements and PD tracking. Review the exact test and its current physical guards separately.","",
              "After a robust trajectory is demonstrated, generate 25%, 50%, and 75% of its Cartesian body displacement using fresh IK at every sample. Never scale q deltas and assume Cartesian scaling. Preflight each complete trace against unchanged limits. For candidate A's diagnostic reference only these are (-1.5,+1.5), (-3,+3), (-4.5,+4.5) mm; A is not a robust or approved hardware trajectory. Use one explicitly approved supported body-only trial at a time, with existing one-use permit, no automatic retry, operator stop, guarded recenter and release. No FR lift.","",
              "Record timestamped target/actual q,dq, gains, attitude, telemetry age, support forces, body/foot position, permit/send/release states, and support loading. Compare measured force redistribution and COM-related geometry to the simulated intervals before considering any foot lift. Abort on the existing 0.50 rad/s, 3 degree, 0.15 rad tracking, freshness/permit/stop guards and approved command limits. On an unsafe abort, follow the existing reviewed release procedure rather than commanding an unguarded recenter.","", "## Artifacts and reproducibility", "",
              "Run commands: `tools/robust_fr_sim/README.md`. Full results, parameter inputs, 100 Hz traces, model audit, exact targets, plots and per-trial JSON are local under `artifacts/robust_fr_campaign/`. `all_results.csv` contains the campaign trials; `factor_results.json` contains the additional one-factor trials. Source hashes and dirty Git status are retained in the audit. Generated bulk artifacts are ignored; this report and tool source are suitable for review without mixing the existing physical-control work.","",
              "Verification: standalone CMake build/CTest and six offline integration regressions passed; existing offline build and 17/17 CTest tests passed. The payload regression verifies that moving payload forward versus rearward changes load distribution; runtime checks also verify actual inertial COM placement, including invalidation of MuJoCo's compiled same-frame shortcut. Earlier development runs that lacked that invalidation were superseded, not used for final robustness counts. No physical executable was launched. `git diff --check` is checked at handoff.","", "Next step: review this failure boundary and calibrate the contact/payload/actuator model. No trajectory from this campaign is READY_FOR_HARDWARE. No physical safety limit should be increased on the basis of these simulations.",""]
    (ROOT/"docs/FR_ROBUST_SIMULATION_2026-09-21.md").write_text("\n".join(lines))
    dump(OUT/"review_summary.json",{"candidates":rows,"factor_results":ablations})
    # Compact evidence can travel with source; bulk 100 Hz traces stay local.
    evidence={"audit_at_campaign_start":load("model_audit.json"),
              "runtime_settings":load("baseline_sphere_settings.json"),
              "summary":summary,"comparison":rows,"robustness":robust,
              "nominal_trials":load("shift_results.json"),"factor_trials":ablations,
              "binary_sha256":hashlib.sha256((ROOT/"build-robust-fr/robust_fr_sim").read_bytes()).hexdigest(),
              "engine_sha256":hashlib.sha256((ROOT/"third_party/mujoco/x86/lib/libmujoco.so.2.3.7").read_bytes()).hexdigest(),
              "final_tool_source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob("*") if p.is_file()},
              "trace_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob("*.csv")},
              "mesh_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"third_party/deep_robotics_model/Lite3/Lite3_mjcf/meshes").glob("*.STL")}}
    dump(ROOT/"docs/FR_ROBUST_SIMULATION_2026-09-21.json",evidence)


if __name__=="__main__":main()
