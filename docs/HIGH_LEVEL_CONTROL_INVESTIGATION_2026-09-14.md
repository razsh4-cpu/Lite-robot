# Lite3 high-level control investigation — 2026-09-14

This is the durable handoff for the path from an external x86 laptop into the
Lite3's existing vendor locomotion controller. It separates observed facts,
static evidence, historical failures, and untested hypotheses.

## Executive result

**PROVEN ON REAL HARDWARE:** the laptop moved the Lite3 forward through the
vendor `jy_exe` manual-axis path using a 12-byte UDP SimpleCMD with full command
code `0x21010130`. An identical repeat completed safely, but only the first has
an explicit operator report of physical translation. The selected pilot
architecture is:

```
bounded software command
  -> Ethernet UDP 192.168.1.120:43893
  -> jy_exe HeartbeatListener (general command receiver)
  -> CommandList / Controller::ParseCommand
  -> ControlCommands manual axes
  -> existing jy_exe vendor gait controller
  -> physical robot
```

This avoids a custom joint-level locomotion controller. It is not yet a general
teleoperation interface: only a bounded positive forward pulse is proven.

## Repository and evidence identity

- Repository: `/home/abx/Lite3_rl_deploy`
- Remote: `https://github.com/DeepRoboticsLab/Lite3_rl_deploy.git`
- Branch: `main`
- Base commit: `c2432945161d38fec8633a997ce5f9f0dc8c5ec2`
- Worktree: substantially dirty (staged, unstaged, and untracked safety/research
  work). Do not reset, clean, or assume the base commit reproduces current tests.
- Robot-matched binary copy:
  `/home/abx/lite3_uart_analysis/deeprcs`, SHA-256
  `72b0bb6d9d9dc0448df9659879177ea4eec6ba4921fb31d212a0ad1e2fa57fe6`.
- Related library copy:
  `/home/abx/lite3_uart_analysis/libdeepras.so`, SHA-256
  `7810017f10facdfa6a7e0dc1cfcdf6c745b84ce3aa53cced7f47206dea4d59be`.
- Bounded validation tool (outside repository):
  `/home/abx/lite3_uart_analysis/lite3_manual_axis_forward_probe.py`.

## Proven hardware milestones

1. Direct Ethernet route from laptop 192.168.1.102 through `enp3s0` to robot
   192.168.1.120; low-latency ping and continuous UDP telemetry verified.
2. MotionSDK joint/IMU feedback decoding and freshness monitoring verified.
3. Acquisition-only request produced no physical motion; ownership acknowledgment
   remains unavailable/unconfirmed in the SDK.
4. `stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED` produced a controlled
   supported stand. Stable hold and explicit release back to lying were proven.
5. Bounded RL-zero and stop/release from RL-zero were physically stable and kept
   normalized input exactly 0,0,0.
6. Direct ONNX forward attempts did not provide useful reliable translation;
   results included lean/posture response, attempted stepping, and falls/releases.
7. The original handheld controller reliably caused vendor gait. Passive state
   evidence showed forward axis/goal velocity and motion_state 0->1->0.
8. External full manual-axis command `0x21010130` moved the robot forward in the
   explicitly observed first test using +0.099985 normalized axis for 0.30 s,
   then returned to neutral. An identical repeat completed and returned safely
   to state `6/0/0`; its physical result was not separately reported.

## Direct ONNX/MotionSDK investigation

The upstream April 25 2026 commit `7871b47` changed the ONNX model together with
its nominal pose/default contract (`HipY/Knee -0.80/1.60` to `-0.65/1.30`) and
stand height. Policy timing also had a 12 ms historical contract versus a later
20 ms path. Mixing model, default pose, stand height, timing, observation/action
contract, or last-action semantics produced invalid comparisons; the pre-April
stack was therefore restored and evaluated coherently.

Offline MuJoCo showed the January/pre-April model was materially more forceful:
approximately 0.996 m over the 5 s +0.25 reference versus 0.619 m for April, with
larger first-second target span and better behavior under weakened-actuator
simulation. Corrected stand-height/default-pose contract and 12 ms policy timing
allowed stepping attempts on hardware, but bounded forward tests still did not
achieve safe useful translation. Hardware produced substantially less knee motion
than simulation and often settled into a lean or lost support.

This does not prove the policy is intrinsically unusable; it proves that direct
ONNX/MotionSDK joint locomotion has unresolved sim-to-real dynamics/tracking risk.
It is paused for the pilot because the vendor gait controller already produces
successful motion and now has a source-backed external command entry point.

