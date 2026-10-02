---
schema: bipolix.test_session/v1
id: TEST-20261002-029
title: Stationary saved-pose hypothesis exhausted at 55.1 percent
date: 2026-10-02
classification: PARTIAL
result: PARTIAL
categories: LOCALIZATION, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md
---

# TEST-20261002-029 — Stationary saved-pose hypothesis exhausted at 55.1 percent

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

The reported stationary global search exhausted at match fraction 0.551, with 216/392 wall hits. A saved pose remains an initial hypothesis, not physical ground truth. The report describes approximately 20 degrees rotation and 20–30 cm manual translation as the recovery sequence, followed by release and three consecutive >=80% samples. Exact before/after samples from this isolated motion are missing; later accepted localization does not fill that gap. No map origin, extrinsic, or threshold change is inferred.

## Evidence and relationships

- [Primary retained report](../../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- Related records: [TEST-20260927-003](TEST-20260927-003-home-map-localization.md), [FINDING-20261002-004](../findings/FINDING-20261002-004-localization-confidence-is-a-custom-scan-to-map-match-score.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.
