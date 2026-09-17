# Lite3 real-test readiness checkpoint — 2026-09-17

## Stop point

**Later result:** the authorized attempt failed closed before motion because the
separate five-second authorization expired. No joint-send gate opened and no
stand command ran. See `docs/SUPPORTED_STAND_RESULT_2026-09-17.md`. A new attempt
requires new explicit approval and must use the atomic `stand_once` action.

The software is ready for one **explicitly authorized, mechanically supported
stand test**. That test has not been run and is not authorized by this document.
The robot has not been moved, control ownership has not been requested, transmit
has not been enabled, and no command packet has been sent.

The system is **not ready for a hardware body-shift or one-leg-lift test**. The
passive capture shows the robot is folded/resting rather than standing, and the
installed SDK/firmware reports zero for all four foot-force channels. A supported
stand must be observed first. Real contact feedback must then be established, or
a separately reviewed contact-independent recovery design must be created, before
any foot lift.

## Exact environment

- Host: Linux Mint 22.1 Xia, Ubuntu Noble base, kernel 6.8.0-63-generic
- Branch: `low-level-leg-control`
- Worktree: `/home/abx/Desktop/robotdog_ws/low-level-leg-control`
- Simulation milestone commit before this checkpoint:
  `69b923722e3e08941b3c8cd9010ff74c0fd09c17`
- Hardware-safe build: `build-low-level-hw`
- Build options: `BUILD_PLATFORM=x86`, `BUILD_SIM=OFF`, `SEND_REMOTE=OFF`,
  `USE_MJCPP=OFF`, `BUILD_TESTING=ON`
- Console:
  `/home/abx/Desktop/robotdog_ws/low-level-leg-control/build-low-level-hw/lite3_validation_console`

The complete build succeeds. CTest reports 13/13 passing, covering passive
startup, acquisition isolation, one-use stand authorization, convergence,
timeouts, hold/release, abort and signal paths, RL/forward isolation, and the
vendor adapter.

## Passive live evidence

`lite3_passive_stand_observer` is structurally receive-only: its translation unit
does not include the vendor `Sender`; ownership and send methods throw if called.
It ran for 35.0005 seconds against live telemetry:

- 34,999 packets, 999.96 Hz callback rate
- 3,499 fresh/progressing samples; one startup sample not fresh
- maximum fresh age 3.78 ms
- joint gate: closed (`0`)
- ownership request: not sent (`0`)
- ownership: `NOT_REQUESTED`
- mean IMU roll: -0.00075 rad; mean pitch: -0.00975 rad
- maximum passive position sample delta: 0.00099 rad

The passive joint angles are far from the 0.30 m standing target. The largest
mean error is 2.1745 rad at FR HipY. This is consistent with a folded/resting
robot and rules out treating the present posture as an established stand.

The MotionSDK telemetry struct contains a three-axis contact-force field for each
leg. `HardwareInterface::GetContactForce()` now maps the Z components in verified
FL, FR, HL, HR order, and the fake-SDK adapter test proves that mapping with four
distinct values. In the live 35-second capture, every mapped channel remained
exactly zero:

| Channel | Minimum | Maximum |
|---|---:|---:|
| FL force Z | 0 | 0 |
| FR force Z | 0 | 0 |
| HL force Z | 0 | 0 |
| HR force Z | 0 | 0 |

This establishes that contact force is unavailable or unpopulated under the
current live conditions. It does not establish a real-robot loaded/unloaded
threshold. Simulation's 2 N threshold must never be reused on hardware.

## Completed simulation prerequisite

The front-right one-leg primitive passed twice in MuJoCo: vertical lift and lift
plus 5 mm forward motion. The measured lift was 6.4315 mm, maximum absolute roll
was 0.3575 degrees, maximum absolute pitch was 0.6556 degrees, minimum COM support
margin was 92.953 mm, FR was unloaded for the complete one-second hold, the other
three feet remained loaded, and all four contacts returned after lowering. The
implementation uses Cartesian FK/IK and position/PD with zero feed-forward torque.
Full details and the joint mapping are in `docs/ONE_LEG_LIFT_SIMULATION.md`.

These simulator gains, offsets, force thresholds, and compliance compensation
are not hardware settings.

## The next real test

The next real test is one supported stand attempt using the existing guarded
`StandUpState`. It is not a body shift and not a leg lift. It may run only after
the operator verifies all of the following at the robot:

1. Mechanical support prevents a fall or collapse, including during SDK release.
2. The original emergency stop is in the operator's hand and working.
3. The area is clear and nobody is within the robot's fall or leg workspace.
4. Battery and robot health are acceptable and the robot is connected as expected.
5. One supervised attempt has separate, explicit approval.

The console sequence in `docs/SUPPORTED_STAND_TEST.md` must be performed one action
at a time. Do not paste it as a batch. The intended sequence is `status`, `acquire`,
`status`, atomic one-use `stand_once`, observation, `status`, and `quit`.
Do not invoke `rl_zero_once`, `forward_once`, velocity control, or the simulated
leg primitive.

The guarded stand requires advancing telemetry no older than 300 ms, finite
joints and IMU, measured joint speed at or below 0.15 rad/s at entry, roll/pitch
within 0.35 rad, zero software velocity, and command tracking within 0.35 rad.
It uses position/PD with zero feed-forward torque. Convergence requires every
joint within 0.08 rad, measured speed at or below 0.15 rad/s, target speed at or
below 0.001 rad/s, and a stable 0.5-second dwell. It aborts on failed checks and
on nonconvergence after 6 seconds, holds a reached target no longer than 2 seconds,
then closes the gate and requests release. The private send permit has an
independent 8-second ceiling.

Passive velocity estimates occasionally exceeded 0.15 rad/s for one sample even
while joint positions remained stable. The live preflight may therefore reject
the attempt; rejection is safe and must not be bypassed or followed by retries.

## After the supported stand

Only if the supported stand passes and release behavior is understood should a
new, separately reviewed and authorized test command a 10 mm rear-left body target
over 3 seconds and return to stand. Its proposed limits are zero feed-forward
torque, `kp <= 60`, `kd <= 0.7`, target joint speed at or below 0.10 rad/s,
per-joint target change at or below 0.03 rad, roll/pitch abort at 3 degrees,
tracking abort at 0.15 rad, and a 5-second state timeout. This body-shift hardware
controller is not implemented or authorized at this checkpoint.

A hardware leg lift remains later still. It requires proven standing and return,
a usable contact/unloading signal or an explicitly reviewed alternative, and its
own one-use authorization. Raw torque control is outside this milestone.
