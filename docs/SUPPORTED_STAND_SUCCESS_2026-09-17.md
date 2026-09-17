# Supported stand result — 2026-09-17

## Result

One explicitly authorized, mechanically supported `stand_once` test reached the
standing target. No RL, velocity, body-shift, leg-lift, or raw-torque command was
used. The operator held the emergency stop and the robot was mechanically
supported.

The guarded sequence was:

1. Passive `status`: telemetry fresh, preflight OK, velocity zero, joint gate
   closed, ownership not requested.
2. `acquire`: one ownership request; MotionSDK supplied no acknowledgement.
3. Second `status`: preflight OK, `OWNERSHIP_UNCONFIRMED`, joint gate closed.
4. Atomic `stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`.
5. State progression: `ARMED`, `PENDING`, `STANDING_UP`, `TARGET_REACHED`.
6. Operator `stop`, followed by `ABORTING` and `RELEASE_REQUESTED`.
7. Final status: idle state, ownership/acquisition `NOT_REQUESTED`, telemetry
   fresh, joint gate closed, and all software velocity components zero.

The final target was `[0, -0.7729795, 1.5005003]` rad for each leg. Near manual
release, maximum joint error was approximately 0.0593 rad, roll was -0.00195 rad,
and pitch was -0.01745 rad. The local diagnostic trace is
`/tmp/lite3-stand-trace-62127-23487113754492.jsonl`; it is not committed because
runtime traces are generated artifacts.

## Safety discrepancy and correction

The live controller remained in `TARGET_REACHED` with the joint-send gate open
instead of performing the documented automatic release after two seconds. The
trace shows that every fresh target-reached sample renewed the private permit,
allowing an indefinite healthy hold. The operator-driven `stop` path closed the
gate and requested release successfully.

The state machine now applies an independent absolute two-second deadline from
the first `TARGET_REACHED` result. At expiry it uses the existing shared abort
path with reason `stand target hold complete`: close the joint gate, exit the
controller, request SDK release once, and return to passive idle. Permit renewal
cannot extend this deadline.

Offline lifecycle, recovery, convergence-replay, authorization, fault and release
tests were updated to require this bounded behavior. The complete suite passes
13/13. This is a tightening of the safety gate; gains, target posture, trajectory,
and vendor packet mapping are unchanged.

## Remaining risks and next step

- MotionSDK still provides no positive ownership acknowledgement.
- All four live foot-force channels were zero in passive testing, so real contact
  detection remains unavailable or unverified.
- SDK release can remove stiffness; mechanical support remains mandatory.
- The two-second automatic-release correction is verified offline but has not
  been exercised on hardware.

The exact next step is engineering review of the trace and automatic-release
patch. No new hardware attempt should occur until that review is complete and the
user gives a new explicit supervised-test approval.
