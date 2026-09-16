# Next steps — one supervised physical action at a time

## Current next milestone — after vendor-gait forward success, 2026-09-14

STOP before another live command. External forward through the existing `jy_exe`
manual locomotion path is physically proven once; an identical repeat completed
its bounded send/neutral sequence safely. The next useful milestone is **one
bounded backward test**, not a longer forward run, continuous teleoperation,
lateral/yaw, ROS2, or a return to direct ONNX control.

The documentation-time read-only preflight passed: ports free, route correct,
packet self-test passed with zero sends, fresh `6/0/0` telemetry and battery 53%.
Therefore the software is ready to prepare the separate bounded backward test.
Because telemetry/state are time-varying, repeat preflight immediately before it.

Required read-only preflight for every subsequent bounded test:

1. Identify all local processes that could send commands or own UDP 43897.
   Do not kill a PID by remembered number; inspect executable/cmdline/socket.
2. If a known test process is active, have the supervised operator terminate it
   through its clean shutdown path. Confirm UDP 43897 is free.
3. Confirm `ip -4 route get 192.168.1.120` selects `enp3s0` and source
   `192.168.1.102`; verify reachability.
4. Bind receive-only telemetry, require a fresh valid RobotState, basic state 6,
   finite values, and adequate current battery. Last-known data is insufficient.
5. Run packet self-tests/dry-run. Require zero network calls in dry-run and the
   exact full wire command—not a bare low-16 code.
6. Human confirms clear floor/legs, original controller/E-stop available, and
   explicitly authorizes exactly one bounded test. No automatic retry.

The current forward tool is intentionally fixed at `+0.10` for 0.30 s and must
not be repurposed silently for backward. Prepare a separate reviewed bounded
negative-value profile first, proving the negative raw conversion and exact
packet bytes offline. Preserve the same 1.0 s neutral before, >=1.0 s neutral
after, exit-neutral redundancy, state-6/fresh-telemetry/battery gates, exclusive
telemetry bind, conflict detection, and explicit confirmation token.

Abort on unexpected direction, instability, excessive tilt, telemetry loss,
state change, network error, or inability to stop. Release/E-stop takes priority
over debugging. Do not broaden to ROS2 or autonomous control until forward and
backward stop behavior have separate supervised evidence and a higher-level
watchdog/command timeout design has been reviewed.

### DO NOT REDISCOVER / DO NOT RETRY

- `/dev/ttyS6` as controller input: disproven; it is the Yesense IMU channel.
- ttyS1/ttyS3/ttyS6 axis transport: no controller axes were found there.
- legacy Motion Host ComplexCMD codes 320/321/325: ignored for directional
  locomotion by this `jy_exe` build; do not retry.
- direct ONNX/MotionSDK joint locomotion as the pilot path: paused after repeated
  lean/step/fall or non-translation outcomes. Preserve it for research only.
- controller axes over the persistent SSH connection from 192.168.2.101:
  unproven and unsupported by the captures; do not build around it.
- visible axis UDP from 192.168.2.101: source-filtered captures showed only the
  12-byte `0x21040001` heartbeat at about 2 Hz, not axis-bearing packets.
- bare wire code `0x0130`: rejected by ParseCommand's category check. The proven
  forward wire code is `0x21010130`.

Historical next-step sections below are retained as evidence and are superseded
by this section.

## Current next milestone — after real-hardware RL-zero lifecycle success

Stop here. Long hold, five-second RL-zero, and explicit stop/release from
RL-zero passed on real hardware (E8–E10). The robot is released/lying and the
console is passive. Do not repeat these tests automatically.

The next milestone would be the first bounded nonzero normalized policy input.
It requires a separate design/review and explicit authorization. Current console
continues to reject unrestricted `rl` and `velocity`; `rl_zero_once` permanently
locks its process input to zero. Do not weaken that lock, reuse zero-test approval,
or interpret normalized input as m/s. Define a tiny command, short wall-clock
duration, immediate zero/stop, tracking/tilt/telemetry guards, mechanical support,
and operator confirmation before implementing or testing it.