Detailed policy comparison: `docs/POLICY_GAIT_ROOT_CAUSE_2026-09-14.md`.

## Original controller and `jy_exe` investigation

### Rejected device/IPC hypotheses

- `/dev/ttyS6` is the Yesense IMU channel, not controller input.
- ttyS3 is associated with battery handling and ttyS1 with ultrasound/heat-related
  hardware; no controller axes were observed on ttyS1/ttyS3/ttyS6.
- `jy_exe` had no controller `/dev/input/event*` or hidraw descriptor.
- No separate local controller daemon, relevant POSIX/System V shared memory,
  UNIX socket, FIFO, or message queue producer was found.
- `nxd` is NoMachine and is unrelated to locomotion.
- A persistent SSH connection from 192.168.2.101 is observable, but no evidence
  proves controller axes traverse SSH. Do not use this as an integration design.

### Passive network evidence

Source-filtered captures during successful original-controller forward motion
showed 12-byte UDP packets from `192.168.2.101:43897` to
`192.168.2.1:43893` at about 2 Hz. Payload was the little-endian heartbeat code
`0x21040001`, value 0, type 0. No axis-bearing UDP packet from that source was
visible. Therefore the original controller's physical transport before `jy_exe`
remains unknown; the heartbeat capture is not proof of its axis protocol.

Capture files:

- `/home/abx/lite3_uart_analysis/lite3-controller-forward.pcap`
- `/home/abx/lite3_uart_analysis/lite3-controller-all-forward.pcap`
- `/home/abx/lite3_uart_analysis/lite3-controller-standing-forward.pcap`
- `/home/abx/lite3_uart_analysis/lite3-controller-ingress-forward.pcap`

### Static command path — proven

`deepros::listener::HeartbeatListener::RunRoutine(void*)` at `jy_exe:0x96c30`
is not heartbeat-only: it creates/binds the general UDP command socket, receives
up to 1036 bytes, classifies simple versus parameterized frames, and enqueues a
`deepros::command::Command` in the global `CommandList`.

SimpleCMD wire layout, little-endian, packed to 12 bytes:

```
offset 0: int32 command code
offset 4: int32 signed command value
offset 8: int32 type (0 for these manual-axis commands)
```

`deepros::controller::Controller::ParseCommand(...)` at `0x7bd24` first requires
the `0x21000000` source/category mask, then switches on the command's low 16 bits.
Consequently a bare `0x0130` is not a valid external wire command. The accepted
full wire command is `0x21010130`.

Manual axes:

| Physical meaning | Full wire code | Parse branch | ControlCommands field |
|---|---:|---:|---|
| forward/back | `0x21010130` | `0x7c730` | `left_axis_y`, offset +32 |
| lateral | `0x21010131` | `0x7c904` | `left_axis_x`, offset +24 |
| yaw | `0x21010135` | `0x7caf4` | `right_axis_x`, offset +40 |
| right Y (not used) | `0x21010102` | `0x7cc3c` | `right_axis_y`, offset +48 |

The 0x0130 branch updates movement timing, sets
`ControlCommands.is_joystick_connect` at offset +69 to 1, propagates an internal
`0x21010130` command, applies the joystick deadzone/scaling, and writes the
normalized double to +32. The four manual fields are consumed by
`IsRobotCanGetIntoMotion`; `SetManualVel` directly reads +24 and +32. The final
ControlCommands object enters the existing vendor Motion pipeline.

Forward scaling recovered exactly:

```
raw in [-6552,+6552] -> 0
raw > +6552          -> (raw - 6553) / 26214
raw < -6552          -> (raw + 6553) / 26215
```

For normalized +0.10 the nearest signed integer is 9174, decoded as
`+0.09998474097810331`. The forward packet bytes are:

```
30 01 01 21  d6 23 00 00  00 00 00 00
```

Legacy plugin codes 320/321/325 are different commands/encodings in this
firmware path and did not cause locomotion. They must not be retried.

## Bounded live-test tool and safety behavior

`/home/abx/lite3_uart_analysis/lite3_manual_axis_forward_probe.py` implements
only the first proven forward pulse:

```
1.00 s: forward=0, lateral=0, yaw=0 at 20 Hz
0.30 s: forward raw=9174 (~+0.10), lateral=0, yaw=0 at 20 Hz
1.00 s: forward=0, lateral=0, yaw=0 at 20 Hz
exit:   five additional neutral triplets
```

