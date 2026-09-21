# FR simulation campaign — 2026-09-21

Status: **NO ROBUST UNLOAD OR LIFT DEMONSTRATED**. Offline evidence only.

The standalone simulator uses unchanged acceptance limits (0.03 rad target delta, 0.10 rad/s commanded speed, 0.50 rad/s measured speed, 0.15 rad tracking, 3 degree attitude). The existing physical-control files and their pre-existing dirty changes were not edited. No hardware commands were sent.

## Actual results

80 nominal body-only candidates; 0 unload passes. Three distinct best candidates each received 100 paired model variations. No lift search was started because the prerequisite failed. The reported robustness counts below are **unload** counts; lift success is **not evaluated**, not inferred.

| Candidate | Body x / y (mm) | Nominal FR fraction | Unload | All safety gates | Sphere-only safety | Native safety |
|---|---:|---:|---:|---:|---:|---:|
| A | -6 / 6 | 18.61% | 0/100 | 75/100 | 75/80 | 0/20 |
| B | -6 / 4 | 18.89% | 0/100 | 75/100 | 75/80 | 0/20 |
| C | -4 / 6 | 19.07% | 0/100 | 78/100 | 78/80 | 0/20 |

A safety pass does not include successful unloading. Passing rates apply only to the declared synthetic parameter distribution, not to real hardware.

| Candidate | Sphere FR fraction range | Worst roll / pitch (deg) | Worst tracking (rad) | Worst dq (rad/s) | Max target delta (rad) | Min sphere triangle margin (mm) |
|---|---:|---:|---:|---:|---:|---:|
| A | 14.32–21.06% | 0.555 / 4.338 | 0.1661 | 0.0414 | 0.02760 | 21.594 |
| B | 14.62–21.34% | 0.521 / 4.329 | 0.1637 | 0.0414 | 0.02509 | 20.136 |
| C | 15.13–21.49% | 0.567 / 3.862 | 0.1595 | 0.0414 | 0.02086 | 19.287 |

The triangle margin is geometric; it cannot by itself establish unloading. A four-contact spring-supported pose can have its CoM inside the three-foot triangle while FR still carries substantial load.

## Model audit and explanation

Source mass is 11.9376 kg; expected weight is 117.108 N. Sphere-only standing foot sum is 117.108 N; individual FL/FR/HL/HR Fz are 26.282, 26.177, 32.334, 32.315 N. Native-model foot sum is 0.729 N because the shank meshes bear most of the weight. This contact-model ambiguity must be resolved before transfer claims.

The prior tool aggregated absolute contact-normal magnitudes and associated shank contacts with the leg. That is not identical to world-frame foot Fz. This campaign transforms the signed contact wrench to world coordinates and separates non-foot contact. The old default PD=180/3.5 also exceeds this campaign's approved gain range; its reported nominal result is not comparable to a 60/0.7 or 100/2.5 bounded maneuver.

The supplied claims about 72 joint-scale and 180 thigh/knee trials are historical context, not freshly reconstructed trace evidence. The present trials support inadequate load transfer in the tested small-displacement family; they do not prove the cause of every historical physical failure or impossibility for every trajectory.

All source inertials, local COM positions, joint ranges, actuator declarations, runtime solver settings, unknowns, parameter distributions and acceptance thresholds are exported beside the traces; see the standalone tool README for interpretation. Payload components are not explicitly modeled in the source and real values remain unknown.

## Controlled one-factor diagnostics

Each row changes only the named factor from nominal candidate A. This separates effects that random joint-angle sweeps mix together.

| Factor | Minimum pre-lift FR fraction | Tracking (rad) | Safety pass |
|---|---:|---:|---:|
| reference | 18.61% | 0.0987 | True |
| no_y | 19.45% | 0.0944 | True |
| no_x | 19.96% | 0.0910 | True |
| stand_gains | 20.49% | 0.0519 | True |
| friction_low | 18.72% | 0.0982 | True |
| friction_high | 18.61% | 0.0987 | True |
| payload_forward | 19.75% | 0.1080 | True |
| payload_rearward | 15.53% | 0.1296 | False |
| payload_right | 18.93% | 0.1135 | True |
| payload_left | 16.48% | 0.1231 | True |
| mass_light | 19.20% | 0.0854 | True |
| mass_heavy | 17.89% | 0.1138 | True |
| weak_motor | 17.20% | 0.1269 | True |
| delay_4ms | 18.61% | 0.0987 | True |
| native_contact | 0.00% | 0.0965 | False |
| contact_soft | 18.44% | 0.0997 | True |
| contact_stiff | 18.70% | 0.0983 | True |

