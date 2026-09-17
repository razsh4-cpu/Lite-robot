# Experiments — evidence, not assumptions

Updated 2026-09-14. CURRENT_STATUS.md is the current operational snapshot.

## E13 — repeat external manual-axis forward: SUCCESS (2026-09-14)

After the first success, a new read-only preflight found fresh basic state 6,
battery 56%, correct Ethernet route, and no competing control process. The same
single-shot tool sent raw forward 9174 (`+0.099985` after firmware mapping) for
0.30 s, with lateral/yaw zero and neutral streams before/after. Operator had
requested the repeat; no automatic retry occurred. Post-test telemetry remained
`6/0/0`, battery 56%. Operator did not report a contrary physical result.

Log: `/tmp/lite3-manual-axis-forward-live-repeat-20260914.jsonl` — 51 records:
20 ZERO_BEFORE, 6 FORWARD, 20 FINAL_ZERO, 5 EXIT_ZERO.

## E12 — first external manual-axis forward: SUCCESS (2026-09-14)

Operator explicitly replied `GO`. Preflight found fresh RobotState `6/0/0`,
battery 57%, port 43897 available and no competing control process. The bounded
tool sent three 12-byte SimpleCMD packets per 20 Hz cycle: forward full code
`0x21010130`, lateral `0x21010131`, yaw `0x21010135`. It held all axes neutral
for 1.0 s, sent forward raw 9174 for 0.30 s (decoded by the firmware formula to
`+0.099985`) while lateral/yaw remained zero, then sent at least 1.0 s neutral
plus five exit-neutral triplets. No heartbeat, mode, posture, gait,
KEEP_STEPPING, legacy velocity, or joint command was sent by this tool.

The process exited 0; post-test telemetry was `6/0/0`, battery 57%. The operator
reported `workkkkkkk`, confirming physical forward locomotion. This proves the
external manual-axis path into the vendor gait controller under this exact test
condition; it does not yet prove backward/lateral/yaw, continuous teleoperation,
disconnect behavior, or safe operation outside the bounded tool.

Log: `/tmp/lite3-manual-axis-forward-live-20260914.jsonl` — 51 records with the
same 20/6/20/5 phase counts as E13.

## E11 — source-backed manual-axis protocol recovery (offline/read-only)

Static analysis of the robot-matched `deeprcs` binary established:

- `HeartbeatListener::RunRoutine` is the general UDP receiver on 43893 and
  accepts 12-byte SimpleCMD (`int32 code`, `int32 value`, `int32 type`).
- `Controller::ParseCommand` requires the command category/source bits
  `0x21000000`, then dispatches on low 16 bits.
- `0x21010130` sets `is_joystick_connect=1`, writes normalized forward to
  `ControlCommands.left_axis_y` (+32), and updates movement timing.
- Low-16 `0x0131` writes lateral `left_axis_x` (+24); `0x0135` writes yaw
  `right_axis_x` (+40). Full accepted wire codes are `0x21010131` and
  `0x21010135` respectively.
- Forward raw deadzone is [-6552,+6552]; positive mapping is
  `(raw-6553)/26214`. Raw 9174 therefore maps to +0.09998474.

The first draft used bare `0x0130`; review of ParseCommand's category check
caught and corrected this before any live packet. Offline byte tests verified
the forward neutral header `30 01 01 21` and forward pulse packet
`30 01 01 21 d6 23 00 00 00 00 00 00`. `strace` of dry-run showed no network
calls and the tool reported zero robot packets.

## E10 — explicit stop/release from RL-zero: SUCCESS (2026-09-13)

From TARGET_REACHED, `rl_zero_once ...` ran 1.4127 s; operator-triggered `stop`
ended it before the five-second deadline. Trace recorded 117 policy starts and
117 completions, normalized input 0,0,0 throughout, max tracking error 0.2017
rad, and the final send ~3.05 ms before the stop event. Console then reported
gate 0, acquisition NOT_REQUESTED, fresh telemetry and zero velocity. Operator
confirmed stable RL-zero and safe physical return to lying.
Trace: `/tmp/lite3-stand-trace-160982-363434026878013.jsonl`.

