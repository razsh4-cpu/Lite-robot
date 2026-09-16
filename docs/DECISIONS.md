# Decisions and safety contract

## Architecture choices

Use existing Lite3_rl_deploy + bundled x86 MotionSDK. No Xbox, App Auto mode,
Nav2, custom Motion Host velocity 320/321/325, KEEP_STEPPING, UART injection,
firmware edits or new packet guessing in this stand task.
SoftwareVelocityInterface retains normalized [-1,1] future policy input, not m/s.
Its timeout is 300 ms; invalid/nonfinite axes zero all inputs. The current outer
StateMachine deliberately blocks RequestRLControl and nonzero velocity entirely.
The unchanged ONNX model can load during startup without entering RL control.

## Acquisition versus actuation

- Hardware construction creates no Sender; Start is receive-only.
- AcquireControl requires fresh finite feedback and sends only the existing
  vendor ControlGet(2) request. No RobotStateInit or joint initialization exposed.
- No authoritative ownership acknowledgment exists. IsControlAcquired remains
  false; console reports REQUEST_SENT / OWNERSHIP_UNCONFIRMED honestly.
- Generic joint gate cannot open on unconfirmed ownership. A separate private,
  explicit, mechanically-supported stand-only permit is the reviewed exception.
  Only StateMachine can create it; this is human test authorization, NOT an SDK ack.
- Acquisition/release/send are mutex serialized. Repeated requests are idempotent;
  release waits out an in-flight send before subsequent sends are prohibited.

## Stand controller retained

OnEnter captures measured q/dq/tick coherently. Stage 1: 1.5 s cubic movement to
`[0,-1.354531,2.549477]` per leg. Stage 2: 1.5 s height trajectory from .12 to .33 m,
final `[0,-0.653535,1.271092]` per leg. Four legs repeat HipX/HipY/Knee targets.
Kp=100, Kd=2.5, feedforward=0; targets, gains, spline and stage durations unchanged.
Double absolute timestamps fix precision; an extra PreStand was NOT added.
Stage 2 remains time-based; no proof justified changing the reference trajectory.

## Freshness and guards

Valid feedback: finite joints/IMU and advancing uint32 tick; steady-clock timeout
300 ms. Frozen/backward ticks do not refresh. Invalid data invalidate eligibility;
last-known versus current samples stay distinguishable. Passive startup waits
without latching an active-stand abort; active failures remain latched.

Preflight: fresh/finite, input zero, absolute measured joint speeds <=.15 rad/s,
absolute roll/pitch <=.35 rad, existing Idle joint bounds +.1 rad tolerance.
Nominal per-leg bounds: HipX ±.530, HipY [-3.500,.320], Knee [.349,2.800] rad;
effective HipY upper .420. No range widening/sign inversion was performed.

Send guard checks CURRENT interpolated target versus current measured q, <=.35 rad
per joint, finite command, nonnegative gains, zero feedforward, valid permit and
fresh feedback. Monitor checks previous accepted target before another Run.
No startup grace, looser threshold or persistence filter was added to hide failure.

Arming expires after 5 s BEFORE entry. Active stand has a separate 8 s permit.
Convergence: final target, error <=.08 rad, measured speed <=.15 rad/s, desired
speed <=.001 rad/s, roll/pitch <=.35 rad and within .03 rad of dwell baseline for
.5 s of progressing feedback. Deadline 6 wall-clock seconds; successful target
observed for 2 s then shared abort/release. TARGET_REACHED is not proof of balance.

## Shared stop/abort/release

stop, release, SIGINT/SIGTERM, stale/invalid feedback, loss of gate/state, tracking,
tilt, expiry, failure deadline or exception all take the idempotent shared path:

1. Latch abort before the next trajectory update; clear queued requests/arm state.
2. Zero software input and close joint gate under send mutex.
3. Exit current state; safely stop/join any worker before ownership return.
4. Request existing ControlGet(1) once if an acquisition request was outstanding.
5. Remain locked; never retry/reacquire automatically. Flush diagnostics afterward.

No posture hold or damping command is synthesized. Disabling sends/releasing may
remove stiffness. Mechanical fall support and independent E-stop are mandatory.
SIGKILL cannot perform cleanup; a stuck SDK call can delay cooperative release.
No heartbeat keeper continues after crashes. Physical timeout behavior is not
proven for this firmware. Current stand test intentionally has no heartbeat stream.

## Diagnostics

Bounded 24,000-record in-memory trace, flushed after gate closure/release attempt.
Exact reasons: STALE_FEEDBACK, INVALID_COMMAND, TRACKING_ERROR, EXCESSIVE_TILT,
PERMIT_EXPIRED, SEND_GATE_CLOSED, INVALID_MEASURED_STATE, STATE_CHANGED, OTHER.
Includes phase, monotonic time, q/dq/tau/targets/errors, joint/leg, freshness,
permit remaining, request/gate and sent-return status. Entry q/dq/tick are separate
log-only metadata, NEVER substituted for current guard feedback.
`SENT` means transport returned, not physical robot acknowledgment. Crash before
flush may lose the buffer. Old generic logs cannot retroactively supply these data.

## Posture interpretation and changes deliberately rejected

Right HipY values changed from +2.506/+1.462 to -1.1633/-1.1479 after normal
power-up/lying setup with unchanged software. No mapping correction is justified.
Do not call this absolute proof against firmware calibration/zero changes during
restart; combined physical conditions changed. Recheck from a reproducible posture.
No gain tuning or initialization was justified by the incomplete failed-stand log.
