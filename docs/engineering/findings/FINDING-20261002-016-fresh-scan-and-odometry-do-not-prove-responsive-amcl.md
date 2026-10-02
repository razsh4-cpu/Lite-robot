---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-016
title: Fresh scan and odometry do not prove responsive AMCL
date: 2026-10-02
status: HISTORICAL
categories: ROS2, LOCALIZATION, RELIABILITY
evidence: onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md
---

# FINDING-20261002-016 — Fresh scan and odometry do not prove responsive AMCL

The retained incident had fresh scan/odometry while AMCL global service, lifecycle and pose responses hung. Diagnose executor/lifecycle responsiveness separately from input freshness. The localization-only workaround resets particle state and needs fresh convergence; avoid interrupting HIGH-LEVEL heartbeat merely to repair localization. Exact recovery captures and repeated-boot acceptance remain missing.

This is retrospective capture; exact run SHA, timestamps, and missing retest
measurements remain `UNKNOWN`. Resolution labels software behavior only where
reported, not current physical safety or sustained reliability.

- [Primary report](../../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- Related sessions: [TEST-20261002-028](../tests/TEST-20261002-028-amcl-global-localization-service-hung-with-fresh-sensors.md).
- DO NOT REPEAT: infer lifecycle readiness from process state or one fresh
  sensor stream; erase pending installed acceptance after software repair.