## E9 — bounded five-second RL-zero: SUCCESS (2026-09-13)

`rl_zero_once ...` remained active until the explicit `RL zero 5s deadline` at
5.0000066 s. 412 policy starts/completions; recorded policy input remained
0,0,0. No policy-send timeout, telemetry loss, or safety guard failure. Maximum
tracking error 0.1939 rad (<0.35). Operator confirmed physical stability during
the full window and safe return to lying after planned release.
Trace: `/tmp/lite3-stand-trace-160982-362946789885257.jsonl`.

## E8 — corrected long supported hold: SUCCESS (2026-09-13)

Robot held TARGET_REACHED for approximately 203 s. Internal monitor did not
abort; explicit release closed the gate and returned the robot safely to lying
per operator confirmation. Retained tail metrics: RMS max 0.0696, max tracking
error 0.0526 rad, stable roll/pitch, no >0.15 RMS sample. The log is a bounded
tail (24000 retained, 180295 replaced), so these maxima apply to the retained
last 24.3 s, while continuous TARGET_REACHED/no-abort covers the full hold.
Trace: `/tmp/lite3-stand-trace-160127-362598751481347.jsonl`.

## E7 — CONTROLLED RELEASE = SUCCESS ON REAL HARDWARE (2026-09-13)

Operator-reported sequence: successful supported stand hold -> explicit `release`
-> joint_send_enabled=0 -> acquisition=NOT_REQUESTED; telemetry remained fresh;
robot physically returned to lying as intended. Exact event time not supplied.
Same supported-stand build as E6; no production changes in this check.

Saved trace `/tmp/lite3-stand-trace-152452-358842653354612.jsonl` has final
`end_reason="stop requested"` (console release invokes StopVelocity first).
Buffer retained 24000 records and dropped 775334; do not claim a complete
release-time measured trajectory. Physical outcome/state observations are from
the operator. Prior focused inert test `stand_explicit_release` passed; it proved
gate closure, no subsequent joint sends, idempotent release and passive reception,
not physical posture. Actual SDK ownership acknowledgement remains unconfirmed.

Next milestone is RL at exactly zero normalized velocity. Static readiness check
found it deliberately blocked: RequestRLControl returns false; console `rl`
aborts/zeros, and stand-active execution cannot transition to the RL controller.
No live commands or additional offline test were necessary to establish this
unconditional block. Do not type `rl` expecting entry. A separately authorized,
reviewed zero-only RL transition is required; no safety gates were changed.

## E6 — REAL SUPPORTED STAND TEST = SUCCESS (2026-09-13)

**Computer-commanded supported stand: PROVEN ON REAL HARDWARE.**
Evidence is the operator's explicit report: robot reached standing posture,
remained standing, and no automatic release occurred.

Exact confirmed operator action and outcome:

```
stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED
-> robot reached standing posture
-> robot remained standing, without automatic release
```

The supported code requires an existing acquisition request and valid preflight,
then internally authorizes once -> submits stand -> guarded PENDING/STANDING_UP
-> convergence -> monitored hold. Surrounding console commands and TARGET_REACHED
output were not supplied with this success report; do not invent a transcript.

- Date: **2026-09-13**, Asia/Jerusalem (+03:00). Milestone documented at
  **21:00**. Exact physical stand time is not recorded. The matching active
  console started at **20:54:10**; that is process start, not stand-command time.
- Build: `/home/abx/Lite3_rl_deploy/build_supported_stand/lite3_validation_console`,
  build mtime **20:46:57 +03:00**; branch `main`; base commit
  `c2432945161d38fec8633a997ce5f9f0dc8c5ec2` plus staged/unstaged/untracked changes.
- Active executable SHA-256 matches the rebuilt file:
  `a7486dfeaed05a883444a92ca9332fea049dbe276245a21f2446b0ec1fdf1372`.
