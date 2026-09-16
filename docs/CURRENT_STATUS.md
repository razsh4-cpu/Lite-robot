# Current status — authoritative handoff snapshot

## Latest status — vendor high-level forward path proven, 2026-09-14

Latest read-only handoff preflight after documentation: no real matching control
process was present (the only `pgrep` match was its own inspection shell), UDP
43893/43897 had no local owner, route selected `enp3s0` source 192.168.1.102,
packet self-test passed with `ROBOT_PACKETS_SENT=0`, and a fresh passive sample
reported `basic/gait/motion=6/0/0`, battery 53%. This is a point-in-time snapshot,
not permission to skip preflight before a later command.

The current pilot control path is the locomotion controller already running in
the robot's `jy_exe`, not direct ONNX joint deployment. A bounded external
forward test succeeded physically on real hardware at approximately 20:08
+03:00. An identical repeat at approximately 20:09 completed safely with healthy
post-state; its physical translation was not separately reported. Both used full
wire command `0x21010130`, raw signed value `9174`, which the firmware maps to
`ControlCommands.left_axis_y ~= +0.099985`.

Preflight before the first test: direct Ethernet route through `enp3s0` from
192.168.1.102 to 192.168.1.120; fresh RobotState `6/0/0`; battery 57%; no
competing control process. Preflight before the repeat: state 6, battery 56%,
fresh telemetry, no conflict. Each run transmitted exactly 20 neutral cycles,
six forward cycles over 0.30 s, 20 post-neutral cycles, and five exit-neutral
cycles. Post-test RobotState was `6/0/0`. The operator explicitly reported
physical success after the first test.

The first old validation console (PID 33723, started from
`build_supported_stand/lite3_validation_console`) had occupied UDP 43897. After
explicit operator authorization it was stopped using SIGINT, its process exited,
and `ss` showed 43897 free. It was not killed blindly and is no longer a blocker.

Current bounded tool (outside this Git repository):
`/home/abx/lite3_uart_analysis/lite3_manual_axis_forward_probe.py`.
It reuses the existing Motion Host telemetry decoder from
`/home/abx/emos-plugin-lite3/lite3_plugin/{protocol.py,codecs.py}` without loading
the optional full plugin. Its live mode requires two explicit arguments, refuses
known competing control processes, binds telemetry exclusively, requires fresh
state 6 and battery >=25%, limits forward to +0.10 for 0.30 s, and always sends
redundant neutral on exit. Dry-run and byte tests pass; dry-run `strace` showed no
network call. No automatic retry exists.

### Proven versus paused

- **Proven hardware:** Ethernet/UDP feedback, MotionSDK telemetry, acquisition,
  supervised stand, stable hold, explicit release, bounded RL-zero, original
  controller gait, and now external `jy_exe` manual-axis forward locomotion.
- **Proven static path:** UDP 43893 -> HeartbeatListener -> CommandList ->
  Controller::ParseCommand -> KineticsDeduce/ControlCommands -> vendor manual
  motion. `0x21010130` writes left_axis_y and sets is_joystick_connect.
- **Offline/source evidence:** lateral full code `0x21010131` writes left_axis_x;
  yaw full code `0x21010135` writes right_axis_x. These have not yet been used in
  a nonzero hardware test.
- **Paused pilot path:** direct ONNX/RL joint locomotion. It proved stand/RL-zero,
  but forward attempts did not yield reliable useful translation. The pre-April
  stack stepped and was more robust in simulation, but it is not the selected
  pilot locomotion path.
- **Unknown:** raw physical transport used by the original handheld controller
  before values reach `jy_exe`; no explicit source/ownership telemetry field was
  found. This no longer blocks bounded external manual-axis control.

Full evidence and disassembly addresses are recorded in
`HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md`. Older sections below are
historical snapshots and may name PIDs or next steps that are no longer current.

## Latest hardware state — 2026-09-13 22:30 +03:00

