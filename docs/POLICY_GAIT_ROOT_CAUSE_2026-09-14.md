# Lite3 gait root cause — 2026-09-14

No robot command was sent during this investigation.

## Proven divergence

The failed hardware trace and MuJoCo have nearly identical first policy
observations, actions, and joint targets at normalized forward `+0.25`. The
divergence begins after that target reaches the plant: MuJoCo develops knee
motion and gait, while the loaded robot moves its knees only `0.014–0.030 rad`
and the policy settles into a lean. Hardware packet decoding, joint ordering,
the PD equation, and command delivery are therefore downstream-correct.

The April 25, 2026 upstream commit `7871b47` replaced the ONNX file together
with its nominal pose (`-0.80/1.60` to `-0.65/1.30`) and stand height. The exact
policy present in upstream on January 28, 2026 was SHA-256
`b576f8354ebb2ec4d3af90322b8d88099a8822723496220a319bdf0f6b30059b`.
An upstream real-Lite3 report from that date states that forward/backward and
lateral motion worked. The replaced April model had SHA-256
`efa6581d314d8c0442881453d39fc082c09b28bbaa3029d328fcd61fa25b57c7`.

## Offline comparison

Both policies were tested from the currently proven `-0.65/1.30` standing
pose using the same Lite3 MuJoCo plant, command, and PD gains.

| Policy | period | zero result | +0.25, 5 s | first-second target span |
|---|---:|---|---:|---:|
| April 2026 | 20 ms | stable | 0.619 m | 0.409 rad |
| January 2026 | 12 ms | stable | 0.996 m | 0.603 rad |

At 70% simulated actuator authority, the January policy retained a `0.644 rad`
first-second target span and translated `0.193 m`; the April policy produced
`0.411 rad` and `0.235 m`. At 60%, the April policy became posture-only
(`0.035 m`) while the January policy still generated approximately twice the
target excursion (`0.559 rad`) and `0.062 m` before falling below the test's
height stability bound. This reproduces the observed failure mechanism:
insufficient real-plant response prevents the April policy from developing its
simulated gait, while the earlier physically reported policy has materially
more gait authority.

## Fix

Restore the exact January 2026 ONNX artifact and its paired deployment
contract: nominal HipY/Knee pose `-0.80/1.60`, action period `12 ms`, unchanged
`Kp=30`, `Kd=1`, action scaling, observation order, command scaling, packet
format, ownership, stand logic, and safety guards. Policy entry still clears
the last-action observation, preventing state leakage between sessions.

This is not yet proof that the restored policy walks on this individual robot.
It is the smallest source-backed correction and requires one bounded,
supervised hardware validation.
