# Offline FR load-transfer campaign

This standalone program links **only Eigen and bundled MuJoCo 2.3.7**. It does
not include the state machine, SDK, transport, ownership, or physical experiment
path. Existing dirty physical-control files are not inputs. No change here
authorizes hardware or changes its thresholds.

Build/run from the repository root:

```sh
cmake -S tools/robust_fr_sim -B build-robust-fr -DCMAKE_BUILD_TYPE=Release
cmake --build build-robust-fr -j2
ctest --test-dir build-robust-fr --output-on-failure
python3 tools/robust_fr_sim/campaign.py --trials 100 --workers 4
python3 tools/robust_fr_sim/test_campaign.py
python3 tools/robust_fr_sim/report.py
```

Python campaign orchestration uses the standard library; plots use the existing
NumPy and Matplotlib installations. No new package downloads are required.
Results are local, ignored files in `artifacts/robust_fr_campaign/`. Each run has
input JSON, metric JSON, a 100 Hz trace CSV, and source model inertial table.
The criteria and dynamics are evaluated at 1 kHz, not just at logged samples.
`model_audit.json` records original MJCF inertials, joint limits, defaults,
actuators, source hashes, HEAD and dirty status. `scenarios.json` records all
randomized parameters; all candidates use the same 100 scenarios, seed 20260921.

## Known model and uncertainties

The vendor MJCF is a source model, not measured identification of this robot.
Its torso is 5.6056 kg. Each leg has 0.550 kg hip, 0.860 kg thigh, 0.153 kg shank,
and 0.020 kg foot (total 11.9376 kg). All link COM positions and inertias are
exported without rounding to conceptual symmetry. Foot rotational inertias are
zero in the source. Computer, D455, S2, mounts and cables have no separate bodies;
whether any were folded into the torso mass is unknown. Their physical masses,
poses and inertia need measurement.

Joint ranges are hip [-0.523,0.523], thigh [-2.67,0.314], knee [0.524,2.792] rad.
The ideal gear-1 motors have +/-30 torque control bounds. There is no identified
torque-speed curve, thermal model, backlash or electrical delay. Source joint
damping/friction are unspecified (MuJoCo defaults are zero). Foot collision
friction is [1,0.01,0.01], condim=3, solref=[0.005,1]; ground defaults and contact
mixing also participate. Runtime friction perturbations change both ground and
robot sliding friction. Contact solref time constants are scaled for both.
The code preserves the source solver configuration and changes dt to 0.001 s.
Compiled settings are Newton solver, 100 iterations, tolerance 1e-8,
semi-implicit Euler, pyramidal friction cone; source dt=0.002 s. The floor
solref is [0.02,1] and foot solimp is [0.9,0.95,0.001,0.5,2]. Per-trial
`*_settings.json` records these rather than inferring every default from XML.

Native shank meshes overlap the ground near the foot spheres. The native-model
baseline is always run. The alternative `sphere-only=1` disables **only** shank
collision in a private model; it is an explicit, unvalidated foot-contact
hypothesis, not a repair declared faithful to hardware. Non-foot ground force
>=1 N fails this campaign. Native and sphere-only results must be distinguished.

The randomized range is a sensitivity hypothesis, **not a measured uncertainty
distribution**: total/link scale 0.9–1.1, independent non-torso link scales
0.95–1.05, added payload 0–1.5 kg at x +/-0.08 m, y +/-0.06 m, z 0.05–0.18 m;
friction 0.35–1.0; actuator scale 0.85–1.0; kp/kd scales 0.9–1.1 around each
candidate, clipped to kp [60,100], kd [0.7,2.5] (one-sided at bounds); joint damping
0–0.15 and Coulomb friction 0–0.1; alternating initial q error +/-0.01 rad,
initial roll/pitch +/-0.01 rad; position-feedback delay 0/1/2/4 ms; contact time
constant scale 0.75–1.5. Velocity feedback has no added delay. 20/100 scenarios
use native collision and 80/100 sphere-only. Added payload is a point mass;
COM and inertia are combined using the parallel-axis theorem and principal-axis
decomposition. Actual payload rotational inertia is unknown. Independent link
scaling preserves each link COM and scales its inertia with mass.
The compiled torso `body_sameframe` optimization is invalidated when the payload
is changed. A runtime assertion compares the realized inertial COM to the
requested transformed COM; an integration regression verifies that forward vs
rearward payload changes the settled foot-load distribution.

