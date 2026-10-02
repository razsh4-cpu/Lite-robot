---
schema: bipolix.test_session/v1
id: TEST-20261002-003
title: AUTONOMY QoS stall and compatible velocity input
date: 2026-10-02
classification: LIVE_STATIC_PROVEN
result: PASS
categories: ROS2, NAVIGATION, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# TEST-20261002-003 — AUTONOMY QoS stall and compatible velocity input

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: Reported by 2026-09-27 closeout; exact run timestamp UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

Nav2 produced velocity intent, but incompatible QoS prevented reliable receipt by the AUTONOMY adapter. The sensor-data/BEST_EFFORT subscription and protected path retained finite bounds, exclusive ownership, and the independent 300 ms watchdog. The closeout reports offline and live software validation. Original per-message QoS/latency captures are missing; this record does not claim a separately measured physical watchdog acceptance.

## Evidence and follow-up

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [TROUBLESHOOTING.md](../../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20261002-001](../findings/FINDING-20261002-001-autonomy-velocity-qos-compatibility-preserves-independent-watchdog.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
