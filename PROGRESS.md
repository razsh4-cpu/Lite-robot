# Progress

## Proven on hardware

- Ethernet and passive robot telemetry.
- Vendor manual-axis discovery and safe ROS 2 `/cmd_vel` adapter.
- Forward, backward, yaw both directions and curved motion.
- RPLIDAR S2 bringup/RViz and corrected positive-X frame convention.
- ICP replay tuning and corrected-TF live forward validation.
- SLAM Toolbox live map publication.

## Implemented, pending one hardware validation

- ICP auto-recovery after three consecutive failures (`ResetCountdown=3`).
- End-to-end mapping after that change, followed by map saving.

## Handoff verification

- 2026-09-16: both ROS packages built successfully.
- Focused offline suite: 15 tests passed.
- Credential-pattern scan found no tracked secret.

## Paused/rejected for pilot

- Direct RL/ONNX joint-control locomotion: stand and RL-zero safe; forward not
  reliable enough.
- Legacy Motion Host velocity codes 320/321/325.
- Controller emulation via tty/UART.

Follow [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md). No autonomous Nav2 motion yet.
