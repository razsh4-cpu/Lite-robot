---
schema: bipolix.test_session/v1
id: TEST-20261002-032
title: Stale central MQTT bridge destination incident
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: MQTT, NETWORKING, NOMAD, DEPLOYMENT
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: docs/engineering/findings/FINDING-20261001-002-mqtt-bridge-ip.md
---

# TEST-20261002-032 — Stale central MQTT bridge destination incident

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

The existing finding reports never_seen while the Mini-PC/edge path ran because the bridge still targeted the former C&C address .142 instead of .177. It reports that updating the destination restored topic arrival and registry visibility. The Phase-3B plan retains the intended .177 update, while a0cda36 separately records later actual non-motion integration. The original incident and isolated restoration captures are missing. This preserves the failure/fix report without treating a plan checkbox as executed evidence or an ONLINE registry as healthy robot readiness.

## Evidence and relationships

- [Primary retained report](../findings/FINDING-20261001-002-mqtt-bridge-ip.md).
- Related records: [FINDING-20261001-002](../findings/FINDING-20261001-002-mqtt-bridge-ip.md), [TEST-20261001-001](TEST-20261001-001-nomad-phase3b-live-static.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.
