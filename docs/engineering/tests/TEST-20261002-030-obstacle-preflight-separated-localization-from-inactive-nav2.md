---
schema: bipolix.test_session/v1
id: TEST-20261002-030
title: Obstacle preflight separated localization from inactive Nav2
date: 2026-10-02
classification: OFFLINE_PROVEN
result: PASS
categories: NAVIGATION, DEPLOYMENT, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: docs/FAILURES_AND_FIXES.md
---

# TEST-20261002-030 — Obstacle preflight separated localization from inactive Nav2

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

Obstacle status reported Nav2 planner unavailable while Map Server and AMCL were active because the separate Nav2 navigation service was not running. The documented implementation permits the motion command to start only the existing Nav2 service when it is the sole missing condition, then verify planner/controller/BT Navigator and both costmaps. Read-only status never starts it. This software repair does not constitute installed Mini-PC retest or physical obstacle-wrapper acceptance.

## Evidence and relationships

- [Primary retained report](../../FAILURES_AND_FIXES.md).
- Related records: [TEST-20261002-006](TEST-20261002-006-importable-obstacle-helper-packaging-repair.md), [TEST-20261002-018](TEST-20261002-018-reconstructable-obstacle-snapshot-software-repair.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.

- Related reusable finding: [FINDING-20261002-017](../findings/FINDING-20261002-017-active-localization-does-not-mean-nav2-servers-are-available.md).
