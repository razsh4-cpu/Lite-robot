---
schema: bipolix.test_session/v1
id: TEST-20261002-027
title: Bounded product odometry publication repair
date: 2026-10-02
classification: LIVE_STATIC_PROVEN
result: PASS
categories: ODOMETRY, ROS2, PERFORMANCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20261002-027 — Bounded product odometry publication repair

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

The contemporary closeout and operations KB report approximately 154 Hz odometry/TF publishing from queued vendor telemetry, creating unnecessary executor/DDS load. The sole receiver now drains a bounded burst of at most 64 datagrams, keeps the newest valid RobotState, and publishes once per 20 ms tick, at most 50 Hz. This is reported live software validation, not a current rate measurement. The recovered finding previously said roughly 1 kHz without support and is transparently corrected. Different dated bag aggregate rates do not overwrite this source-specific observation.

## Evidence and relationships

- [Primary retained report](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- Related records: [FINDING-20260927-004](../findings/FINDING-20260927-004-odom-publication-rate.md), [FINDING-20261002-084](../findings/FINDING-20261002-084-retained-bags-and-clock-metadata-impose-evidence-limits.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.
