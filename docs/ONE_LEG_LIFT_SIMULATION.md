# Lite3 one-leg lift simulation milestone

## Isolation and safety

- Branch: `low-level-leg-control`
- Worktree: `/home/abx/Desktop/robotdog_ws/low-level-leg-control`
- Base commit: `ac563282da0d42c93c88d2889a6893b5efe98486`
- Robot model submodule: `third_party/deep_robotics_model` at `b452a1f404d37155400242f18e454fed8bcc51b8`
- Host: Linux Mint 22.1 Xia, Ubuntu Noble package base
- Simulator: Ubuntu MuJoCo 2.2.2, extracted under `/home/abx/Desktop/robotdog_ws/.deps`; no system package was installed

The new executable contains no socket, MotionSDK sender, ROS publisher, or hardware transport. It loads a local MJCF and writes local CSV/JSON files. It cannot transmit to the robot. Feed-forward torque is always zero. The MuJoCo motor actuator receives only the bounded result of the simulated position/PD law.

## Model and joint mapping

The SDK and MJCF order agree: FL, FR, HL, HR; each leg is HipX, HipY, Knee. “Positive direction” below is the axis attached to a positive SDK/MJCF joint angle. Limits are the MJCF limits, which are tighter than some controller-side safety values.

| Leg | Joint | SDK index | Positive model axis | Limits (rad) |
|---|---|---:|---|---:|
| FL | hip ab/ad (HipX) | 0 | body −X | −0.523 to +0.523 |
| FL | hip flex/ext (HipY) | 1 | local −Y | −2.670 to +0.314 |
| FL | knee | 2 | local −Y | +0.524 to +2.792 |
| FR | hip ab/ad (HipX) | 3 | body −X | −0.523 to +0.523 |
| FR | hip flex/ext (HipY) | 4 | local −Y | −2.670 to +0.314 |
| FR | knee | 5 | local −Y | +0.524 to +2.792 |
| HL | hip ab/ad (HipX) | 6 | body −X | −0.523 to +0.523 |
| HL | hip flex/ext (HipY) | 7 | local −Y | −2.670 to +0.314 |
| HL | knee | 8 | local −Y | +0.524 to +2.792 |
| HR | hip ab/ad (HipX) | 9 | body −X | −0.523 to +0.523 |
| HR | hip flex/ext (HipY) | 10 | local −Y | −2.670 to +0.314 |
| HR | knee | 11 | local −Y | +0.524 to +2.792 |

The 0.30 m controller stand-height geometry gives the same joint target on each leg:

```text
HipX =  0.000000000 rad   (  0.0000 deg)
HipY = -0.772979526 rad   (-44.2885 deg)
Knee =  1.500500351 rad   ( 85.9723 deg)
```

This differs slightly from MotionSDK's simpler `StandUp()` example (`0°, -42°, 78°`). The simulation uses the research controller's 0.30 m geometry and the pinned MJCF link lengths.

## Kinematics and control

The selected leg is **front-right (FR), SDK indices 3–5**.

`tools/lite3_leg_kinematics.hpp` implements the exact MJCF transform chain: body-to-hip origin, HipX rotation about −X, signed lateral hip offset, HipY rotation about −Y, 0.20 m thigh, knee rotation about −Y, and 0.21012 m shank. Cartesian IK uses damped least squares, the exact FK Jacobian, a nearby bent-knee seed, and the MJCF joint limits.

The FK result was compared with all four foot-body positions computed by MuJoCo. Maximum disagreement was `1.01e-16 m`. The largest IK endpoint residual in either dynamic run was below `1.0e-7 m`.

Weight shift is produced by keeping the feet fixed in the world while moving every foot target relative to the body by `(+0.060, -0.060, 0) m`. This requests a body/COM shift of `(-0.060, +0.060, 0) m`, rearward and left, away from FR. A 6 mm coordinated leg-extension term compensates simulated PD spring sag. A bounded correction of 0.15 m/rad changes stance-foot heights to regulate roll and pitch. The measured COM projection is checked against the FL-HL-HR support triangle at every step.

The foot command is a quintic Cartesian trajectory. A 15 mm IK target includes contact-compliance compensation and produces 6.43 mm measured world-frame clearance. PD is `kp=180`, `kd=3.5`, desired velocity zero, feed-forward torque zero, and simulated actuator torque clamped to ±30 Nm. Peak observed PD torque was 9.44 Nm. These simulation gains and compliance compensation are **not approved hardware settings**.

The pinned MJCF's `shank.STL` extends 0.50 mm below the dedicated foot sphere, causing two ground contacts per leg and masking small lifts. The harness leaves the source MJCF unchanged but disables shank-floor collision at runtime and uses the four explicit `*_FOOT_collision` spheres. Results therefore depend on this documented simulation-only contact normalization.