**ZERO-VELOCITY RL LIFECYCLE = PROVEN ON REAL HARDWARE**, based on console traces
and operator physical confirmation. Current PID 160982 uses the same on-disk
binary (SHA-256 `4f0b1d58f6953bffb67f01f5e3afec749f92b31687e01c1fdf53622317a9b4fe`).
After the final explicit-stop test it reported state=0, RELEASE_REQUESTED,
abort_reason=`stop requested`, acquisition/ownership=NOT_REQUESTED,
joint_send_enabled=0, fresh telemetry, and velocity 0,0,0. Operator confirmed
stable RL-zero behavior and safe physical return to lying. The console remains
running passively; do not duplicate it or assume future telemetry freshness.

Real-hardware results:

1. Long supported hold: TARGET_REACHED for approximately 203 s, followed by
   explicit release and safe return to lying. Retained final 24.3 s had max
   RMS speed 0.0696 rad/s, position-range speed 0.0214 rad/s-equivalent,
   tracking error 0.0526 rad, stable roll/pitch, and no 0.15 RMS violation.
   Trace: `/tmp/lite3-stand-trace-160127-362598751481347.jsonl`.
2. RL-zero deadline: 5.0000066 s, 412/412 policy starts/completions (~82 Hz),
   all recorded policy commands 0,0,0, max tracking error 0.1939 rad; operator
   confirmed stable standing until planned release and safe return to lying.
   Trace: `/tmp/lite3-stand-trace-160982-362946789885257.jsonl`.
3. RL-zero explicit stop: 1.4127 s, 117/117 policy starts/completions, all
   recorded commands 0,0,0, max tracking error 0.2017 rad. Last joint send was
   about 3.05 ms before the recorded stop event; gate then closed, worker joined,
   release was requested, passive telemetry continued, and operator confirmed
   stable return to lying. Trace:
   `/tmp/lite3-stand-trace-160982-363434026878013.jsonl`.

Two concrete fixes were validated en route: an isolated 4.12 ms FR HipY velocity
burst no longer aborts a hold unless an RMS-only violation persists 50 ms (the
0.15 rad/s threshold was not raised); completed abort/release is idempotent and
cannot re-stop the reset input interface before a subsequent acquisition.

No unrestricted RL or nonzero velocity was enabled or tested. Ownership remains
unconfirmed because MotionSDK supplies no authoritative acknowledgment. Next
work must separately design and review the first bounded nonzero-input test; it
is not authorized by these zero-input results.

## RL-zero preparation — 2026-09-13, offline only

User approved the distinct zero-only RL transition. New operator command:
`rl_zero_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`.
Requires fresh/finite stationary preflight, valid active acquisition request,
TARGET_REACHED hold rechecked immediately, valid stand permit, and open stand gate.
Transition closes gate -> exits stand -> locks input zero -> enters unchanged RL
worker -> opens separate RLZeroPermit -> next fresh tick supplies first observation.
Ownership remains UNCONFIRMED; generic RL/velocity commands remain blocked.

RLZeroPermit is non-renewable: five seconds maximum; 300 ms policy-send silence
also invalidates it. Stop/release/signal, stale/invalid feedback, tilt >0.35 rad,
tracking error >0.35 rad, invalid output or worker failure abort via the existing
gate-close -> worker join -> ownership-return path. End of five-second test also
releases: support must remain in place. Stand trajectory/gains/guards, policy,
packet encoding and networking were not changed. Policy still uses its EXISTING
Kp=30/Kd=1 (stand Kp=100/Kd=2.5); zero normalized input is not zero joint effort
and does not promise physical stillness or support equivalent to stand hold.

Built supported console and `rl_zero_test`; exactly one focused CTest suite passed
(1.25 s). It uses real RL worker lifecycle, inert SDK transport and mocked safe
policy; checks rejected entry, one-time transition, permanent zero lock, fault,
stop/release/shutdown, timeout, worker termination and continuing passive feedback.
One actual unchanged ONNX zero-input inference at final stand posture was finite:
max initial target error 0.0825157 rad (<0.35). This is not a dynamics validation.
Network syscall trace `/tmp/lite3-rl-zero-offline-network.log` contains no
socket/connect/sendto/sendmsg calls. No robot command or live executable was run.
Console SHA256: `8f9c9f152aa0c6eeb24b145de954b243ae3f760dbf1d38bee9a6723fdecd1fec`.
An already running old console was NOT restarted and does NOT gain the new command.

