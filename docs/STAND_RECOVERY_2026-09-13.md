# Stand recovery session — 2026-09-13

## Latest handoff update — normal lying posture recovered (19:29 +03:00)

**The NOT_READY result below is the historical autonomous-recovery result, not
the latest state.** Read [CURRENT_STATUS.md](CURRENT_STATUS.md) first.

After normal battery reconnect/startup and manufacturer-controller lying posture,
operator confirmed LYING READY. A new 35 s passive record showed all HipY joints
normal: indices 1/4/7/10 approximately -1.1604/-1.1633/-1.1498/-1.1479 rad.
No mapping/sign/offset/limit/gain/target edit was made between observations.
This supports posture/startup dependence; it does not independently isolate
physical posture from restart/calibration effects or prove every encoder convention.

Latest live acquire-only was explicitly approved. One 12-byte vendor SDK ownership
request was sent, with no joint packets. Operator confirmed the robot remained
still. Current console: LOCKED, preflight OK, abort empty, fresh telemetry,
velocity zero, gate closed, REQUEST_SENT / OWNERSHIP_UNCONFIRMED.
Current acquisition has NOT been released. No new stand authorization/attempt
has occurred. See [EXPERIMENTS.md](EXPERIMENTS.md) and [NEXT_STEPS.md](NEXT_STEPS.md).
The prior guard rejection remains historically unresolved; detailed logging is
ready for the next explicitly approved, mechanically supported single stand.

Everything below documents the earlier recovery session chronologically. Statements
such as "no console remains" or "no acquisition sent" apply to THAT session only.

## Result: NOT_READY — physical posture/calibration check required

No acquisition, authorization, stand, initialization, joint, velocity, RL,
heartbeat or other robot command was transmitted in this session. All acquisition,
stand and release tests below used inert transports, not the robot. Live operations
were receive-only observation and passive console status/startup/shutdown.

The current physical blocker is stable feedback outside the existing software
limits: FR HipY (index 4) ~+2.506 rad and HR HipY (index 10) ~+1.462 rad.
Neither signs nor limits were changed to accept these values. Human mechanical
observation/calibration evidence is needed; telemetry alone cannot establish
which physical posture those encoder readings represent.

## 1. Root cause of first abort: only immediate cause proven

Historical source: `/tmp/lite3-stand-operator-ready.log`, around lines 4108–4146.
The recorded sequence is authorization, PENDING, STANDING_UP, ABORTING,
RELEASE_REQUESTED, then status with `send guard rejected output`.

Source reconstruction: Idle preflight passes -> StandUp OnEnter captures measured
q/dq/timestamp -> a new bounded stand-only permit opens the gate -> the next fresh
feedback iteration runs the trajectory -> HardwareInterface evaluates the new
interpolated output -> rejection closes the gate -> StateMachine aborts before
any subsequent trajectory call -> closes/join-exits the controller -> requests
ownership return once. Ownership acknowledgment is never fabricated.

The historical log has neither per-command timestamps nor sent command vectors or
a successful-send counter. It cannot establish the first successful send time,
number of successful sends, active phase at rejection, or which guard fired.
Possible rejecting paths were permit invalidation, freshness, malformed/nonfinite
output, tilt, tracking, or invalid gain/feedforward fields. A subsequent FRESH
status does not exclude an earlier stale-feedback check. Tracking is plausible,
not retrospectively proven. Do not label this a proven gain or posture failure.

Nearest printed pre-entry q, radians (not the exact historical OnEnter snapshot):

```
0.0669479  0.4193500 2.7373600  -0.0818253  0.3396990 2.3986800
0.0785446 -0.0981522 2.4027300  -0.0762558 -0.1874160 2.6772300
```

Later post-abort/reacquisition q:

```
0.0735855  0.414772 2.73865   0.439568 2.50592 2.40532
0.0805283 -0.102043 2.40677   0.445061 1.46145 2.74894
```

These are not a synchronized active-stand response trace.

## 2–4. Concrete fixes and files

- `state_machine/standup_state.hpp`: retain absolute timestamps as double, avoiding
  float quantization of millisecond feedback at long uptimes. Capture q/dq/time
  together. Add log-only exact entry metadata and trajectory elapsed context.
  Cubic equations, stage durations, targets, gains and final posture unchanged.
- `interface/robot/robot_interface.h`: coherent stand-feedback accessor and
  inert-by-default diagnostic hooks; existing backend compatibility retained.