## State machine

All transitions use quintic interpolation. A state duration is also its timeout. Global aborts are: IK failure, roll or pitch over 12°, torso height outside 0.22–0.40 m, COM more than 10 mm outside the three-foot support triangle, or failure of the final acceptance checks.

| State | Entry condition | Command | Completion / timeout | State-specific abort evidence |
|---|---|---|---|---|
| STAND | simulation initialized | hold 0.30 m standing angles | 2.0 s | global checks |
| SHIFT_WEIGHT | stand interval complete | shift body 60 mm rear and 60 mm left; apply height/attitude correction | 2.0 s | global checks |
| LIFT_LEG | shifted endpoint reached | raise FR Cartesian target with quintic interpolation | 1.5 s | support margin check |
| HOLD_LEG | lift endpoint reached | hold FR target fixed | 1.0 s | FR must be unloaded in at least 95% of samples |
| MOVE_LEG_FORWARD | hold complete | optional 0–10 mm FR +X trajectory | 1.0 s | global checks |
| RETURN_LEG | forward endpoint reached | return FR X to its lift point | 1.0 s | global checks |
| LOWER_LEG | return complete | lower FR with quintic interpolation | 1.5 s | global checks |
| VERIFY_CONTACT | lower endpoint reached | hold shifted four-foot pose | 0.75 s | contact restoration is checked |
| STAND | contact verification complete | recenter body with quintic interpolation | 2.0 s | all four contacts must exist in at least 95% of post-lowering samples |

The simulation-only loaded threshold is 2 N. No real-robot threshold is defined or implied.

## Results

Two deterministic headless runs completed without abort:

| Measurement | Vertical lift | Lift + 5 mm forward |
|---|---:|---:|
| Measured FR clearance | 6.4315 mm | 6.4315 mm |
| Max absolute roll during lift | 0.3575° | 0.3575° |
| Max absolute pitch during lift | 0.6556° | 0.6556° |
| Minimum COM support margin | 92.953 mm | 92.953 mm |
| FR unloaded during 1 s hold | 100% | 100% |
| All three stance feet loaded | 100% of lift interval | 100% of lift interval |
| Four contacts restored after lowering | 100% | 100% |
| Torso-origin height range | 0.31638–0.32208 m | 0.31638–0.32208 m |
| Peak bounded PD torque | 9.4341 Nm | 9.4341 Nm |
| Result | PASS | PASS |

Mean forces during the one-second vertical hold were FL 33.54 N, FR 0.00 N, HL 45.62 N, and HR 37.95 N. The front-right foot remained clear and unloaded for the complete hold. During the first part of `LIFT_LEG` and final part of `LOWER_LEG`, FR force changes continuously through the contact transition, as expected.

Generated local evidence is under `artifacts/one_leg_lift/vertical` and `artifacts/one_leg_lift/forward_5mm`. It is ignored by Git to prevent generated traces from entering the branch.

## Reproduction

From this worktree:

```bash
g++ -std=c++17 -O1 tests/leg_kinematics_test.cpp -I. -Ithird_party/eigen \
  -o /tmp/lite3_leg_kinematics_test
/tmp/lite3_leg_kinematics_test

tools/run_one_leg_lift_sim.sh \
  --output-dir artifacts/one_leg_lift/vertical

tools/run_one_leg_lift_sim.sh --forward-mm 5 \
  --output-dir artifacts/one_leg_lift/forward_5mm
```

The runner resolves the workspace-local MuJoCo extraction. `MUJOCO_COMPAT_ROOT` can point to another extracted `usr` directory if the worktree is moved.

## Hardware gate

No physical test was run or enabled. The simulation proves the kinematic and quasi-static primitive, not hardware readiness. Before sending any low-level packet, verify the real joint signs in passive telemetry, validate real foot-force channels and thresholds, and determine whether the vendor controller accepts the same 12-joint PD semantics while standing.

The recommended first explicitly approved hardware experiment is one supported attempt only: stable stand, 10 mm rear-left body target over 3 s, return to stand, and stop. Keep the robot mechanically supported, clear the area, hold the emergency stop, use position mode with feed-forward torque exactly zero, `kp <= 60`, `kd <= 0.7`, target velocity no more than 0.10 rad/s, per-joint target change no more than 0.03 rad, roll/pitch abort at 3°, joint tracking abort at 0.15 rad, and a 5 s state timeout. Do not lift a foot in that first hardware attempt. A later separately approved supported test may add at most 2 mm of FR Cartesian target and a 0.25 s hold after real contact unloading and return behavior are demonstrated.

Neither hardware experiment is authorized by this document.
