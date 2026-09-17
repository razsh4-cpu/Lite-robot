# Supported stand-only test — runtime implementation

This is NOT approval for unattended or unsupported floor operation. No hardware
test was performed during implementation. SDK ownership remains unconfirmed.
Mechanical support must prevent collapse when SDK release removes stiffness.
The operator must have the original emergency stop immediately available and
review current battery/health and the limits below before authorizing the test.
Undocumented state 98 is not reclassified by this code.

## Build and executable

The hardware-safe build is separate from the simulation build and any previously
running console:
`/home/abx/Desktop/robotdog_ws/low-level-leg-control/build-low-level-hw/lite3_validation_console`.
Build options: BUILD_SIM=OFF, BUILD_PLATFORM=x86, SEND_REMOTE=OFF.
The executable was built and started once for a receive-only `status`, then quit.
No ownership request or joint command was made. Offline tests use an injected
inert SDK.
The unchanged ONNX constructor resolves its model relative to the working
directory, so launch from `build-low-level-hw` as shown below.

## Later live sequence — do not paste as an automatic batch

Only after separate hardware go-ahead and passive health/safety checks:

```sh
cd /home/abx/Desktop/robotdog_ws/low-level-leg-control/build-low-level-hw
./lite3_validation_console
```

Then perform one console action at a time:

1. `status` — confirm fresh feedback, zero input, closed joint gate.
2. `acquire` — ownership request only; observe no unexpected physical movement.
3. `status` — request sent, OWNERSHIP_UNCONFIRMED, joint gate closed.
4. `stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED` — atomically attest
   mechanical support, supervision/E-stop, fresh acceptable battery/health and
   acceptance of the engineering limits, then queue one stand. The combined
   action prevents operator or remote-console latency from consuming the
   five-second authorization window. No gate opens until actual StandUp entry.
6. Observe without further mode/input commands. Expect STANDING_UP, then possibly
   TARGET_REACHED. A successful target is held for at most 2 seconds before the
   shared abort/release path; lack of convergence aborts at 6 seconds after entry.
7. `status` — expect RELEASE_REQUESTED, zero input, joint gate closed. Actual
   ownership return and physical posture must still be checked independently.
8. `quit` — shutdown; no duplicate release request and no automatic retry.

The separate `authorize_stand ...` followed by `stand` interface remains for
local development diagnostics. Do not use that two-command form for a real test:
on 2026-09-17, console/tool latency exhausted its five-second arm interval. The
request failed closed with `stand authorization expired`, requested release, and
never opened the joint-send gate. It must not be retried under the same approval.

`stop`, `release`, Ctrl+C/SIGINT and SIGTERM abort the supported test. Do not rely
on Ctrl+C instead of a physical E-stop. On unexpected movement, prioritize E-stop.
`rl` and `velocity` are rejected and abort an active test. No KEEP_STEPPING,
Motion Host velocity packets, RobotStateInit or automatic posture packet is used.

## Authorization and output

Only StateMachine can construct the private StandOnlyPermit. A grant is consumed
once per acquisition session and expires; duplicate acquire/authorize cannot
renew it. Opening the ordinary generic joint gate still requires confirmed
ownership. The separate supervised gate accepts only the private bounded permit
after entry and preflight, without changing IsControlAcquired().

Only the existing StandUpState runs during the authorized session. There is no
transition to RL, damping or another controller. The ONNX policy, stand spline,
joint PD gains and MotionSDK encoder are unchanged. The policy may be loaded by
the existing constructor but its inference/control worker is never entered.

## Shared abort sequence

1. Atomically latch stop/signal intent; clear stand authorization and queued modes.
2. Zero software velocity; close joint sends under the SDK send mutex.
3. Exit the current controller before ownership release (OnExit joins an RL worker
   if one existed; this test never starts one).
4. Request ControlGet(ROBOT) once. Local status is RELEASE_REQUESTED only if the
   call returned; this is not a robot acknowledgment. On an exception stay locked,
   report failure/unconfirmed ownership, and do not retry automatically.
5. Remain locked/passive. Fresh explicit acquisition and a new attestation are
   required for another test; telemetry recovery alone never resumes output.

Requests are checked before timestamp skipping and before the next trajectory
Run. An already in-flight SendCmd may finish; release waits for it, and subsequent
sends are prohibited. The private permit also checks the stop/signal latch at
send time and has an independent real steady-clock 8-second ceiling. If the
worker/process stalls, no external heartbeat keeper is installed. Firmware
command-loss behavior and physical damping timing remain firmware-dependent.

## Exact monitoring limits (engineering guardrails, not vendor specifications)

- Feedback must advance and remain valid; existing timeout is 300 ms. Invalid
  numeric feedback immediately makes it unusable until a newer valid sample.
- Before arming/entry: finite joints/IMU; absolute measured joint speed <=0.15 rad/s;
  roll/pitch within 0.35 rad; zero software velocity. Existing idle checks remain.
- Previous target tracking error: every joint <=0.35 rad, checked before Run.
- NEW target tracking error: every joint <=0.35 rad, checked at the send guard;
  non-finite commands, negative gains or nonzero feedforward torque are rejected
  for the supervised stand grant. The existing stand output has zero feedforward.
- Convergence requires a command generated at/after the unchanged trajectory's
  final phase (2 x stand_duration = 3 seconds of robot time), every joint error
  <=0.08 rad, measured joint speed <=0.15 rad/s, and target speed <=0.001 rad/s.
- These conditions must hold on progressing feedback for >=0.5 wall-clock seconds.
  Roll/pitch remain within 0.35 rad and within 0.03 rad of the dwell baseline.
- Nonconvergence by 6 wall-clock seconds after entry aborts. TARGET_REACHED is
  observed for at most 2 further seconds, then abort/release automatically.
- Loss of target stability after convergence, stale/invalid feedback, excess tilt,
  tracking error, authorization expiry, gate loss, exception or shutdown aborts.

TARGET_REACHED means measured joint/IMU criteria passed, not proof of balance,
foot contact or upright weight-bearing. Mechanical support must be present before
any action; never approach the robot to catch it after an abort.

## Offline evidence

Tests cover the actual unchanged StandUpState with inert MotionSDK, acquisition
without output, explicit arming, no pending/idle packet, consumed/expired grant,
all shared abort inputs, actual SIGINT/SIGTERM via the same console handler,
convergence/timeout, and concurrent in-flight send followed by stop/release.
The focused tests do not execute robot SDK networking or ONNX inference.
No test establishes actual ownership acknowledgment or safe unsupported release.
