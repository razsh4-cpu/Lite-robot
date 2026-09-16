# DeepRobotics Lite3 project handoff — 2026-09-16

This is the entry point for a new engineer or agent. Do not rediscover paths
already disproven below.

## Current outcome

- Laptop Ethernet `192.168.1.102/24` communicates with Motion Host
  `192.168.1.120`.
- Passive Motion Host telemetry on UDP `43897` is decoded and monitored.
- Vendor `jy_exe` gait control works through verified manual-axis UDP cases on
  port `43893`.
- Forward, backward, both yaw directions and linear+angular arcs are proven on
  real hardware through the ROS 2 `/cmd_vel` adapter.
- RPLIDAR S2 publishes `/scan`; current mount transform is
  `base_link -> lidar_link = (0,0,0.08 m, yaw=pi)`.
- ICP replay/live validation is stable at `Icp/CorrespondenceRatio=0.50`;
  physical forward now produces positive odometry X.
- SLAM Toolbox produces `map -> odom` and `/map`.
- Nav2 is not authorized to drive the robot yet.

## Proven control chain

```text
/cmd_vel + /lite3/cmd_vel_deadman
  -> lite3_cmd_vel_adapter
  -> normalized forward/yaw + manual-axis deadman
  -> lite3_manual_axis_control
  -> 12-byte SimpleCMD UDP to 192.168.1.120:43893
  -> jy_exe vendor gait controller
```

Verified wire commands: forward/back `0x21010130`, lateral `0x21010131`, yaw
`0x21010135`. Normalized `+0.10` maps to signed raw value `9174`.

Safety: forward ±0.10, yaw ±0.25, lateral forced zero, 300 ms command/deadman/
telemetry freshness, state 6, battery >=25%, finite inputs, neutral on any
failed gate, five neutral packets on shutdown, transmit false by default, no
automatic mode change or retry.

## LiDAR/odometry/SLAM

```text
RPLIDAR S2 -> /scan [lidar_link]
base_link -> lidar_link [static z=0.08, yaw=pi]
rtabmap_odom/icp_odometry -> odom -> base_link and /odom
slam_toolbox -> map -> odom and /map
```

Current deliberate ICP changes are only `Icp/CorrespondenceRatio=0.50` and
`Odom/ResetCountdown=3`. The first survived a recorded forward run. The second
recovers after three rejected scans instead of the observed permanent
null-guess cascade. It is built and passive-tested but needs one motion run at
safe battery.

## Hardware milestones

- Vendor-gait forward/back/yaw/arcs, deadman neutral and shutdown: proven.
- MotionSDK/ONNX acquisition, stand, stable hold, RL-zero and release: proven
  during research; ONNX forward remained unreliable and is paused for pilot.
- Corrected-TF forward run: `dx=+0.303169 m`, `dy=+0.012513 m`,
  `dyaw=-0.037248 rad`, max odom gap `0.11876 s`, no loss report.
- SLAM produced a live map. A later drive exposed the ICP null-guess cascade,
  leading to `Odom/ResetCountdown=3`.

## Do not rediscover / do not retry

- `/dev/ttyS6` is the Yesense IMU, not controller input.
- Legacy codes 320/321/325 are not the manual-axis gait cases for this build.
- `KEEP_STEPPING` caused stepping in place, not intended velocity control.
- Do not use direct ONNX joint control as the pilot gait path.
- No controller-axis stream was found over SSH or visible UDP from
  `192.168.2.101`.
- Never write to tty sensor devices or inject unproven codes.

## Next milestone

With battery preferably above 35%, run one supervised recorded mapping motion
through vendor gait. Verify ICP auto-recovery, positive-X forward and no map
jump, then save the map. Next: AMCL/planning-only, footprint measurement, and
only then a bounded Nav2 controller test.

See `docs/EVIDENCE_INDEX.md` for evidence paths and checksums.

