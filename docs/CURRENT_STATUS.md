# Current status — 2026-09-16

## Robot/network

- Motion Host `192.168.1.120`; laptop `192.168.1.102/24` on `enp3s0`.
- Robot commands UDP `43893`; telemetry delivered to UDP `43897`.

## Software/control

- ROS 2 Jazzy workspace `/home/abx/ros2_ws`.
- `sensor_visualization`: current control, telemetry, sensor and mapping tools.
- `lite3_security_patrol`: future mission scaffold; no autonomous authority.
- Pilot locomotion is the verified `jy_exe` manual-axis vendor gait path.
- Navigation state is mapping only; no Nav2 controller enabled.

## Sensors/frames

- RPLIDAR S2: `/scan`, `lidar_link`, about 10 Hz.
- Mount assumption/validation: `(0,0,0.08 m)`, yaw `pi`.
- TF: `map -> odom -> base_link -> lidar_link`.
- ICP publishes `/odom` and `odom -> base_link`; SLAM publishes `/map` and
  `map -> odom`.
- D455 is planned/partially demonstrated but not in current mapping acceptance.

## Open issue

The corrected-TF forward bag proves continuous ICP and correct sign. A later
mapping drive had one rejected registration then a null-guess cascade because
reset was disabled. `ResetCountdown=3` is now built/passive-stable; a new motion
run was correctly blocked at battery 24%, below the 25% control gate.

Runtime process state must be checked anew before every test; this document
does not claim a node is currently running.

