# Supported stand convergence review — NO further hardware test authorized

## Superseding safety update — 2026-09-17

A new supported stand reached `TARGET_REACHED`, then exposed that permit renewal
kept the joint gate open indefinitely. Operator `stop` released successfully.
The handoff branch now imposes an absolute two-second successful-target hold in
the state machine, independent of permit renewal. All 13 offline tests pass. The
new limit has not been hardware-tested. See
`docs/SUPPORTED_STAND_SUCCESS_2026-09-17.md`. The indefinite-hold design below is
retained only as historical rationale and no longer describes the branch tip.

## Latest post-success update — supported hold, explicit stop/release

The operator subsequently requested removal of successful-stand automatic release.
The current build no longer aborts merely because two seconds have elapsed after
TARGET_REACHED. It continues the unchanged final joint target under the unchanged
convergence/finite/tilt/tracking/telemetry guards. The private eight-second permit
is atomically renewed only on fresh, successful monitor updates; expired/cancelled
permits cannot be renewed. Pre-success timing and all failure/stop/release paths
remain unchanged. No RL, velocity, trajectory, gain or network changes were made.

Build passed. Exactly two focused inert tests passed (16.46 s): healthy success
held >8.25 real seconds without auto-release, then explicit stop released; fault
cases covered stop/release, stale/invalid feedback, tilt, tracking, lost convergence,
send-gate failure, shutdown and worker-pause permit expiry. No hardware executable
was launched/restarted and no robot commands were sent. The older running process
does not hot-load this build. Mechanical support remains required because faults
or explicit stop/release can still remove stiffness. Historical statements below
about mandatory two-second successful release are superseded by this section.

## Latest update — operator-approved window implemented and tested offline

The operator explicitly approved the proposed 50 ms RMS-speed plus position-range
criterion after being told that individual samples above .15 rad/s can pass the
window. The sections below this update preserve the earlier diagnosis and review
block as history; their "not implemented" statements no longer describe the build.

Implemented in `state_machine/supervised_stand_monitor.hpp`:

- For each joint, time-weighted RMS of measured velocity over 50 ms <= .15 rad/s.
- Additionally, joint-position range over that window / .05 s <= .15 rad/s.
- RMS squares values, so opposite-sign oscillations cannot cancel.
- Complete progressing window required; >50 ms sample gaps reset it. Repeated
  timestamps do not add evidence. Storage is bounded to 512 samples; overflow
  fails closed. Invalid/nonfinite values still abort, and finite squared overflow
  fails the convergence check.
- This is explicitly a changed convergence-speed definition, NOT the unchanged
  instantaneous .15 rad/s test. Sustained excessive speed remains disqualifying.
- Raw finite-data, tracking .35 rad, final error .08 rad, tilt, .5 s dwell,
  6 s deadline, 2 s observation and 8 s private permit remain unchanged.
- Trajectory, final posture, gains, SDK, ownership, authorization, RL and velocity
  logic were not changed. Existing abort/release behavior was not changed.

Logging now also exports `rms_max_speed_50ms`, `position_range_speed_50ms` and
`speed_window_ready`, alongside raw speed, joint arrays and monitor timers.

### Updated focused results

| Offline case | TARGET_REACHED | Bounded release decision |
|---|---:|---:|
| Recorded physical feedback | 3.51422 s | 5.51436 s |
| Synthetic 25 ms lag / .04 rad knee bias | 3.55 s | 5.56 s |
| Synthetic 75 ms lag / .05 rad knee bias | 3.62 s | 5.63 s |
| Synthetic 150 ms lag / .05 rad knee bias | 3.76 s | 5.77 s |

Recorded replay uses the same data as the previous timeout; the unchanged strict
per-sample definition still has only .252445 s longest dwell. The new replay
release time is counterfactual software output, NOT a newly observed robot event.
No post-release stability can be inferred from this replay.

The supported console rebuilt. Three focused tests passed: stand_once,
stand_convergence_replay, stand_monitor (3643 checks), total .29 s in this run.
Negative tests cover sustained speed, alternating-sign speed, position movement
with false zero velocity, gaps, duplicates, capacity overflow, invalid/overflow
numbers, immediate tilt/tracking faults, stale feedback, operator abort and
clock reversal. Authorization expiry and observation ordering remain covered.