- `interface/robot/hardware/hardware_interface.hpp`: coherent feedback snapshot;
  retain invalid received data for explicit diagnostics without refreshing it;
  classify every send rejection; record all desired/measured joint vectors,
  IMU, freshness, permit, gate, request state, returned-send result and timing.
  Store accepted command only after transport returns successfully.
- `interface/robot/stand_diagnostics.hpp`: bounded-record schema, reason enum,
  explicit SDK joint names. `SENT` means transport returned, NOT robot acceptance.
- `interface/robot/stand_only_permit.hpp`: read-only cancellation/expiry inspection.
- `state_machine/state_machine.hpp`: preserve detailed send rejection in abort;
  distinguish invalid measured feedback from silence; coherent monitor samples;
  log supervisor entry/exit; flush after gate closure and ownership-return attempt.
  Preflight checks the EXISTING Idle joint-position bounds/tolerance before arm,
  with an actionable index/name/value explanation. No bounds widened.
- `state_machine/idle_state.hpp`: throttle unchanged invalid-joint/IMU status to
  changes/at most 1 Hz rather than every control iteration. Keep checks unchanged.
- `tools/lite3_validation_console.cpp`: status includes specific preflight reason.
- `tools/lite3_passive_stand_observer.cpp`: bounded receive-only observer; no Sender;
  both control methods throw. Vendor detached receiver exits with the process.
- `tests/stand_recovery_test.cpp`: actual Idle/StandUp/HardwareInterface replay via
  inert injected transport, including recorded and asymmetric valid start poses.
- `CMakeLists.txt`: only observer/replay targets added for this work.

The repository already had extensive safety modifications before this session.
Do not attribute its entire git diff to these changes. ONNX/RL, transport backend,
ownership semantics, firmware and network configuration were not changed here.

## 5. Joint mapping

Proof: vendor `robot_types.h` LegData/RobotCmd unions; MotionSDK README joint-order
tables; HardwareInterface direct array access; inert tests check every outgoing
position/velocity/kp/kd/torque field. StateMachine does not permute these arrays.
No extra sign inversion is applied in this stand path. Physical axis calibration
has NOT been established by this static proof.

| Index in controller, feedback and SDK command | Leg | Joint | Software nominal range rad | Pre target | Stand target |
|---|---|---|---|---|---|
| 0 | FL | HipX | -0.530..0.530 | 0 | 0 |
| 1 | FL | HipY | -3.500..0.320 | -1.354531 | -0.653535 |
| 2 | FL | Knee | 0.349..2.800 | 2.549477 | 1.271092 |
| 3 | FR | HipX | -0.530..0.530 | 0 | 0 |
| 4 | FR | HipY | -3.500..0.320 | -1.354531 | -0.653535 |
| 5 | FR | Knee | 0.349..2.800 | 2.549477 | 1.271092 |
| 6 | HL | HipX | -0.530..0.530 | 0 | 0 |
| 7 | HL | HipY | -3.500..0.320 | -1.354531 | -0.653535 |
| 8 | HL | Knee | 0.349..2.800 | 2.549477 | 1.271092 |
| 9 | HR | HipX | -0.530..0.530 | 0 | 0 |
| 10 | HR | HipY | -3.500..0.320 | -1.354531 | -0.653535 |
| 11 | HR | Knee | 0.349..2.800 | 2.549477 | 1.271092 |

Idle already adds 0.1 rad tolerance: effective HipY upper bound is +0.420.
These are software limits, not newly verified mechanical limits. The local
`third_party/deep_robotics_model` directory is empty, so no additional model-based
physical calibration proof was available. Model fetching was not needed to
verify the existing SDK array mapping.

## 6. Trajectory analysis

The existing PreStand-equivalent stage already interpolates from measured q AND
dq to `[0,-1.354531,2.549477]` on each leg in 1.5 s. Next it interpolates modeled
height 0.12 -> 0.33 m in 1.5 s using thigh 0.20 m and shank 0.21 m.
Final triplet is `[0,-0.653535,1.271092]`, repeated four times.
The SDK separate PreStandUp example instead uses [0,-70°,150°]; it is not called.

At t=0 spline q/dq equal captured q/dq. At stage boundary the positions agree and
the first-stage terminal velocity is zero. Stage-2 velocity is a 1 ms finite
difference, so it has small discretization error, not an exact analytic derivative.
Cubic acceleration is bounded but not jerk-continuous at segment boundaries.

Recorded-start nominal replay at 1 ms steps: maximum target delta 0.00178656 rad,
maximum desired speed 1.78649 rad/s, observed finite-difference acceleration peak
about 5.63 rad/s². This validates numerical behavior, not motor torque capability.
All replayed targets remain inside existing software acceptance bounds.