## Current next milestone — after controlled release success, 2026-09-13

E7 proves one operator-observed supported return to lying after explicit release.
Next requested test: stand hold -> RL with normalized forward/lateral/yaw=0.
**Software prepared after explicit approval; hardware RL remains UNTESTED.**
New build adds `rl_zero_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED` only after
fresh converged supported hold. `rl` and `velocity` STILL abort: do not use them.
Separate five-second non-renewable permit; permanently zero-only input; existing
stop/join/release path. Deadline releases control and may remove support.

Next operator action: `status` in the existing console, confirm released/zero/gate
closed before `quit` and launching the new build. Do not restart an active hold.
Then, separately: status -> acquire -> status -> stand_once confirmation token ->
wait for TARGET_REACHED/physical stable hold -> status -> rl_zero_once confirmation
token. Observe only; stop immediately for unexpected motion, tilt, stale telemetry,
fault, tracking failure, or uncertain control. Mechanical support/E-stop required
through release; no retry, walking or nonzero command. Zero policy input does not
guarantee physical stillness. No hardware action was executed during preparation.

## Historical next milestone — superseded by E7

Computer-commanded supported stand is now **PROVEN ON REAL HARDWARE** (E6 in
EXPERIMENTS.md). Do not repeat stand or follow the older startup sequence below
automatically. The next milestone is **controlled return-to-rest / stop/release
validation** under explicit supervision and mechanical support. Determine the
current live status before any action; release can remove stiffness and has not
yet been physically validated as a safe return-to-rest. No RL or walking next.

The instructions below are historical stand-preparation notes, not authorization
to act on their old PID/session or superseded two-second release behavior.

## Resume the CURRENT session

Read CURRENT_STATUS first. At handoff console PID 143195/session 47145 is running,
acquisition REQUEST_SENT, ownership UNCONFIRMED, stand LOCKED, gate closed, input
zero. The user confirmed no physical motion after acquire. No stand authorization
or stand has followed. **Do not blindly acquire again or launch another console.**

1. Read `status` in that console. Require fresh telemetry, preflight OK, no active
   abort, zero velocity and gate closed. If state differs, reassess; do not force it.
2. Human confirms sufficient battery/health, normal lying posture, mechanical
   support, independent E-stop and people clear of legs. Do not move energized
   legs by hand. Laptop telemetry cannot replace this confirmation.
3. Obtain explicit approval for ONE stand attempt BEFORE opening the 5 s arm window.
4. In the existing console, issue:

   `authorize_stand SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`

5. Immediately `status`; require ARMED, valid preflight, gate still closed, velocity
   zero. Then, only under the explicit approval, `stand` within the 5 s window.
   Do not spend another chat round-trip waiting while armed. If approval has not
   been given, do not arm yet. Expiry is a safety event, not permission to bypass.
6. ONE attempt. No RL, velocity, walking or automatic retry. Observe physically
   and capture transcript + `/tmp/lite3-stand-trace-*.jsonl`.
7. Stop and wait for the operator's physical result after stand. Existing monitor
   may automatically abort/release at failure or after bounded target observation.

## Fresh-session sequence (only if existing session has safely ended)

Inspect port owner first; never kill arbitrary listeners. If restarting is needed,
coordinate with the operator: an outstanding control request requires a reviewed
safe stop/release, and release may remove stiffness. Do not use SIGKILL casually.

```sh
cd /home/abx/Lite3_rl_deploy/build_supported_stand
script -q -f -e -c './lite3_validation_console' "/tmp/lite3-stand-$(date +%Y%m%d-%H%M%S).log"
```

Inside console (NOT shell), staged rather than pasted as an unattended batch:

```
status
acquire
status
authorize_stand SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED
status
stand
```

After acquire, STOP for physical confirmation of no movement before authorization.
AcquireControl must never call RobotStateInit. No mode tricks or ownership bypass.

## During and after the single stand

