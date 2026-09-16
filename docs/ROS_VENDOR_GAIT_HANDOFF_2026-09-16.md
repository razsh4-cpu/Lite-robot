# Selected pilot locomotion path — 2026-09-16

This repository preserves the direct MotionSDK/ONNX research. It is no longer
the selected pilot locomotion path.

## What this repository proved

- Passive MotionSDK feedback and safe acquisition-only behavior.
- Supervised computer-commanded stand, stable hold and explicit release.
- Zero-velocity RL entry and explicit stop/release.
- Multiple safeguards around telemetry freshness, joint-send gating, worker
  shutdown, stand authorization, convergence and abort handling.
- Direct ONNX forward trials did not produce reliable useful translation;
  observed results included leaning, stepping attempts and falls/releases.

## Selected path

The pilot uses the high-level manual-axis path in the robot's existing `jy_exe`
gait controller. Real-hardware forward, backward, yaw and arcs are proven. The
ROS 2 implementation and complete current handoff are in:

```text
/home/abx/ros2_ws
```

Start with its `ROBOT_HANDOFF.md`. The verified wire cases are:

- forward/back `0x21010130`
- lateral `0x21010131`
- yaw `0x21010135`

Legacy 320/321/325 and `KEEP_STEPPING` are rejected paths for this firmware.

## Preservation rule

Do not delete this repository or rewrite its history: it contains the safety
implementation, test suite, stand/RL-zero milestones, failed locomotion traces
and the static analysis that led to the vendor-gait solution. Do not resume live
MotionSDK joint control without a new explicit engineering decision.