Build: `cmake --build build_supported_stand --target lite3_validation_console rl_zero_test -j2`.
Test: `ctest --test-dir build_supported_stand -R '^rl_zero_test$' --output-on-failure`.
Next: operator checks released/zero/closed state before exiting the old console,
launches new build, then one action at a time: status -> acquire -> status ->
stand_once token -> wait for supported stable TARGET_REACHED -> status ->
rl_zero_once token -> observe at zero -> explicit stop/release (or 5 s deadline).
No automatic live sequence; no walking/nonzero request.

## Latest result — controlled release, 2026-09-13

**CONTROLLED RELEASE = SUCCESS ON REAL HARDWARE**, per the operator's report.
Robot held stand; operator issued `release`; joint_send_enabled became 0,
acquisition became NOT_REQUESTED, telemetry remained fresh, and robot returned
to lying as intended. Exact physical event time was not supplied. Ownership
return still has no authoritative SDK acknowledgement. This is one successful
supported test, not proof of safe release under every posture/failure condition.

Trace: `/tmp/lite3-stand-trace-152452-358842653354612.jsonl` ends with
`end_reason="stop requested"`, consistent with console release calling stop first.
It retained 24000 records and dropped 775334; it cannot provide a complete late
release joint/IMU trace. Physical return and fresh post-release state are operator
evidence. Build/provenance remain those in the stand milestone below.

**Historical pre-implementation RL readiness: BLOCKED by intended stand-only gates.**
`StateMachine::RequestRLControl()` returns false; console `rl`/`velocity` calls
StopVelocity. Active stand only runs StandUpState, and the private permit is
stand-only. The input interface has a zero-initializing RL request and 300 ms
velocity timeout, but that does not authorize a production RL transition or
permanently constrain RL to zero. Zero policy input still generates joint commands
and does not guarantee physical stillness. No production change, hardware command,
or RL test was performed during this readiness check. Separate focused zero-only
RL authorization/transition work is needed before a live test can be offered.

## Latest milestone — 2026-09-13, documented at 21:00 +03:00

**REAL SUPPORTED STAND TEST = SUCCESS. Computer-commanded supported stand:
PROVEN ON REAL HARDWARE, from the operator's explicit physical observation.**
Command: `stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`.
Robot reached standing posture, remained standing, and did not auto-release.

Active console observed read-only: PID 152452, pts/0, started **20:54:10 +03:00**,
`/home/abx/Lite3_rl_deploy/build_supported_stand/lite3_validation_console`.
Its executable hash matches the on-disk build:
`a7486dfeaed05a883444a92ca9332fea049dbe276245a21f2446b0ec1fdf1372`.
Build mtime: **20:46:57 +03:00**. Branch `main`, base commit
`c2432945161d38fec8633a997ce5f9f0dc8c5ec2`, plus uncommitted changes.
The exact stand-command timestamp and live status fields were not captured here;
do not substitute process start time for the stand time or infer current freshness.

Success-enabling fixes: `stand_once` authorization/request race removal;
50 ms RMS-speed/position-range convergence; successful-hold permit renewal and
removal of two-second auto-release. Trajectory/gains were unchanged by these fixes.
Authoritative SDK ownership acknowledgement remains unavailable.

Success evidence/log limitations and exact known sequence: **E6 in EXPERIMENTS.md**.
Next milestone: **controlled return-to-rest / stop/release validation**, supervised
and mechanically supported. Stand success does not prove a safe release, walking
or RL. No robot commands were sent while recording this milestone.

## Historical snapshot — superseded operational state below

Recorded 2026-09-13 around 19:28–19:29 +03:00 (Asia/Jerusalem).
This is a snapshot, not a continuing freshness guarantee. Read fresh status before
any live action. Earlier implementation/audit documents describe earlier phases;
this document supersedes their obsolete readiness/ownership statements.

## Immediate operational state

The normal-lying passive check PASSED. The operator then explicitly requested
`acquire`. One 12-byte SDK ownership request was transmitted; NO joint packet,
stand authorization, stand, RL or velocity request followed. The operator answered
yes when asked whether the robot remained completely still.

