---
schema: bipolix.engineering_finding/v1
id: FINDING-20260915-001
title: ICP rejection enters a null-guess cascade
date: 2026-09-15
status: DO_NOT_USE
categories: ODOMETRY, ROS2, R_AND_D
evidence: onboard_ros2_ws/src/sensor_visualization/docs/ICP_ODOMETRY_OFFLINE_2026-09-15.md
---

# FINDING-20260915-001 — ICP null-guess cascade

A recorded scan with correspondence ratio 0.646 was rejected by the 0.70
threshold; the next update received a null guess and later scans cascaded into
`cannot do registration with a null guess`. Lower-threshold experiments are
research evidence, not product odometry authority.

- Evidence: [offline ICP investigation](../../../onboard_ros2_ws/src/sensor_visualization/docs/ICP_ODOMETRY_OFFLINE_2026-09-15.md).
- Known bad: promote this experimental ICP configuration into the product path
  merely because isolated replay improves.
- Current path: persistent HIGH-LEVEL telemetry owns product `/odom` and
  `odom→base_link`.
- DO NOT REPEAT: change odometry ownership or thresholds without isolated
  replay, single-owner proof, and a separately approved live validation.
