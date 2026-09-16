# Lite3 handoff — START HERE

## Authoritative update — 2026-09-14 20:10 +03:00

**COMPUTER-COMMANDED FORWARD LOCOMOTION THROUGH THE VENDOR `jy_exe` GAIT
CONTROLLER IS PROVEN ON REAL HARDWARE.** The first test has explicit operator
confirmation of physical motion. An identical repeat completed its packet/zero
sequence with healthy post-state, but lacks a second explicit physical report.
Both used the exact manual-axis wire command identified in this robot's
`deeprcs` binary:

```
laptop 192.168.1.102
  -> UDP 192.168.1.120:43893
  -> 12-byte SimpleCMD 0x21010130, signed raw value 9174
  -> ParseCommand low-16 case 0x0130
  -> ControlCommands.left_axis_y / is_joystick_connect
  -> existing jy_exe manual locomotion controller
```

Each test used 1.0 s neutral, normalized forward approximately `+0.10` for
0.30 s (six 20 Hz samples), at least 1.0 s neutral, and five extra exit-neutral
triplets. Lateral and yaw stayed zero. Both tests ended at telemetry tuple
`6/0/0` with the robot standing; the operator physically confirmed the first
test moved and requested the repeat. Logs:

- `/tmp/lite3-manual-axis-forward-live-20260914.jsonl`
- `/tmp/lite3-manual-axis-forward-live-repeat-20260914.jsonl`

The bounded tool is
`/home/abx/lite3_uart_analysis/lite3_manual_axis_forward_probe.py` (outside this
repository). Its dry-run was verified under `strace` with zero network syscalls.
It fails closed on competing control processes, telemetry not fresh, basic state
other than 6, or battery below 25%. It sends no heartbeat, mode, posture, gait,
KEEP_STEPPING, legacy 320/321/325 command, or joint command.

Historical blocker PID 33723 (`lite3_validation_console`) was identified on
UDP 43897, then cleanly stopped via SIGINT after operator authorization. Port
43897 was confirmed free before the live tests. This blocker is **resolved**;
do not reuse or blindly kill that PID.

The direct ONNX/MotionSDK locomotion path remains valuable engineering work but
is paused as the pilot motion source: multiple hardware forward trials produced
leaning/stepping/falls instead of useful translation. Supported stand, stable
hold, release, and RL-zero remain proven milestones. The selected pilot path is
now the vendor gait controller via the source-backed manual-axis command.

Next: no further live command until a new supervised test is explicitly approved.
Perform a read-only preflight, retain the same bounded limits, and expand only
one dimension at a time (first backward; lateral/yaw later). See
`docs/HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md` and `docs/NEXT_STEPS.md`.

Updated 2026-09-13 at 22:30 +03:00 after three additional real-hardware
milestones. **Long stand hold, bounded RL-zero, and explicit stop/release from
RL-zero are now PROVEN ON REAL HARDWARE.**

- Supported stand held for about 203 s and released safely to lying.
- RL-zero held physically stable for the full 5.000 s window; 412 policy cycles,
  normalized command always 0,0,0; planned deadline released safely.
- A second RL-zero run was explicitly stopped after 1.413 s; 117 policy cycles,
  zero command throughout; gate closed, worker stopped, telemetry stayed fresh,
  and robot returned safely to lying.

Unrestricted RL and nonzero velocity remain blocked and UNTESTED. Do not infer
that normalized zero means zero joint actuation, or that a nonzero command is
safe. Current console remains running passively in a released state.

Updated 2026-09-13 after the operator-reported successful supported stand
(milestone documented at 21:00 +03:00, Asia/Jerusalem).

**REAL SUPPORTED STAND TEST = SUCCESS. Computer-commanded stand is PROVEN ON
REAL HARDWARE (operator observation).** The robot stood using
`stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`, remained standing, and did
not automatically release. See E6 in docs/EXPERIMENTS.md for evidence/provenance.

Enabling fixes: atomic one-shot authorization/request; 50 ms RMS-speed plus
position-range convergence; monitored stable-hold permit renewal without the
two-second successful-stand release. Ownership acknowledgement is still unconfirmed.

**CONTROLLED RELEASE = SUCCESS ON REAL HARDWARE (operator report, 2026-09-13).**
From stable stand, explicit `release` closed the joint gate, returned local
acquisition to NOT_REQUESTED, preserved fresh telemetry, and the robot returned
to lying as intended. See E7 in docs/EXPERIMENTS.md.

**Historical milestone: supervised zero-velocity RL — now proven as documented above.**
After explicit implementation approval, `rl_zero_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`
uses a separate non-renewable five-second permit from a converged supported hold.
Input is irreversibly locked to zero for that process; `rl`/`velocity` still abort.
Deadline/stop/fault closes the gate, joins the worker, then requests release.
Mechanical support remains mandatory, including after release. One focused inert
suite passed, including actual ONNX first-zero-output continuity. See current status.

The former right-HipY range blocker disappeared after battery restart and an
original-controller normal lying posture, with NO mapping/sign/range changes.
This supports posture/startup dependence, not a proven software mapping defect.

Read in order:

1. [Current state, architecture and exact dirty-tree summary](docs/CURRENT_STATUS.md)
2. [Next supervised operator sequence](docs/NEXT_STEPS.md)
3. [Hardware versus offline evidence](docs/EXPERIMENTS.md)
4. [Design/safety decisions](docs/DECISIONS.md)
5. [Failures and fixes](docs/FAILURES_AND_FIXES.md)
6. [Detailed recovery analysis and historical mapping table](docs/STAND_RECOVERY_2026-09-13.md)

Main branch base: `c2432945161d38fec8633a997ce5f9f0dc8c5ec2`.
The complete research tree is preserved on a dedicated local handoff branch;
use `git log -1` and `git status` for its exact commit/cleanliness. Do not
reset/clean away evidence or assume upstream `main` reproduces this build.
The selected pilot is now the ROS vendor-gait path documented in
`docs/ROS_VENDOR_GAIT_HANDOFF_2026-09-16.md`.