- Success log path: **not located/confirmed**. Active console PID 152452,
  pts/0, stdout/stderr `pipe:[699492]`, not a regular transcript file.
  This entry preserves the operator's report. Buffered traces normally flush
  to `/tmp/lite3-stand-trace-152452-*.jsonl` after release; this is an expected
  pattern, not a confirmed existing success file. Do not release just to get a log.
- Related offline validation log:
  `/home/abx/Lite3_rl_deploy/build_supported_stand/Testing/Temporary/LastTest.log`
  (hold-success/failure tests; overwritten by future CTest runs, not hardware proof).

Fixes enabling success:
1. `stand_once` combines authorization and stand request, removing operator timing.
2. 50 ms RMS-speed plus position-range convergence avoids isolated-speed-spike resets.
3. Fresh/converged feedback renews the bounded hold permit; no two-second auto-release.

**Next milestone: controlled return-to-rest / stop/release validation.** Stable
release is not proven; abort/release may remove stiffness. No RL/velocity/walking
was validated, and SDK ownership acknowledgement remains unconfirmed. No code,
robot state or robot commands were changed while documenting this result.

# Superseding update — 2026-09-17

A separately authorized, mechanically supported `stand_once` reached the target.
The indefinite successful hold described in E6 remained active until operator
`stop`; the gate then closed and SDK release was requested. The handoff branch
now enforces an absolute two-second post-convergence hold. All 13 offline tests
pass; the correction has not been hardware-tested. See
`docs/SUPPORTED_STAND_SUCCESS_2026-09-17.md`. Historical experiment entries below
remain evidence of their original builds, not the current hold policy.

## E1 — acquisition-only (earlier supervised run)

Operator requested acquire, then release. Robot reportedly remained still;
feedback fresh, input zero, joint_send_enabled false. No RobotStateInit/stand/RL
or joint streaming. Local acquisition returned to NOT_REQUESTED after release.
Actual firmware ownership acknowledgment remained unavailable. This proves only
that the tested request/return sequence produced no observed physical movement.

## E2 — first attempted supervised stand, abnormal later posture

Source `/tmp/lite3-stand-operator-ready.log` (~lines 4108–4146).
Nearest initial q and later q are preserved in STAND_RECOVERY_2026-09-13.md.
Observed local sequence: ARMED -> PENDING -> STANDING_UP -> ABORTING ->
RELEASE_REQUESTED. `abort_reason=[send guard rejected output]`.
Operator reported noise/slight movement but no completed standing. No walking/RL.

The old log lacks synchronized desired/measured vectors, returned-send counters
and branch-specific rejection. Exact first cause is UNRESOLVED. Do not assert
tracking failure, gains, initialization, or a mapping defect as proven.
Later samples showed FR/HR HipY +2.506/+1.462 rad. They cannot reconstruct the
active transition; a subsequent attempt was blocked by idle checks/arm expiry.

## E3 — autonomous recovery (no physical actuation)

All acquire/stand/release calls were to inert transports. Built the actual
trajectory + guard replay; fixed timing/snapshot/preflight/logging issues.
Five focused CTest targets passed plus startup-only regression. Final CTest
duration ~8.87 s (includes deliberately waiting for permit expiry).

- Recorded-start mock completes preparation, raising, final convergence, and
  bounded observation. Two asymmetric valid starts also pass.
- Old absolute float timestamps collapse adjacent ms at 2,000,000 seconds uptime;
  updated double clock passes a full long-uptime replay.
- Frozen measured response fails at ~0.435 s with TRACKING_ERROR. This is a
  synthetic scenario, NOT proof of the historical robot response.
- Late arm at 4.8 s completes despite crossing original 5 s arm deadline.
- All ten result/rejection enum labels exercised across 28 JSON traces / 23,739
  records. All 12 target/feedback/SDK command fields checked.
- Stale/invalid feedback, invalid commands, tilt, tracking, expiry, closed gate,
  transport failure, in-flight release, stop/signal lifecycle tested.
