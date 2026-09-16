# Acquisition-only safety review — 2026-09-13

READY_FOR_ACQUISITION_ONLY_REVIEW. Offline evidence only; no hardware test
authorized or performed. Robot commands sent during this task: 0.

## Preserved components

The ONNX model, policy runner calculations, joint mapping, gains and stand
trajectory are unchanged. Only lifecycle, synchronization, validation, gates,
telemetry handling, console reporting and tests changed.

Policy SHA256:
efa6581d314d8c0442881453d39fc082c09b28bbaa3029d328fcd61fa25b57c7

## Acquisition / ownership

Construction creates no SDK Sender or Receiver. Start creates receive-only
feedback; Sender construction is deferred until an explicit ownership request.

AcquireControl requires finite decoded feedback with a progressing tick within
300 ms on a steady clock. It sends ControlGet(2) only, never RobotStateInit or
SendCmd. Repeated acquire is idempotent. No joint-initialization operation is
exposed: whether one is necessary later needs separate review.

REQUEST_SENT does not mean OWNERSHIP_CONFIRMED. The available RobotData/SDK has
no authoritative ownership acknowledgment, so real hardware reports
OWNERSHIP_UNCONFIRMED and keeps stand, RL and joint transmission blocked.
Only the inert test backend can supply confirmed ownership.

Release requests ControlGet(1). Its physical effect/ownership return remains
unconfirmed, which the console states explicitly.

## Thread and state gates

A mutex serializes ownership requests, gate changes, and complete joint sends.
Release waits for any in-flight send, then prevents subsequent sends.

StateMachine methods and iterations share a lifecycle mutex. RequestStand queues
intent without enabling the send gate. Gates open only after entry into an
authorized state. The worker's observations/counter are synchronized. Policy
initialization precedes worker start. Worker stop is atomic and join idempotent.

Shutdown/release order:
1. Zero/stop software input and cancel pending stand/RL/velocity intent.
2. Close joint send gate, waiting out an in-flight send.
3. Exit active controller and join RL worker.
4. Request ownership return.
5. Exit on shutdown; reset to idle on explicit release.

Reacquisition cannot replay old requests. SIGINT/SIGTERM take this cleanup path.
The console uses bounded read/select rather than potentially blocking getline
on partial input. SIGKILL cannot execute application cleanup.

## Freshness / validation

Finite decoded joint/IMU samples are copied into a synchronized store. A repeated
or backward tick does not refresh time; uint32 wrap works. Invalid samples are
ignored. Robot tick reset requires re-establishing the receive session.

Last-known feedback is retained but separately labeled FRESH or
STALE_OR_NEVER_RECEIVED, with age in seconds. A wall-clock check runs even if
robot ticks stop. Staleness zeros input, closes sends, joins work and requests
release; recovery does not automatically reacquire ownership.

NaN or +/-Inf on any velocity axis zeros all axes. Finite inputs retain [-1,1]
clamping and the 300 ms command deadman. stop cancels pending mode requests.

## Build / tests

Build configuration: x86, BUILD_SIM=OFF, SEND_REMOTE=OFF, USE_MJCPP=OFF,
BUILD_TESTING=ON. Both clean /tmp build and existing build_offline rebuilt.
rl_deploy and lite3_validation_console were compiled, never executed.

CTest: 3/3 PASS:
- software_velocity_interface_test: clamping, timeout, mode gates, stop,
  non-finite values on each axis, pending mode cancellation, stopped requests.
- control_safety_test: inert SDK, passive startup, stale/frozen/invalid feedback,
  last-known values, repeated acquisition/release, honest ownership status,
  in-flight sends versus release, real state-machine transition gating,
  real RL worker with inert policy, join-before-release, no stale request replay.
- vendor_adapter_test: production adapter compiled against fake Sender/Receiver;
  exactly one receiver startup, no Sender in passive startup, no initialization
  or joint sends during acquire-only, unconfirmed gate, idempotent release.

Inert tests link neither real MotionSDK nor ONNX Runtime. strace network tracing
of both integration tests showed no network calls. Logs:
- build_offline/Testing/Temporary/LastTest.log
- /tmp/lite3_control_safety_network.trace
- /tmp/lite3_adapter_network.trace

Hardware binaries retain repository-local x86 MotionSDK and ONNX Runtime RPATH.
git diff --check passed; policy and stand-trajectory files have no changes.

## Remaining risks / limits

- No physical acquisition, release, stop, posture or ownership validation yet.
- Vendor Receiver auto-starts a detached receive worker and has no stop/join API.
  Static inspection confirms its destructor does not join. It is deliberately
  retained until process exit; callback uses weak feedback storage to avoid a
  destroyed HardwareInterface. Do not repeatedly create hardware sessions in
  one process. Vendor callback registration/decoder synchronization are opaque.
- A hung SDK send or inference can delay cooperative shutdown; there is no
  hard real-time termination guarantee.
- SDK RobotData supplies joint/IMU data, not authoritative battery/fault/posture
  or ownership state. Future acquisition tests require independent passive
  robot-health observation and the original controller/E-stop.
- Console state is the local deployment state, not physical standing.
- Stand/RL on production remain blocked pending a reviewed ownership-confirmation
  mechanism. No automatic confirmation or safety override was added.
