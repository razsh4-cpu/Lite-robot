# Experiment record

## Vendor gait/control

- Original-controller captures linked physical axes, HandleState goal velocity
  and motion state `6/0/0 -> 6/0/1`.
- Static analysis mapped accepted manual-axis cases and wire source bits.
- Bounded live tests proved forward, backward, yaw both ways and an arc.
- Deadman and shutdown reliably returned to neutral.

## Direct ONNX/MotionSDK research

- Safe acquisition, supervised stand, hold, release and RL-zero were proven.
- April/pre-April contracts, default poses and policy periods were compared;
  pre-April used a coherent 12 ms policy period.
- Forward produced lean/stepping/fall rather than reliable translation. This
  route is paused; vendor gait is selected for the pilot.

## ICP replay

Source `bags/lite3_20260915-191547`: 626.7 s, 6,273 scans, 2,769 odom,
139 cmd_vel. Baseline lost tracking during motion.

| Test | Change | Result |
|---|---|---|
| baseline | current-at-capture | loss/null-guess cascade |
| ratio 0.30 | correspondence only | improvement, not selected |
| ratio 0.50 | correspondence only | continuous plausible replay; selected |

Compact results are in `logs/icp_replay/`; detailed procedure is under
`src/sensor_visualization/docs/`.

## Corrected-TF live validation

`bags/tf_forward_validation_20260915_2002`: dx `+0.303169 m`, dy
`+0.012513 m`, dyaw `-0.037248 rad`, max odom gap `0.11876 s`, no loss,
minimum positive inlier ratio `0.504673`, fresh state 6 throughout.

## Mapping/recovery

SLAM produced live `/map`. A later drive caused one ICP failure followed by an
indefinite null-guess cascade (`ResetCountdown=0`). Only ResetCountdown changed
to 3. Passive odometry returned at ~10 Hz. Motion re-test was safely blocked at
24% battery.