Expected: measured-start preparation ~1.5 s, raising ~1.5 s, monitored convergence.
No translation/yaw requested. TARGET_REACHED requires measured joint/IMU checks,
but does not prove unsupported balance. The monitor permits only bounded observation
then requests release; support must remain in place throughout.

Abort for violent/unexpected/asymmetric motion, translation, excessive tilt,
stale/invalid telemetry, severe tracking, guard rejection, process failure,
unexpected send-gate state, poor battery/health, inability to stop/release or
uncertain control situation. Physical danger -> independent E-stop first.

Console `stop` invokes the integrated shared abort/release path. `release`,
SIGINT/SIGTERM also use it. Neither promises a posture hold. Release waits for
an already in-flight send; do not approach to catch a collapsing robot.
Use `status` afterward: zero input, closed gate, request no longer pending if
return call completed; actual ownership return remains unconfirmed.

Record STAND_TEST_COMPLETE only after the single actual attempt, with:
physical outcome (smooth stand/partial/still/unexpected), state trace, exact guard,
target-versus-measured response, IMU, release result, and one next decision.
If it fails, analyze the precise trace—no automatic retry or speed/gain changes.

## Build/test commands (offline only; not needed merely to resume)

```sh
cmake -S /home/abx/Lite3_rl_deploy -B /home/abx/Lite3_rl_deploy/build_supported_stand \
  -DBUILD_SIM=OFF -DBUILD_PLATFORM=x86 -DSEND_REMOTE=OFF -DBUILD_TESTING=ON
cmake --build /home/abx/Lite3_rl_deploy/build_supported_stand \
  --target lite3_validation_console lite3_passive_stand_observer \
  stand_recovery_test control_safety_test vendor_adapter_test -j2
ctest --test-dir /home/abx/Lite3_rl_deploy/build_supported_stand \
  -R '^(stand_recovery_test|control_safety_test|vendor_adapter_test|software_velocity_interface_test|stand_monitor_test)$' \
  --output-on-failure
/home/abx/Lite3_rl_deploy/build_supported_stand/control_safety_test --startup-only
```

Flags: BUILD_SIM=OFF compiles hardware interface (does NOT run it), platform x86
selects ABI, SEND_REMOTE=OFF prevents deploy hooks, BUILD_TESTING=ON enables inert
tests, --target limits builds, -j2 limits compilation parallelism; CTest -R selects
focused tests. Do not run generic `rl_deploy` for the supported stand experiment.

Passive observer command, ONLY when telemetry port is free and passive observation
is intended: `./lite3_passive_stand_observer` from build_supported_stand. It runs
35 s, cannot send, and writes `/tmp/lite3-stand-passive-observation.csv` (archive
that file first if preserving earlier data). Never compete with the current console.

## After successful stand — separate, newly authorized work

1. Review synchronized physical trace, tracking margin, convergence, and release.
   Do not mark a mock TARGET_REACHED as physical stand success.
2. Resolve any remaining supervised stop/release uncertainty. Preserve stand-only
   build/evidence; commit reviewed source/docs rather than generated binaries.
3. Design/review a separate RL-zero authorization stage; the current StateMachine
   rejects RL and all nonzero velocity. Do not simply remove those blocks.
4. Only after explicit RL-zero hardware validation, plan one tiny bounded normalized
   forward test with timeout/stop/release; +0.05 is not a verified m/s speed.

## Next ROS2 integration step (NOT part of current live test)

First implement an OFFLINE/DRY-RUN ROS2 Jazzy adapter around the existing software
command abstraction: bounded velocity input, freshness watchdog, explicit lifecycle,
status diagnostics and single-owner arbitration. Keep its robot-send gate disabled.
If using `/cmd_vel` (m/s, rad/s), do not pass values directly into normalized policy
axes until the policy's physical scaling is verified. Require safety-reviewed
stand/RL authorization; a Twist message must never acquire ownership or stand.
Then test against inert transport before any robot integration. Nav2 needs separate
real odometry/localization/TF validation; stand alone proves none of these.
