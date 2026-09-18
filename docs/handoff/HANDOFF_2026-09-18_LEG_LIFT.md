# Lite3 FR Leg Lift Handoff — 2026-09-18

## Goal
Make the DeepRobotics Lite3 stand normally, transfer weight safely, lift the Front-Right (FR) leg deliberately, hold briefly, lower it, recenter, and release control.

## Hardware / environment
- DeepRobotics Lite3 Venture
- Development machine: ThinkPad P14s
- Ubuntu / ROS2 Jazzy
- MotionSDK low-level joint control
- 12 joints:
  - FL: 0-2
  - FR: 3-5
  - HL: 6-8
  - HR: 9-11
- Per leg:
  - HipX
  - HipY
  - Knee

Nominal stand:
- HipX = 0
- HipY = -0.772979526
- Knee = 1.500500351

## Safety model
Low-level control remains position/PD based.
No raw feed-forward torque is used.

Existing safety guards include:
- roll/pitch <= 3 deg
- measured dq <= 0.50 rad/s
- tracking error <= 0.15 rad
- target velocity <= 0.10 rad/s
- explicit mechanical support / E-stop acknowledgement
- one-shot action followed by release

Do not weaken these blindly.

## Body shift work

A static body shift was developed before attempting leg lift.

Physical progression:
- 6 mm shift: worked
- 10 mm shift: worked
- 15 mm shift: worked

Offline results previously showed:
- 6 mm  -> max joint delta ~0.0276 rad
- 10 mm -> ~0.0463 rad
- 15 mm -> ~0.0702 rad
- 20 mm -> ~0.0944 rad

15 mm was chosen for physical leg-lift testing.

## FR lift attempts

Initial Cartesian FR lift attempts:
- 1 mm: motion occurred
- 2 mm: no visible clearance
- 5 mm: no visible clearance
- measured FK for the 5 mm attempt showed only ~2.73 mm actual FR foot motion relative to body
- 10 mm: still no visible ground clearance
- later test configuration increased FR lift to 20 mm with slower timing

The main conclusion:
The commanded FR direction was correct, but either:
1. the leg was still loaded and the body/compliance absorbed the command, or
2. the static weight transfer was insufficient.

## Vendor gait passive recording

A receive-only observer was created:

tools/lite3_passive_stand_observer.cpp

It uses Receiver only and does NOT request ownership or send joint commands.

Output:
- /tmp/lite3-stand-passive-observation.csv

Recorded telemetry includes:
- q0-q11
- dq0-dq11
- torque
- roll/pitch
- contact forces

Successful passive vendor recording:
- ~1000 Hz SDK callback
- no ownership request
- no control gate
- original remote remained in control

Important result:
Vendor gait uses coordinated diagonal/trot motion.
FR swing cannot simply be copied as a standalone three-leg static lift.

During strong FR-specific vendor motion, typical relative motion was roughly:
- HipY: -0.18 to -0.38 rad relative to other legs
- Knee: +0.25 to +0.40 rad

This supported the conclusion that our early 5-10 mm lift commands were very small compared with the vendor swing trajectory.

## Contact force observation

Contact force values were useful during vendor gait.

However, during our low-level validation runs, contact_force channels returned zero.
Therefore they currently cannot be used reliably to determine FR unloading during custom low-level control.

## Latest physical run

Command used inside lite3_validation_console:

body_shift_once SUPPORTED_ESTOP_BODY_SHIFT_LIMITS_CONFIRMED

Latest trace:

/tmp/lite3-stand-trace-5221-1238047946465.jsonl

Console showed:

STAND_TEST STANDING_UP
STAND_TEST BODY_SHIFT_SHIFT_WEIGHT
STAND_TEST ABORTING
STAND_TEST RELEASE_REQUESTED

Trace had ~4148 records.

Abort:
- event_detail = "supported body shift guard failure"

Last measured values before abort were approximately:
- roll = -0.0030 rad
- pitch = -0.0151 rad
- max_error = 0.0617 rad
- raw_max_speed = 0.0976 rad/s

These values were individually inside the reviewed limits.

## Guard investigation

SupportedBodyShiftGuard() currently checks:

1. body shift active
2. correct controller/state
3. control request active
4. joint command gate enabled
5. stand permit valid
6. elapsed time <= kTotalSeconds + 0.75
7. feedback valid/fresh/finite
8. roll/pitch <= 3 degrees
9. measured dq <= 0.50 rad/s
10. command bounds
11. tracking <= 0.15 rad

The measured trace did NOT indicate:
- tilt failure
- measured speed failure
- tracking failure

Important discovery:

stand_permit_->RenewSupportedHold()

is called when entering the supported body-shift action.

During the active body-shift trajectory, the guard uses:

stand_permit_->Valid()

but does not currently renew it continuously.

Because the latest leg-lift trajectory was lengthened, the leading hypothesis is:

THE STAND PERMIT EXPIRES DURING THE LONGER BODY-SHIFT / LEG-LIFT ACTION.

## Current next step

Do NOT increase the FR lift again yet.

First verify/fix the stand permit lifecycle.

Candidate fix:
During SupportedBodyShiftGuard(), renew the supported hold instead of only testing Valid(), while retaining:
- kTotalSeconds + 0.75 timeout
- tilt guard
- measured speed guard
- command bounds
- tracking guard

Then run only the relevant tests:

supported_body_shift_plan_test
supported_body_shift_once_test

Then rebuild:

lite3_validation_console

Then perform one mechanically-supported physical attempt.

Expected phase sequence:

BODY_SHIFT_SHIFT_WEIGHT
BODY_SHIFT_HOLD
BODY_SHIFT_LIFT_FR
BODY_SHIFT_HOLD_FR
BODY_SHIFT_LOWER_FR
BODY_SHIFT_RECENTER
BODY_SHIFT_VERIFY_STAND

Only after reaching BODY_SHIFT_LIFT_FR should FR physical clearance be evaluated.

## Important workflow

For small parameter/code changes:

1. edit
2. targeted build
3. run only the two relevant body-shift tests
4. launch validation console
5. one physical attempt
6. inspect trace if aborted

Avoid repeated full ctest runs unless structural changes were made.

## Git / development notes

Do not blindly commit:
- state_machine/state_machine.hpp.save
- fix_policy_path.py

Review before adding them.

Do not merge automatically.