Stage 2 is still time-based. Measured convergence gating may be useful, but there
is no evidence the failed hardware test reached Stage 2. The existing guard and
whole-stand convergence monitor remain active; no extra stage or grace period
was added on conjecture. Kp=100, Kd=2.5 and zero feedforward remain unchanged.

## 7. Guard analysis

The 0.35 rad guard compares the NEW CURRENT INTERPOLATED target to a coherent
latest feedback snapshot, not the final stand target. It applies from the first
send. A total planned excursion >0.35 is not itself a violation: only instantaneous
target-to-measured error is bounded. No threshold increase, persistence filter or
startup grace was introduced. Target and feedback naturally refer to different
instants; coherent feedback removes mixed packets, not physical plant delay.

Explicit reasons: STALE_FEEDBACK, INVALID_COMMAND, TRACKING_ERROR,
EXCESSIVE_TILT, PERMIT_EXPIRED, SEND_GATE_CLOSED, INVALID_MEASURED_STATE,
STATE_CHANGED, OTHER. New trace captures the offending joint and complete vectors;
invalid numeric fields serialize as null, not invalid JSON NaN/Infinity literals.

Monitor rejection before a new trajectory update also records its current
feedback/last target. Entry metadata is separately labelled `metadata_only` and
is NEVER used as current feedback or as a safety-guard input.

## 8. Authorization

Existing 5 s arm deadline applies only to ARMED/PENDING and entry preflight.
Active stand gets a separate 8 s permit. Monitor deadline is 6 s; convergence
requires <=0.08 rad error, <=0.15 rad/s measured speed, final zero desired speed
and 0.5 s stable dwell. Successful observation lasts 2 s before shared release.
The late-start replay arms at t=0 and starts at t=4.8 s; it completes without the
arm deadline killing active stand. Real permit expiry is separately tested.

## 9. Stream/abort safety

Worker sleeps 500 us and updates once per changed feedback timestamp; observed
feedback callback rate is ~1000 Hz. This does not guarantee a future hard real-time
send rate under load. Next trace records each returned send and wall time.

Send/release synchronization and abort-before-next-Run tests pass. stop, release,
signal, stale/invalid feedback and failures converge on the shared abort path.
No hold/damping/posture command is added. Release may remove stiffness: mechanical
support remains mandatory. SDK send blocking and robot-side ownership acceptance
cannot be physically proven offline.

All hot-path records are bounded in memory (24,000 capacity; overflow counted).
File I/O is deferred until AFTER gate closure and the release attempt. Trace path:
`/tmp/lite3-stand-trace-<pid>-<monotonic-ns>.jsonl`.
If the process crashes before flushing, the buffer may be lost; do not mistake
absence of a trace for absence of packets. Terminal transcript remains useful.

## 10–12. Offline replay, tests and build

Production trajectory + production guard + actual IdleState + inert transport:

- Recorded initial q/dq: complete 3 s trajectory, convergence and bounded observation.
- Two additional asymmetric valid poses: complete successfully.
- Uptime 2,000,000 seconds: complete successfully. Old float collapses adjacent
  millisecond timestamps; double retains necessary resolution.
- Frozen measured joints: rejects at approximately 0.435 s with TRACKING_ERROR.
  This is a synthetic nonresponse test, NOT reconstruction of actual robot lag.
- Specific stale, NaN, Inf, tilt, bad feedforward and expired-permit rejection.
- No early send on stand request; no post-release send; unchanged gains/targets;
  all 12 transport fields and array/name mappings checked.
- Invalid currently observed resting poses reject before authorization.
- Existing stop/release/in-flight-send/signal/idempotency tests retained.
- Passive startup wait/recovery regression retained; RL/nonzero velocity blocked.
- Console invalid-posture flood regression checks 1,000 evaluations produce one
  unchanged warning, while all evaluations continue to block transition.

Build targets: lite3_validation_console, lite3_passive_stand_observer,
stand_recovery_test, control_safety_test, vendor_adapter_test. BUILD_SIM=OFF,
BUILD_PLATFORM=x86, SEND_REMOTE=OFF. No deploy target executed.
Focused tests: software_velocity_interface_test, control_safety_test,
stand_recovery_test, stand_monitor_test, vendor_adapter_test; plus startup-only.
Test/trace evidence paths are listed below. No vendor library is linked into
stand_recovery_test; its inert transport cannot access the network.

Final results: affected-target build PASSED; five focused tests PASSED (8.87 s
under syscall tracing); startup-only regression PASSED. Parsed 28 inert trace
files / 23,739 valid JSON records. All ten send-result/rejection enum labels are
represented, including simulated transport failure and closed gate. Trace schema
and 12-element arrays validated. `git diff --check` passed.