No hardware executable was launched/restarted and no robot command was sent.
The previously running console does NOT hot-load this rebuilt implementation.
The offline convergence fix is ready for a separately approved supported test,
NOT an unsupported standing/hold trial. Support must carry the full robot weight
when the existing release removes stiffness, even on successful completion.

Files changed for this approved step: monitor header, stand diagnostic snapshot
and serialization, focused monitor/replay tests, and this report. Build/test
commands remain the focused commands recorded below.

## Outcome

NOT_READY for another physical stand. The recorded timeout is reproducible. The
unchanged trajectory completes in replay with valid slower measured tracking.
No trajectory, gain, threshold, ownership, MotionSDK, RL or velocity behavior was
changed in this investigation. Only diagnostic metadata and focused tests were
added. No robot commands were sent and the running console was not restarted.

The operator reported that the robot stood and then fell. This supersedes any
earlier assumption that the latest attempt never reached a standing posture.
Physical standing was observed; successful monitor convergence was NOT observed.

## Preserved evidence

Original `/tmp/lite3-stand-trace-143195-353427752151962.jsonl` is preserved as
`docs/handoff_evidence/20260913/supported-stand-timeout.jsonl`.
There are 5,928 SENT records, entry metadata, a supervisor exit event and an end
reason. The trace contains no post-release physical trajectory, so it cannot
prove the exact fall time or exclude other physical factors.

Entry wall time: 353419.749608 seconds (monotonic, not calendar time).
Last sent command: elapsed robot time 5.999 s, wall 353425.749378.
Supervisor abort: wall 353425.750030, about 6.000422 s after entry.
Reason: `convergence deadline`. Private permit had about 1.9996 s remaining.
Thus neither the 5 s unused-authorization deadline nor the 8 s send permit caused
this abort. Release follows the existing shared abort path and can remove joint
stiffness. The reported fall is consistent with that, but causal certainty would
require synchronized physical/post-release observation.

## Proven numerical diagnosis

| Interval | Largest target-position error | Joint | Samples with any abs(measured speed) > .15 rad/s |
|---|---:|---|---:|
| preparation, 0–1.5 s | .074851 rad | 11, HR knee | 1,173 |
| raising, 1.5–3 s | .083109 rad | 11, HR knee | 1,401 |
| final hold, 3–4 s | .052072 rad | 11, HR knee | 13 |
| final hold, 4–5 s | .051996 rad | 11, HR knee | 20 |
| final hold, 5–6 s | .051996 rad | 11, HR knee | 16 |

Motion during the trajectory is expected. During final hold all position errors
were below .08 rad and target velocities were zero. Measured velocity spikes on
49 of 2,966 final-hold samples prevented the required continuous .5 s dwell.
The longest qualifying dwell was only .252445 s. HR HipX (index 9) contributed
35 speed-exceedance samples; its largest final-hold speed was .22289 rad/s.
The largest final-hold joint-position peak-to-peak range was .002289 rad across
three seconds. Final tilt stayed below .008568 rad. Every instantaneous position
tracking error was far below the .35 rad abort bound.

**PROVEN:** the strict per-sample speed/dwell condition, not final position error,
prevented TARGET_REACHED and led to the deadline. **INFERENCE:** velocity noise or
small vibration explains the spikes. Position stability supports this but does
not prove that the velocity samples are erroneous. By the existing definition,
the recorded response is not a valid converged response.

## Timing and local reference comparison

- Stage 1: 1.5 s, measured entry q/dq to the existing ready posture.
- Stage 2: 1.5 s, height .12 → .33 m; fixed final joint posture unchanged.
- Final target: 3.0 s after captured entry timestamp; target dq becomes zero.
- Stage transition remains time-based, not measured-ready-pose convergence.
- `ControlParameters::stand_duration_` is 1.5 s in
  `state_machine/parameters/control_parameters.h`.
- The local vendor `third_party/Lite3_MotionSDK/src/motionexample.cpp` implements
  PreStandUp over 1.0 s and StandUp over 1.5 s, but uses different joint targets
  and gains. That is a reference, not proof of safety on this supported setup.
- The recorded target tracking and completed final hold do not support slowing
  or replacing this trajectory as the fix for this specific timeout.

## Exact monitor/control timing — unchanged

`state_machine/supervised_stand_monitor.hpp` requires ALL of:
fresh finite feedback; final target valid; each joint error <= .08 rad;
each measured abs(dq) <= .15 rad/s; each target abs(dq) <= .001 rad/s;
abs(roll/pitch) <= .35 rad; roll/pitch change from dwell anchor <= .03 rad;
and .5 s continuous qualifying dwell with progressing feedback.

