---
schema: bipolix.test_session/v1
id: TEST-20261002-026
title: Map Server and AMCL ordered lifecycle recovery
date: 2026-10-02
classification: LIVE_STATIC_PROVEN
result: PASS
categories: ROS2, LOCALIZATION, RELIABILITY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# TEST-20261002-026 — Map Server and AMCL ordered lifecycle recovery

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

Map Server/AMCL processes appeared active while configuration/activation timed out, amcl_pose and map→odom were absent, and confidence stayed zero. The documented repair orders network/DDS, HIGH-LEVEL, fresh scan/odom, Map Server ACTIVE, AMCL ACTIVE, TF, then confidence. Bounded retries and localization-only restart after DDS cleanup avoid indefinite half-alive startup. The closeout reports offline/live software validation. Exact journals, installed manifest and repeated-boot soak are missing; heartbeat-sensitive HIGH-LEVEL restart is not a casual localization workaround.

## Evidence and relationships

- [Primary retained report](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- Related records: [FINDING-20260927-001](../findings/FINDING-20260927-001-systemd-active-ros-dead.md), [TEST-20261002-001](TEST-20261002-001-dds-recovery-with-incomplete-persistent-deployment.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.