Latest status sampled during handoff:

```
state=0 state_source=LOCAL_DEPLOY_STATE_MACHINE
stand_test=LOCKED abort_reason=[] preflight=[OK]
acquisition=REQUEST_SENT ownership=OWNERSHIP_UNCONFIRMED
telemetry=FRESH feedback_age_s=0.002396
joint_send_enabled=0 forward=0 lateral=0 yaw=0
```

`state=0` is LOCAL deployment Idle/WaitingForStand, not Motion Host RobotState
basic-state 0. These state spaces must not be conflated. Actual SDK ownership has
no authoritative acknowledgment. Request sent is not proof of ownership acquired.

The user has NOT yet approved the new stand attempt. The last assistant asked
for `STAND` only when support, E-stop and clear legs are confirmed. A subsequent
request asked for this handoff instead; do not treat that as stand authorization.

## Running session — do not duplicate

- Console: PID **143195**, TTY `pts/4`, `./lite3_validation_console`.
- Parent `script`: PID **143194**, TTY `pts/1`.
- Parent strace: PID **143187**.
- CWD: `/home/abx/Lite3_rl_deploy/build_supported_stand`.
- UDP `0.0.0.0:43897`: console PID 143195, FD 3.
- Codex terminal session ID at handoff: **47145** (may not survive a new session).
- Transcript: `/tmp/lite3-lying-check.u8qXO2/console.log`.
- Transmission audit: `/tmp/lite3-lying-check.u8qXO2/console-network.log`.
- Old shell wrappers 124617/124618 mention a previous console in their command
  lines but are NOT extra running validation executables. Inspect executable/PID
  and socket ownership, not substring count, before declaring a conflict.

Existing run command:

```sh
strace -f -e trace=sendto,sendmsg,sendmmsg,connect \
  -o /tmp/lite3-lying-check.u8qXO2/console-network.log \
  script -q -f -e -c './lite3_validation_console' \
  /tmp/lite3-lying-check.u8qXO2/console.log
```

Do not blindly write to an old PID/FD in a new session. If terminal ownership is
unavailable, have the physical operator locate the current console. Do not kill
or restart it solely for convenience while an ownership request is outstanding.

## Architecture

Current permitted physical test path:

```
operator console -> StateMachine -> SoftwareVelocityInterface/UserCommand
   -> Idle preflight -> private stand-only permit -> StandUpState
   -> HardwareInterface guard -> MotionSdkTransport -> Sender::SendCmd -> Lite3
```

Passive path:

```
Lite3 UDP :43897 -> vendor Receiver, code 0x0906 -> RobotData joints/IMU
 -> synchronized finite/progressing feedback store -> preflight/stand monitor
```

Future locomotion path (NOT enabled/physically proven):
software normalized input -> UserCommand -> RLControlStateONNX -> unchanged
ONNX policy -> 12-joint command -> guarded MotionSDK transport -> robot.
The application API is high-level; MotionSDK underneath is low-level joint control.
The stand trajectory itself does NOT use RL. Constructor model loading/tests do
not mean RLControlMode or the policy-control worker has started.

External x86 Ubuntu host: Ethernet enp3s0, previously verified 192.168.1.102/24.
Robot: 192.168.1.120. SDK sender port 43893, feedback port 43897.
No ROS2/Foxy/drdds/onboard installation is needed for this current C++ path.
Do not substitute the failed high-level Motion Host 320/321/325 path.

## Current measurements and posture interpretation

After operator-confirmed battery reconnect/normal startup/normal lying posture:
35 s passive observation: 34,999 callbacks (~999.968 Hz), 3,499 fresh observations
plus one receiver-startup sample. Maximum fresh age 0.00163351 s. All sampled
joints/IMU finite; largest sampled joint change 0.00083924 rad. Feedback advances.

Representative pre-acquisition joint positions, radians, HipX/HipY/Knee per leg:

