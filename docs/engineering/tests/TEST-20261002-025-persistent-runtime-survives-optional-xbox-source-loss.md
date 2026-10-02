---
schema: bipolix.test_session/v1
id: TEST-20261002-025
title: Persistent runtime survives optional Xbox source loss
date: 2026-10-02
classification: LIVE_STATIC_PROVEN
result: PASS
categories: ROBOT_CONTROL, SAFETY, ROS2
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20261002-025 — Persistent runtime survives optional Xbox source loss

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

The contemporary closeout reports the persistent runtime separated from optional Xbox command sources. Disconnect revokes manual authorization, zeros/releases that source, and leaves critical heartbeat, telemetry, odometry and TF running through the sole UDP 43897 owner. Source transitions never restore cached velocity or authorization. This is reported live software validation; exact per-disconnect traces, deployed package manifest, and long soak are missing. It does not establish current browser transport readiness.

## Evidence and relationships

- [Primary retained report](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- Related records: [FINDING-20260930-001](../findings/FINDING-20260930-001-command-authority.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.