## Motion and criteria

STAND/SETTLE 3 s -> Cartesian quintic SHIFT (2 or 4 s) -> VERIFY_UNLOAD 1 s
-> optional LIFT 2 s -> HOLD 0.5 s -> LOWER 2 s -> RECENTER (shift duration)
-> FINAL 1 s. Every Cartesian sample is solved by IK; no scaling of joint
deltas is used. FK is checked against MuJoCo at initialization. Traces contain
all four numerical Jacobians and FR body-frame FK, actual/target q, velocities,
accelerations, limit distance, COM, contacts, forces and attitude.

Nominal stand q=[0,-0.7729795255029084,1.5005003509817765] rad per leg. Simulation
PD comparisons are 100/2.5 (supported stand / offline body-shift review choice)
and 60/0.7 (earlier reduced pair). No 180/3.5 gains. Constant gains are applied
from simulation initialization; this is **not** a test of physical gain-switch
transients. The physical final-send path currently has unresolved gain/limit
differences and is not changed by this campaign.

Hard acceptance criteria:

* Command displacement from stand <=0.03 rad; command speed <=0.10 rad/s.
* Measured joint speed <=0.50 rad/s; tracking error <=0.15 rad.
* Absolute roll and pitch <=3 degrees; joint limit distance >0.01 rad.
* Actual loaded-contact polygon margin >=0; non-foot ground force <1 N.
* Friction utilization <=1.05 (5% numerical diagnostic tolerance, not a hardware
  friction approval); utilization uses full contact-frame tangential force and
  the actual contact friction, and world vertical forces are signed correctly.
* UNLOAD: FR <=5% of summed foot Fz, FL/HL/HR each >=2 N, FR surface within
  +/-2 mm of the ground, CoM at least 1 mm inside FL/HL/HR triangle, all gates
  valid continuously for the **last 0.5 s before lift**.
* LIFT: unload prerequisite plus FR surface >=3 mm above ground and FR Fz <1 N,
  the three other feet each >=2 N, triangle margin >=1 mm and other gates valid
  throughout the 0.5 s hold (0.49 s tolerance for discrete endpoint timing).
* Any evaluated safety failure permanently invalidates the trial. A missing
  unload gate suppresses lift targets, even if lift was requested.

The first 2.5 s are free-standing **simulation initialization**, not an approved
hardware acquisition/stand procedure. Full traces retain that transient, but
success metrics cover the last 0.5 s of settle and the maneuver. No active
mechanical support is modeled. Continuing a failed simulation records a
diagnostic counterfactual, not physical abort/release behavior.

Ranking (lower better) uses 100*minimum FR fraction + 1000*triangle-margin deficit
below 1 mm + 10*(peak |roll|+|pitch|+tracking) + peak dq + 0.1*target acceleration
+ 0.001*force slew + 100*friction excess above 1 + 10*joint-limit deficit below
0.05 rad - 100*lift clearance + 10000 each for safety/envelope failure. Units
are SI. Hard gates determine PASS; ranking never overrides them. Acceleration
and force slew are recorded/penalized without inventing physical approved limits.

## Progressive search and interpretation

Stage 1 tests native and explicit sphere-only static stand. Stage 2 searches
80 combinations of x={-6,-4,-2,0,+2} mm, y={0,2,4,6} mm, duration={2,4} s,
gain pair={100/2.5,60/0.7}. Out-of-envelope commands are rejected, not clamped.
Three spatially distinct, safe candidates receive 100 paired domain trials.
If nominal unloading fails, these trials are **failure diagnostics**, not a
validated robust lift. Lift search is gated on nominal unloading. No lift
success may be claimed from body-only trials or a high foot-Z sample.

The small search envelope follows the existing 0.03 rad restriction. Failure
does not prove all imaginable trajectories fail; it can establish that this
tested family, gains, and envelope fail. No larger motion is silently authorized.
Robustness fractions are conditional on the stated synthetic distribution;
they are not estimates of real-robot success probability.
