# Supported leg-lift offline handoff — 2026-09-18

STATUS: EVIDENCE_INCOMPLETE

## Goal and changes

Prepare one mechanically supported, one-use front-right leg-lift sequence without
executing it. The milestone adds a bounded 5 mm body shift, 2 mm Cartesian FR
lift, 0.25 s hold, lowering, recentering, and automatic release. Changed files:

- `CMakeLists.txt`
- `docs/HANDOFF_SUPPORTED_LEG_LIFT_2026-09-18.md`
- `docs/NEXT_SUPPORTED_LEG_LIFT_TEST.md`
- `docs/SUPPORTED_STAND_AUTO_RELEASE_RESULT_2026-09-17.md`
- `interface/robot/hardware/hardware_interface.hpp`
- `interface/robot/robot_interface.h`
- `state_machine/standup_state.hpp`
- `state_machine/state_machine.hpp`
- `state_machine/supported_leg_lift_plan.hpp`
- `tests/supported_leg_lift_once_test.cpp`
- `tests/supported_leg_lift_plan_test.cpp`
- `tools/lite3_validation_console.cpp`

## Validation

- `cmake --build build-handoff -j2` -> PASS, exit 0, 100% built.
- `ctest --test-dir build-handoff -R '^(supported_leg_lift_plan_test|supported_leg_lift_once_test)$' --output-on-failure`
  -> PASS, 2/2 tests, 0 failures.
- `git diff --check` -> PASS before this handoff note; rerun before commit.

## Safety and evidence limits

The action requires a distinct exact token, a fresh one-use acquisition epoch,
mechanical support, E-stop readiness, valid stationary telemetry, zero software
velocity, and an existing supervised stand permit. State-machine and final-send
guards enforce 3 degree roll/pitch, 0.15 rad tracking error, 0.03 rad target
displacement, 0.10 rad/s target velocity, bounded gains (`kp <= 60`, `kd <=
0.7`), zero feed-forward torque, measured-speed and absolute-time limits,
automatic lowering/recentering, gate closure, and release. Stop, shutdown,
signal, stale telemetry, invalid state, permit expiry, or a limit violation
fails closed. RL, general velocity, Nav2, and raw-torque paths are not used.

No hardware-facing process ran for this milestone. No control ownership was
requested, transmit remained off, and no stand or leg-lift action was executed.

Physical behavior remains unproven. Live Lite3 contact-force feedback previously
reported zero for all four legs, so this action cannot confirm unloading,
touchdown, or weight transfer. Balance, clearance, hardware joint response,
support loading, automatic release behavior, and repeatability therefore remain
unresolved. The offline result must not be treated as hardware evidence.

NEXT SAFE ACTION: review this commit and the exact preflight in
`docs/NEXT_SUPPORTED_LEG_LIFT_TEST.md`. Do not execute until the robot is
mechanically supported and the user separately approves that exact supervised
run.