## 13. Passive evidence

35-second receive-only observation: 34,999 SDK feedback callbacks (~999.968 Hz).
3,499/3,500 sampled observations fresh; the one missing sample was startup.
Maximum fresh age 0.00109414 s. All fresh joint and IMU values finite.
Maximum absolute roll/pitch ~0.002634/~0.002609 rad. Sampled tick steps 9–11 ms
at a 100 Hz observer rate. No sampled joint jump >0.000840 rad.

FR HipY range +2.50576..+2.50630; HR HipY +1.46175..+1.46252. Both persistently
outside current software bounds. This rules out a brief single-sample glitch in
this observation, not an incorrect physical calibration or stable decoding error.
Some instantaneous reported joint speeds reached ~0.17 rad/s despite tiny position
changes, so the unchanged 0.15 stationary preflight may also reject individual
samples. No filtering/threshold weakening was introduced without physical evidence.

Final passive console status observed WAITING_FOR_TELEMETRY -> LOCKED, no startup
abort latch, telemetry fresh (~0.00065 s), request/ownership NOT_REQUESTED,
joint_send_enabled=0, software input 0/0/0; preflight identifies index 4 out of range.
Console was closed without acquisition. Send/connect syscall traces contain no
transmission calls. Passive observer has no Sender symbol and explicitly rejects
any control operation.

Final console transcript after log throttling is 77 lines rather than 2,986 for
the same short passive window. No console/observer process remains; UDP 43897 is
free. Final recorded feedback age was 0.00062566 s. The final build is prepared
on disk, NOT left running with actuator capability enabled.

## 14–16. Remaining uncertainty, posture, confidence

Current blockers cannot be removed by honest software changes alone:

1. A human must compare the right-leg physical configuration and encoder readings
   with a supported ready posture, or obtain vendor calibration/sign confirmation.
2. Actual ownership still has no authoritative SDK acknowledgment.
3. First abort's precise guard and commanded/measured trajectory are unrecoverable
   from the historical log; new logging makes the NEXT authorized test conclusive.
4. Joint dynamics, self-collision/foot contact and safe release under support require
   physical supervision. Finite telemetry is not a complete fault/battery certificate.

Required starting posture: mechanically supported, clear legs, level/stationary,
correctly interpreted joint angles within existing accepted bounds; not arbitrary
folding that merely looks safe. Do not reposition energized legs by hand.
Original controller/E-stop immediately available. Vendor README recommends hoisting
and keeping personnel clear (5 m) during SDK tests.

Confidence percentage: no statistically defensible probability of successful
physical standing exists. Static mapping/numeric trajectory are tested; zero
successful complete hardware stands are evidenced. Do not turn passing mock tests
into a fabricated hardware-success percentage.

## 17. Future operator sequence — NOT executed

First resolve the physical posture/calibration blocker and review fresh passive
health/battery information. Do not continue if preflight is not OK.

```
cd /home/abx/Lite3_rl_deploy/build_supported_stand
script -q -f -e -c './lite3_validation_console' "/tmp/lite3-next-supervised-stand-$(date +%Y%m%d-%H%M%S).log"
```

Inside the console, one supervised action at a time:

```
status
acquire
status
authorize_stand SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED
stand
```

Type stand within the existing 5 s arm window, only after explicit physical safety
confirmation. No automatic retry. Do not issue RL/velocity. Any unexpected motion,
tilt, stale data or tracking failure requires the supported abort path and physical
E-stop as needed. `stop` uses the shared abort/release; do not expect it to hold
the robot upright without mechanical support. Review `status` and the saved trace.

## Evidence files

- `/tmp/lite3-stand-final-tests.log`
- `/tmp/lite3-stand-final-build.log`
- `build_supported_stand/Testing/Temporary/LastTest.log`
- `/tmp/lite3-stand-offline-network.log`
- `/tmp/lite3-passive-observer-summary.log`
- `/tmp/lite3-passive-observer-network.log`
- `/tmp/lite3-stand-passive-observation.csv`
- `/tmp/lite3-final-passive-console.log`
- `/tmp/lite3-final-passive-console-network.log`
- `/tmp/lite3-stand-trace-*.jsonl` (this session's traces are explicitly INERT tests)

One proposed logging implementation was rejected by the safety reviewer because
cached entry feedback could be confused with current guard inputs. It was NOT
applied. The accepted alternative stores entry q/dq/tick only as separate file
metadata; every guard continues to read current feedback.