| Leg | HipX | HipY | Knee |
|---|---:|---:|---:|
| FL | -0.446739 | -1.160430 | 2.739110 |
| FR | +0.435899 | -1.163279 | 2.741892 |
| HL | -0.445207 | -1.149775 | 2.745257 |
| HR | +0.441011 | -1.147867 | 2.747190 |

Sample roll/pitch: +0.001891/-0.003697 rad; observation maxima approximately
0.002617/0.003895 rad absolute. Preflight remained eligible at the sampled statuses.
Live hardware may change after this snapshot; do not act on cached measurements.

HipY comparison (indices 1/4/7/10):

| Index | Earlier non-ideal posture | Normal lying posture |
|---|---:|---:|
| 1 FL | +0.415 | -1.1604 |
| 4 FR | +2.506 | -1.1633 |
| 7 HL | -0.102 | -1.1498 |
| 10 HR | +1.462 | -1.1479 |

No software mapping/sign/offset/limit change occurred between observations.
The range rejection was posture/startup dependent, not evidence requiring a
mapping fix. Because battery restart and physical posture both changed, their
individual causal contributions cannot be isolated. This is NOT proof of every
physical calibration convention. All current readings pass unchanged limits.

Battery percentage and comprehensive fault/protection state are NOT supplied by
this MotionSDK RobotData stream. The operator must independently confirm battery
and health before actuation. Do not claim a numerical battery level from this log.

## Repository identity and exact diff summary

Path `/home/abx/Lite3_rl_deploy`; branch **main**; base commit
`c2432945161d38fec8633a997ce5f9f0dc8c5ec2`.
Origin: `https://github.com/DeepRoboticsLab/Lite3_rl_deploy.git`.
No commit/staging/reset was performed during handoff. Staged diff is empty.

Exact tracked `git diff --numstat` at handoff (unchanged by new untracked docs):

```
70   2   CMakeLists.txt
2    1   interface/CMakeLists.txt
321  89  interface/robot/hardware/hardware_interface.hpp
33   0   interface/robot/robot_interface.h
13   2   main.cpp
12   2   state_machine/idle_state.hpp
40   17  state_machine/rl_control_state_onnx.hpp
7    4   state_machine/standup_state.hpp
339  31  state_machine/state_machine.hpp
9 files changed, 837 insertions(+), 148 deletions(-)
```

Important UNTRACKED sources (not included in that diff statistic):

```
interface/robot/hardware/motion_sdk_transport.cpp
interface/robot/hardware/motion_sdk_transport.hpp
interface/robot/stand_diagnostics.hpp
interface/robot/stand_only_permit.hpp
interface/user_command/software_velocity_interface.hpp
state_machine/supervised_stand_monitor.hpp
tools/lite3_passive_stand_observer.cpp
tools/lite3_validation_console.cpp
tools/stand_signal.hpp
tests/control_safety_test.cpp
tests/fake_sdk/receiver.h
tests/fake_sdk/sender.h
tests/software_velocity_interface_test.cpp
tests/stand_monitor_candidate.hpp
tests/stand_monitor_candidate_test.cpp
tests/stand_recovery_test.cpp
tests/supervised_stand_review_model.hpp
tests/supervised_stand_review_test.cpp
tests/vendor_adapter_test.cpp
```

`build_offline/`, `build_supported_stand/`, all `docs/`, and `PROGRESS.md` are also
untracked. Build directories contain generated artifacts, not a clean source
commit. Documentation handoff adds the six requested docs/updates, PROGRESS.md,
and evidence snapshots. `git diff` alone omits all these essential untracked files.

ONNX SHA256 (unchanged):
`efa6581d314d8c0442881453d39fc082c09b28bbaa3029d328fcd61fa25b57c7`.

## Read next

[Experiments/proof limits](EXPERIMENTS.md), [safety decisions](DECISIONS.md),
[fixes](FAILURES_AND_FIXES.md), [operator sequence](NEXT_STEPS.md).
Historical `ACQUISITION_ONLY_SAFETY_REVIEW.md` and `SUPPORTED_STAND_TEST.md` have
obsolete statements such as "hardware never run" or "stand blocked pending
ownership confirmation"; use this handoff for current state and the implemented
explicit supervised exception for stand only.
