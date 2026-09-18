# Body-shift offline review — 2026-09-18

## Scope and safety gate

This review prepares only the prerequisite, mechanically supported body-shift.
It does not authorize unloading, foot lift, RL, gait velocity, ownership, or
hardware execution. Front-right lift remains blocked until a separately reviewed
body-shift hardware result exists.

## Compared command strategies

The offline `SupportedBodyShiftPlan` samples the existing 5 mm rearward/leftward
body shift (all feet remain at their requested ground height), 0.5 s hold, and
2 s recenter at 1 kHz.

| Strategy | Gains during shift | Offline max target delta | Offline max target speed |
| --- | --- | ---: | ---: |
| A: abrupt reduced | kp=60, kd=0.7 immediately | 0.0229582 rad | 0.0215233 rad/s |
| B: keep stand gains | kp=100, kd=2.5 | 0.0229582 rad | 0.0215233 rad/s |
| C: smooth reduced | quintic 100/2.5 to 60/0.7 over 0.5 s | 0.0229582 rad | 0.0215233 rad/s |

All samples have finite values, zero feed-forward torque, target delta below
0.03 rad, and commanded speed below 0.10 rad/s. These are command-construction
results only. The planner cannot predict measured joint speed, oscillation,
settling, tracking error, or hardware guard triggers.

## Selection

Select **B: keep stand gains** for the next implementation/review. The failed
hardware body-shift began immediately after the discontinuous 100/2.5 to
60/0.7 transition, while commanded motion was nearly stationary. Keeping the
already-proven stand gains removes that discontinuity without relaxing any
limit. This is engineering inference, not proof of the physical cause.

## Evidence separation

- Hardware: supported stand succeeded; the one body-shift attempt aborted on a
  real FL-knee measured-speed sample of 0.514640808 rad/s; no retry occurred.
- Replay: trace analysis supports a real short oscillatory excursion and a
  correlation with the gain transition; it cannot establish causality.
- Simulation: the existing one-leg simulation is not evidence for body-shift
  hardware safety.
- Offline plan: verifies IK-derived targets and command limits only.

## Next offline work

Integrate the selected body-only plan behind a new one-use explicit action and
its own diagnostics, preserving final-send revalidation, gate closure, and
release. Do not expose a leg-lift command through that action.