It is dry-run by default and does not create a UDP socket in dry-run. Live mode
requires both `--transmit` and the exact explicit confirmation token. It refuses
known competing control processes; binds 43897 exclusively; waits for a valid
fresh RobotState; requires basic state 6, finite battery >=25%, and freshness
throughout nonzero transmission. SIGINT/SIGTERM and exceptions enter the redundant
neutral path whenever a send socket exists. It has no automatic retry.

It does not send heartbeat, MODE, CONTROL, posture, gait, KEEP_STEPPING,
320/321/325 ComplexCMD, MotionSDK ownership, RL, or joint commands.

Offline checks:

- Python compile: pass.
- Packet size/header/value/deadzone and invalid-value self-tests: pass.
- Missing live confirmation token: rejected before socket creation.
- Dry-run under `strace -e trace=network`: no network syscalls.
- Dry-run packets/log fields: exact expected bytes, zero robot packets.

Live evidence:

| Test | Time (+03:00) | Battery | Pre/post state | Result |
|---|---|---:|---|---|
| First | ~20:08 | 57% | `6/0/0` -> `6/0/0` | physical forward success |
| Repeat | ~20:09 | 56% | state 6 -> `6/0/0` | completed safely; physical result not separately reported |

Logs contain 51 records each: 20 ZERO_BEFORE, 6 FORWARD, 20 FINAL_ZERO,
5 EXIT_ZERO:

- `/tmp/lite3-manual-axis-forward-live-20260914.jsonl`
- `/tmp/lite3-manual-axis-forward-live-repeat-20260914.jsonl`

## Resolved process conflict

An old `/home/abx/Lite3_rl_deploy/build_supported_stand/lite3_validation_console`
was found as PID 33723, bound to UDP 43897. Its identity, executable, CWD, TTY,
and socket were inspected. After the operator explicitly said to proceed, SIGINT
was used so its integrated shutdown/release path could run. The process exited;
43897 and the conflicting process list were empty. A fresh passive sample then
showed state `6/0/0`, battery 57%, before the first test.

This is historical and resolved. Never kill PID 33723 by number in a later boot;
PID identities are ephemeral. Always re-identify the owning executable and use
its clean shutdown path.

## Safety rules

- Original controller/E-stop immediately available; clear flat area; nobody near
  the legs; physical operator observing.
- One bounded action per explicit approval; never automatic retry.
- Require fresh current telemetry, safe standing state, adequate current battery,
  correct Ethernet route, exclusive telemetry socket, and no competing sender.
- Abort to neutral on unexpected direction, instability, excessive tilt,
  telemetry loss, state change, send/network error, or inability to stop.
- Never bypass a guard or equate last-known telemetry with current state.
- Never inject command codes not supported by direct source/static evidence.
- Never write to ttyS1/ttyS3/ttyS6; they are sensor/system channels.
- Do not retry legacy 320/321/325 or KEEP_STEPPING.
- Do not combine the manual-axis tool with MotionSDK/RL, the old Xbox bridge,
  Lite3 transfer, or another telemetry-port owner.

## DO NOT REDISCOVER / DO NOT RETRY

1. ttyS6 controller hypothesis — disproven; Yesense IMU.
2. Legacy velocity codes 320/321/325 — did not enter locomotion on this build.
3. Direct ONNX as pilot locomotion — paused; joint-level sim-to-real path did not
   provide safe useful translation despite considerable validation.
4. Controller-axis-over-SSH — no evidence; SSH is not a proven axis transport.
5. Visible axis UDP from 192.168.2.101 — captures showed heartbeat only.
6. Bare `0x0130` on the wire — fails ParseCommand category/source requirement.

## Exact next step

No live command is pending. Before any new test:

1. Repeat process/socket/route/fresh RobotState/battery preflight.
2. Re-run the packet-byte self-test in dry-run.
3. Prepare a **separate bounded backward-only tool/profile** using the proven
   negative 0x21010130 conversion, with the same limits and fail-closed behavior.
4. Stop and obtain explicit operator authorization before its first nonzero send.

Do not lengthen forward or test lateral/yaw automatically. General ROS2/autonomy
integration comes only after separately proving forward, backward, neutral/timeout,
and controlled stop behavior through this vendor-gait path.

Documentation-time readiness snapshot: no real competing process or local port
owner; Ethernet route via `enp3s0`/192.168.1.102; packet self-test pass with zero
robot packets; fresh passive RobotState `6/0/0`, battery 53%. This establishes
readiness at that instant only. No robot command was sent during documentation.
