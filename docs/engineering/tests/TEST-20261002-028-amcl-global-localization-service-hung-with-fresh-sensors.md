---
schema: bipolix.test_session/v1
id: TEST-20261002-028
title: AMCL global-localization service hung with fresh sensors
date: 2026-10-02
classification: PARTIAL
result: PARTIAL
categories: ROS2, LOCALIZATION, RELIABILITY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md
---

# TEST-20261002-028 — AMCL global-localization service hung with fresh sensors

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

The troubleshooting report records a fixed 55.1% score, scan near 10 Hz and odometry near 50 Hz, while global-localization service remained at making request, lifecycle queries failed and amcl_pose did not respond. This supports an unresponsive AMCL process rather than stale sensors. The documented workaround restarts localization only and discards the old particle state, requiring fresh convergence/manual disambiguation. No separate raw recovery terminal capture is retained, so this session preserves the failure and workaround without inventing an isolated post-restart PASS.

## Evidence and relationships

- [Primary retained report](../../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- Related records: [FINDING-20260927-001](../findings/FINDING-20260927-001-systemd-active-ros-dead.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.

- Related reusable finding: [FINDING-20261002-016](../findings/FINDING-20261002-016-fresh-scan-and-odometry-do-not-prove-responsive-amcl.md).
