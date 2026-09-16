# Failures and fixes

| Failure/evidence | Implemented response | Proof/remaining limit |
|---|---|---|
| UDP bind EADDRINUSE, multiple/stale receiver sessions | Verify exact owner before launching; use one console/receiver | Current PID 143195 owns 43897; do not launch a second observer |
| `status`/`quit` typed at shell after console exit | Operator commands belong inside console, not bash | Current terminal/session listed in CURRENT_STATUS |
| Startup missing telemetry latched stale abort permanently | Passive startup WAITING_FOR_TELEMETRY -> LOCKED; no active latch until a real control session | Startup regression and multiple passive live startups pass |
| Console could appear unusable amid endless joint-status warnings | Rate-limit unchanged invalid warnings to 1 Hz/state change; maintain rejection every cycle | 1,000-call offline test; passive transcript fell from ~2,986 to 77 lines |
| Acquire once called RobotStateInit/initialized joints | Acquire now only ownership request; no initialization API on transport seam | Fake SDK tests, live acquisition-only remains still |
| Acquisition result confused with confirmed ownership | REQUEST_SENT / OWNERSHIP_UNCONFIRMED; IsControlAcquired stays false | SDK still has no authoritative ack |
| Stand request could open gate before authorized transition | Private supervised permit, OnEnter/preflight before gate; no idle/pending joint packets | Inert state-machine tests; first live stand reached STANDING_UP |
| Release could race SendCmd / worker lifecycle | Send/lifecycle mutexes, atomic abort before next Run, join-before-release, idempotent paths | In-flight/send/signal tests; physical hung-call behavior still unknown |
| NaN/Inf velocities could saturate rather than reject | Nonfinite any axis -> all zeros; finite clamp [-1,1], 300 ms timeout | Input tests; locomotion blocked in current build |
| Feedback fields read from separate packet snapshots | Coherent stand q/dq/tick/IMU snapshot | Inert replay + passive finite/progressing reads; cannot prove physical calibration |
| Float absolute stand clock loses ms resolution at long uptime | Double absolute timestamps | Long-uptime regression passes; not proven as first live abort cause |
| First actual stand aborted with generic `send guard rejected output` | Branch-specific enum, full bounded command/feedback trace, exact entry metadata | Historical root remains unknown; future supervised attempt will identify exact guard |
| Guard diagnostics hid invalid received sample behind last-known values | Preserve invalid raw sample for diagnostics without refreshing eligibility | NaN/Inf rejection tests and valid JSON null representation |
| Command cache could imply send succeeded before SDK returned | Update accepted command after successful transport return; OTHER on throw | Inert transport exception test; return still not robot acceptance |
| Bad resting joint range could be armed then rejected by Idle | Preflight mirrors existing Idle ranges/tolerance and reports offending index/value | FR/HR abnormal-pose tests; no range changes |
| Concern 5 s arm expired during active stand | Inspected: active permit already independent; no timing redesign needed | 4.8 s delayed-start replay passes, active expiry separately tested |
| Suspected missing PreStand/fixed-start trajectory | Existing measured-start preparation confirmed; no extra stage added | Actual StandUpState replay full 3 s path passes |
| Suspected right-leg mapping/offset bug | Did NOT change signs/mapping/limits; repeat normal lying preparation first | Latest values normal and symmetric with unchanged software; posture/startup dependence supported |

## What was not fixed by guessing

- First failed hardware stand's precise rejecting condition remains unknown.
- No complete successful physical stand yet; no RL-zero or walking validation.
- SDK ownership acknowledgment unavailable; no fabricated confirmation.
- Gains Kp100/Kd2.5 and target posture unchanged.
- Existing .35-rad guard was not widened to allow more tracking error.
- No additional PreStand, RobotStateInit, KEEP_STEPPING, packet code guesses,
  firmware edits, network changes, or original-controller reverse engineering.

The recovery report's original NOT_READY posture blocker is historical. After the
normal lying preparation, preflight is OK and a new acquire-only test passed;
the next stand still needs explicit physical operator approval.
