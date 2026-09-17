# Next physical test: supported stand automatic release

## Purpose and scope

Validate one behavior only: after an explicitly authorized, mechanically
supported `stand_once` reaches `TARGET_REACHED`, the state machine must hold the
target for no more than two seconds, close the joint-send gate, request SDK
release once, and return to passive idle.

This test does not authorize or exercise RL, velocity control, body shifting,
leg lifting, walking, lidar, Nav2, raw torque, or repeated attempts.

No hardware command was run while preparing this plan.

## Software under review

- Branch: `handoff/low-level-leg-control-2026-09-17`
- Safety implementation commit before this plan: `193cbc999fd555c324534dafdba6104fbd069f07`
- Build directory: `build-handoff`
- Executable: `build-handoff/lite3_validation_console`
- Executable SHA-256:
  `32d1a307def8eec63b185ae653947516cc32d186e395a9d6218e401ddb5b420a`
- Build options: x86 hardware adapter, simulation off, remote input off,
  testing on

The stand target, trajectory, gains and SDK mapping are unchanged. Each leg's
final joint target is approximately `[0, -0.7729795, 1.5005003]` rad. Position
PD uses `kp=100`, `kd=2.5`, target velocity zero at final hold, and zero
feed-forward torque.

## Offline evidence

From the branch above:

```text
cmake --build build-handoff -j2
  PASS

ctest --test-dir build-handoff --output-on-failure -j2
  PASS: 13/13, 0 failed

g++ -std=c++17 -O1 tests/leg_kinematics_test.cpp -I. -Ithird_party/eigen \
  -o /tmp/lite3_next_test_leg_kinematics
/tmp/lite3_next_test_leg_kinematics
  PASS: Lite3 FK/IK checks passed

one_leg_lift_sim, vertical
  PASS

one_leg_lift_sim, 5 mm forward
  PASS
```

The simulation runs are supporting regression evidence only. They do not prove
hardware release behavior.

## Physical prerequisites

Before launching the console, the operator must confirm all of the following:

1. A mechanical support prevents a fall or collapse before, during and after
   SDK release. It must not depend on a person catching the robot.
2. The original emergency stop is working and held by the operator.
3. The area and every leg's workspace are clear.
4. Battery and robot health are acceptable.
5. The robot is in a normal folded/resting posture and physically stable.
6. No other controller or console is active.
7. The exact one-shot test has new explicit user approval after this plan is
   reviewed.

## Existing software preflight and limits

- Feedback must be finite, advancing and no older than 300 ms.
- Software forward, lateral and yaw commands must all be zero.
- Every measured joint speed must be at or below 0.15 rad/s at entry.
- Roll and pitch must each be within 0.35 rad at entry and during the test.
- The resting joint pose must pass the existing controller limits.
- New and previous command tracking error must remain at or below 0.35 rad.
- Convergence requires every joint within 0.08 rad, final target velocity at or
  below 0.001 rad/s, and the 50 ms speed checks at or below 0.15 rad/s.
- Convergence must remain valid for a 0.5-second dwell and occur within six
  seconds after entry.
- The private send permit has an independent eight-second ceiling.
- The first `TARGET_REACHED` sample starts an absolute two-second hold deadline.
  Permit renewal cannot extend it.

Any failed preflight blocks the attempt and must not be bypassed or retried.

## Exact supervised sequence

Capture the console transcript from process startup. Perform one input at a time:

```bash
cd /home/abx/Desktop/robotdog_ws/github-handoff/build-handoff
script -q -f -c ./lite3_validation_console /tmp/lite3-auto-release-console.log
```

1. `status`
   - Require `preflight=[OK]`, fresh telemetry, zero velocity,
     `ownership=NOT_REQUESTED`, and `joint_send_enabled=0`.
2. `acquire`
   - This requests SDK ownership only. Require no unexpected physical response.
3. `status`
   - Require fresh telemetry, `preflight=[OK]`,
     `ownership=OWNERSHIP_UNCONFIRMED`, and `joint_send_enabled=0`.
4. `stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`
   - This is the single authorized motion action.
5. Send no further command while observing the expected progression:
   `PENDING` -> `STANDING_UP` -> `TARGET_REACHED` -> `ABORTING` ->
   `RELEASE_REQUESTED`.
6. After automatic release, run `status` and require idle state,
   `acquisition=NOT_REQUESTED`, `ownership=NOT_REQUESTED`,
   `joint_send_enabled=0`, fresh telemetry and zero velocity.
7. `quit`.

Do not use the separate `authorize_stand` plus `stand` sequence. Do not invoke
`rl_zero_once`, `forward_once`, `velocity`, or any leg-control primitive.

## Abort and acceptance rules

The operator uses the physical emergency stop immediately for unexpected motion,
support failure, collision, excessive noise, or any doubt. Software `stop` is the
secondary abort and uses the shared gate-close/release path.

If `TARGET_REACHED` remains active 2.5 seconds after it first appears, issue
`stop`, verify the gate closes, and mark the test failed. Do not wait for the
eight-second permit. Do not retry under the same approval.

Pass requires all of the following:

- `TARGET_REACHED` was observed.
- Automatic release occurred without operator `stop`.
- Release reason is `stand target hold complete`.
- The joint-send gate closed and ownership/request returned to `NOT_REQUESTED`.
- A completed diagnostic trace ends with the same release reason.
- The operator reports the supported robot's physical response and final posture.

SDK release may remove stiffness, so the final physical posture cannot be
predicted by software and is not required to remain standing.

## Evidence to retain

- Full console transcript from startup through `quit`.
- The `/tmp/lite3-stand-trace-*.jsonl` path printed after release.
- Pre-action and post-release `status` lines.
- Branch name, full commit SHA and executable SHA-256.
- Operator observation of motion, sound, support behavior and final posture.

Do not commit generated traces, credentials, machine authentication files, or
build trees. Summarize the evidence in a small reviewed document after the run.