Native contact has no meaningful foot-load fraction when shanks carry weight; its foot-only fraction (including the 100% sentinel when total foot force <=1 N) must not be interpreted as whole-robot load distribution. Compare valid sphere-contact rows for force effects. These interventions are causal within this model only. Actual robot friction, payload and actuator behavior remain unidentified.

## Exact diagnostic trajectories

Every candidate uses 3 s settle, 4 s quintic body shift, 1 s unload verification, 4 s quintic recenter, 1 s final stand. Nominal PD=60/0.7 throughout simulation initialization and motion. No candidate qualifies for lift or hardware execution. A failed unload request cannot generate a lift target.

Candidate A targets (FL, FR, HL, HR; hip/thigh/knee; rad):

```json
[[0.02005645195, -0.7596914914, 1.513558048], [0.01992682801, -0.7453774936, 1.485688389], [0.02005645195, -0.7596914914, 1.513558048], [0.01992682801, -0.7453774936, 1.485688389]]
```
Nominal mean FR force in verify hold: 21.806 N. Actual joint displacement from nominal stand (including PD sag) reaches 0.11174 rad; the 0.03 limit here is commanded target displacement, not a claim that loaded joints remain within 0.03 rad.

Candidate B targets (FL, FR, HL, HR; hip/thigh/knee; rad):

```json
[[0.0133573677, -0.7574298089, 1.50915517], [0.01329974305, -0.7478874764, 1.490576101], [0.0133573677, -0.7574298089, 1.50915517], [0.01329974305, -0.7478874764, 1.490576101]]
```
Nominal mean FR force in verify hold: 22.134 N. Actual joint displacement from nominal stand (including PD sag) reaches 0.11054 rad; the 0.03 limit here is commanded target displacement, not a claim that loaded joints remain within 0.03 rad.

Candidate C targets (FL, FR, HL, HR; hip/thigh/knee; rad):

```json
[[0.02005639845, -0.7665231848, 1.513800163], [0.01992677521, -0.7521229949, 1.485931059], [0.02005639845, -0.7665231848, 1.513800163], [0.01992677521, -0.7521229949, 1.485931059]]
```
Nominal mean FR force in verify hold: 22.339 N. Actual joint displacement from nominal stand (including PD sag) reaches 0.11054 rad; the 0.03 limit here is commanded target displacement, not a claim that loaded joints remain within 0.03 rad.

## Future 25/50/75% model-validation plan — not authorized to execute

Keep the planned small supervised body-only experiment. First resolve the contact model and weigh/locate the computer, D455, lidar, mounts and cables. With force channels historically zero, obtain independently calibrated load measurements for all four feet (and quantify any harness/support load); video alone cannot validate unloading. Confirm timing, joint measurements and PD tracking. Review the exact test and its current physical guards separately.

After a robust trajectory is demonstrated, generate 25%, 50%, and 75% of its Cartesian body displacement using fresh IK at every sample. Never scale q deltas and assume Cartesian scaling. Preflight each complete trace against unchanged limits. For candidate A's diagnostic reference only these are (-1.5,+1.5), (-3,+3), (-4.5,+4.5) mm; A is not a robust or approved hardware trajectory. Use one explicitly approved supported body-only trial at a time, with existing one-use permit, no automatic retry, operator stop, guarded recenter and release. No FR lift.

Record timestamped target/actual q,dq, gains, attitude, telemetry age, support forces, body/foot position, permit/send/release states, and support loading. Compare measured force redistribution and COM-related geometry to the simulated intervals before considering any foot lift. Abort on the existing 0.50 rad/s, 3 degree, 0.15 rad tracking, freshness/permit/stop guards and approved command limits. On an unsafe abort, follow the existing reviewed release procedure rather than commanding an unguarded recenter.

## Artifacts and reproducibility

Run commands: `tools/robust_fr_sim/README.md`. Full results, parameter inputs, 100 Hz traces, model audit, exact targets, plots and per-trial JSON are local under `artifacts/robust_fr_campaign/`. `all_results.csv` contains the campaign trials; `factor_results.json` contains the additional one-factor trials. Source hashes and dirty Git status are retained in the audit. Generated bulk artifacts are ignored; this report and tool source are suitable for review without mixing the existing physical-control work.

Verification: standalone CMake build/CTest and six offline integration regressions passed; existing offline build and 17/17 CTest tests passed. The payload regression verifies that moving payload forward versus rearward changes load distribution; runtime checks also verify actual inertial COM placement, including invalidation of MuJoCo's compiled same-frame shortcut. Earlier development runs that lacked that invalidation were superseded, not used for final robustness counts. No physical executable was launched. `git diff --check` is checked at handoff.

Next step: review this failure boundary and calibrate the contact/payload/actuator model. No trajectory from this campaign is READY_FOR_HARDWARE. No physical safety limit should be increased on the basis of these simulations.