The 6 s wall-clock deadline starts in ProcessOnce after StandUpState::OnEnter,
immediately before opening the supervised send gate. The .5 s dwell starts only
when all convergence conditions hold. The 2 s observation starts only after
TARGET_REACHED. Observation completion intentionally takes the release path.

It would be incorrect to claim release can never occur before convergence:
abort/fault/timeout MUST still release through the existing reviewed path.
What is proven is that *successful-observation completion* does not precede
convergence. Synthetic replay explicitly tests this distinction.

Unused/pending authorization is limited to 5 s. After actual stand entry,
stand_armed_ and stand_pending_ are false; that timer no longer aborts active
stand. The independent 6 s convergence, 2 s observation and 8 s permit limits
remain in force. The stand_once regression test covers active stand crossing the
old unused-authorization deadline without an expiry abort.

## Focused replay results

Actual production monitor + trajectory/state machine, injected inert SDK only.
Synthetic plant is a first-order joint response, NOT validated robot dynamics.

| Profile | TARGET_REACHED | Release | Max error |
|---|---:|---:|---:|
| lag 25 ms, knee bias .04 rad | 3.52 s | 5.53 s | .078203 rad |
| lag 75 ms, knee bias .05 rad | 3.58 s | 5.59 s | .150135 rad |
| lag 150 ms, knee bias .05 rad | 3.71 s | 5.72 s | .239154 rad |
| recorded physical feedback | never | deadline at ~6 s | .083109 rad |

These demonstrate mutually achievable timings and valid slower responses, NOT
that the next physical stand will converge. Recorded replay uses command-loop
samples and the previous sent target; it cannot reproduce unsampled receiver
updates between those records. The final-hold failure is insensitive to that
one-cycle difference because targets are constant.

## Changes implemented (diagnostics only)

- Monitor diagnostics expose wall elapsed, dwell timer, observation timer,
  raw maximum speed, candidate/final-target/new-feedback flags and reason.
- StateMachine copies that snapshot to the existing buffered diagnostic stream.
- RobotInterface/HardwareInterface carry logging-only metadata; each event now
  preserves its exact internal cause (`event_detail`), not merely STATE_CHANGED.
- Existing arrays target[12], target_velocity[12], position[12], velocity[12],
  torque[12], error[12], largest-error joint, IMU and phase remain present.
- Monitor metadata describes the check immediately preceding the send; it has
  its own wall timestamp. Receiver data may progress before the send snapshot.
- No hot-loop file write added. Records are flushed after abort/release as before.

## Proposed change NOT implemented

A 50 ms time-weighted RMS measured-speed criterion plus a 50 ms joint-position
range/speed check, both using .15 rad/s, could reject sustained motion while
avoiding reset on isolated spikes. Exploratory recorded-data calculations gave
sampled-window RMS <= .08355 rad/s during settled hold. This is only a candidate.

Safety review rejected implementing it because it changes the meaning of the
per-sample guard and can accept instantaneous samples over .15 rad/s. No workaround,
filter, grace period, raised threshold or extended deadline has been installed.
Explicit approval is required for this safety-semantic change, followed by focused
negative tests for sustained motion, oscillation, telemetry gaps and invalid data.

Even if convergence detection is improved, the existing successful-test release
can remove stiffness after two seconds. A future supported test needs a fixture
that safely bears full robot weight when stiffness is removed. Do not mistake
TARGET_REACHED for indefinite position hold or a verified safe ownership handoff.

## Build and tests

```
cmake -S . -B build_supported_stand
cmake --build build_supported_stand --target lite3_validation_console stand_convergence_replay_test stand_monitor_test stand_once_test -j2
ctest --test-dir build_supported_stand -R '^(stand_convergence_replay_test|stand_monitor_test|stand_once_test)$' --output-on-failure
```

Build passed. Three focused tests passed (0.20 s total in this run). The new
recorded replay deliberately asserts the existing timeout: a passing regression
test is NOT a claim that hardware failure was fixed. No live control executable
was launched; no robot commands were sent. `git diff --check` passed.

Confidence in identifying the recorded timeout trigger: approximately 95%
(engineering judgment, not a statistical safety guarantee). Confidence in next
hardware stand/release safety cannot responsibly be quantified from these replays.
