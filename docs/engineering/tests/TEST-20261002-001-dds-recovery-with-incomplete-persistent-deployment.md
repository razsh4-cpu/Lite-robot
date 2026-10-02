---
schema: bipolix.test_session/v1
id: TEST-20261002-001
title: DDS recovery with incomplete persistent deployment
date: 2026-10-02
classification: PARTIAL
result: PARTIAL
categories: ROS2, LOCALIZATION, DEPLOYMENT
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md
---

# TEST-20261002-001 — DDS recovery with incomplete persistent deployment

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: 2026-09-26.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

On 2026-09-26 the services were active and existing laptop subscribers saw traffic, but new onboard DDS participants and the input gate saw no scan, odometry, or required TF. UDPv4 discovery immediately found the runtime and LiDAR. The copied input helper returned all required readiness fields true. Localization then produced twelve 98.4–98.9% samples, and a dry 10 cm path returned three poses and error code zero. No autonomous motion was sent; the last recorded source was NONE. The updated privileged unit installation remained pending after sudo authorization expired. The later closeout reports ordered recovery, but does not convert this incomplete persistence stage into an installed-unit proof.

## Evidence and follow-up

- [TROUBLESHOOTING.md](../../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20260927-001](../findings/FINDING-20260927-001-systemd-active-ros-dead.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
