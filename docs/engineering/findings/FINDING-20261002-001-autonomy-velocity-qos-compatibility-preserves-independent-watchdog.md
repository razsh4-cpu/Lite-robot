---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-001
title: AUTONOMY velocity QoS compatibility preserves independent watchdog
date: 2026-10-02
status: RESOLVED
categories: ROS2, NAVIGATION, SAFETY
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# FINDING-20261002-001 — AUTONOMY velocity QoS compatibility preserves independent watchdog

## Finding and applicability

Compatible sensor-data/BEST_EFFORT subscriptions repaired the reported Nav2-to-AUTONOMY stall. The independent 300 ms watchdog, finite bounds, and exclusive command ownership remain necessary. Diagnose publisher/subscriber QoS and freshness separately; do not weaken the watchdog to conceal transport loss.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [TROUBLESHOOTING.md](../../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.

- Related records: [TEST-20261002-003](../tests/TEST-20261002-003-autonomy-qos-stall-and-compatible-velocity-input.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