- RL/nonzero velocity blocked; current stand gains/targets retained.
- Syscall traces: zero network calls from inert tests.

35 s passive observation before posture reset: ~1000 Hz, finite stable telemetry,
right HipY persistently outside software range. No sign/offset correction applied.
Current raw-telemetry representation alone could not identify physical posture.

## E4 — normal lying posture reset and passive readiness (latest)

Human confirmed `LYING READY` after normal battery/startup/original-controller
lying procedure. No laptop actuation during observation. 35 s receive-only check
yielded 34,999 callbacks, max fresh age 1.63351 ms, no sampled position jump above
0.00083924 rad; all joints/IMU finite, tick advancing.

HipY now FL -1.1604, FR -1.1633, HL -1.1498, HR -1.1479 rad. All pass unchanged
ranges. The prior right-leg range blockage disappeared without software mapping,
sign, gain, limit or target edits. Posture/startup dependence is supported; exact
effect of battery reset versus leg arrangement is not separately proven.

Console startup: WAITING_FOR_TELEMETRY -> LOCKED, abort_reason empty, preflight OK,
request/ownership NOT_REQUESTED, input zero, joint gate closed. No startup latch.

## E5 — current acquisition-only, after normal lying

User explicitly typed `acquire`. Fresh precheck passed. Console submitted ONE
ownership request and printed REQUEST_SENT / OWNERSHIP_UNCONFIRMED.
Transmission trace contains one 12-byte send to connected UDP 192.168.1.120:43893:
`14 01 00 00 00 00 00 00 00 00 00 00`. This is the existing vendor acquisition
path, NOT a candidate to replay manually. No joint packet was transmitted.
Subsequent status: fresh feedback, preflight OK, velocity zero, joint gate 0,
stand LOCKED, no abort. Operator explicitly confirmed robot remained still.

**Release has NOT been requested in this current session.** Stand has NOT been
authorized or requested. Do not confuse E1's earlier release with current state.
The documentation handoff only read `status`; it did not actuate or release.

## What is physically proven / not proven

Proven under the recorded conditions: Ethernet and feedback reception; passive
SDK joint/IMU decoding; safe observed acquisition-only requests; earlier release
request without reported movement; normal posture passes range checks; and E6:
computer-commanded supported stand completed and remained standing without
automatic release, as physically confirmed by the operator.

Offline only: exhaustive convergence/guard behavior under injected scenarios,
normalized software command plumbing, and the new abort-path fault tests. The
successful physical posture/hold does not prove every fault case. RL-zero stability,
autonomous walking, physical velocity scale, stopping distance, controlled
return-to-rest and safe unsupported release remain unproven.

## Evidence locations

Latest directory `/tmp/lite3-lying-check.u8qXO2/`:

- `lying-observation.csv`: normal-lying full passive sample record.
- `previous-observation.csv`: earlier asymmetric posture observation.
- `summary.log`, `network.log`: normal-lying observer summary/zero-send trace.
- `console.log`, `console-network.log`: CURRENT running acquisition-only session.

Earlier:

- `/tmp/lite3-stand-operator-ready.log`: first failed stand and blocked retry.
- `/tmp/lite3-stand-final-build.log`, `/tmp/lite3-stand-final-tests.log`.
- `/tmp/lite3-stand-offline-network.log`: inert syscall evidence.
- `build_supported_stand/Testing/Temporary/LastTest.log`: detailed tests and paths.
- `/tmp/lite3-passive-observer-summary.log`: earlier abnormal-posture observation.
- `/tmp/lite3-final-passive-console.log`: earlier safe startup and range rejection.
- `/tmp/lite3-stand-trace-<pid>-<monotonic-ns>.jsonl`: bounded diagnostics;
  recovery-session files were INERT tests, not physical actuation evidence.

Selected immutable copies are in `docs/handoff_evidence/20260913/`. The copied
current-console transcript is only a handoff snapshot; /tmp original may grow.
Never assume /tmp survives reboot. Do not overwrite the failed-attempt evidence.
