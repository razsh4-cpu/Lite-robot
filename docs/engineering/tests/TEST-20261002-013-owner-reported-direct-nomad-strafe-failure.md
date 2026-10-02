---
schema: bipolix.test_session/v1
id: TEST-20261002-013
title: Owner-reported direct NOMAD strafe failure
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: FAIL
categories: NOMAD, ROBOT_CONTROL
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf p7/p10/p12
---

# TEST-20261002-013 — Owner-reported direct NOMAD strafe failure

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

The owner reports that direct NOMAD manual strafe was physically attempted and failed. Date, exact deployed path, command packets, state, and cause are UNKNOWN; no time-aligned raw command/yaw/displacement record was found in the retained audit sources. Historical PDF A explicitly says that its ROS adapter forced linear.y to zero and disabled lateral pending dedicated validation. The accepted Nav2 world-frame detour remains a recorded autonomous PASS, but does not independently identify body-frame linear.y. This record preserves the reported failed experiment without guessing a packet/sign/gate root cause.

## Evidence and follow-up

- [Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) p7/p10/p12.
- [LITE3_HISTORY_AUDIT.md](../../../../../Documents/NOMAD/docs/LITE3_HISTORY_AUDIT.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [TEST-20260927-001](TEST-20260927-001-chair-avoidance-interrupted.md), [TEST-20260927-002](TEST-20260927-002-chair-avoidance-pass.md), [FINDING-20261002-005](../findings/FINDING-20261002-005-independent-body-frame-strafe-physical-proof-remains-incomplete.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
