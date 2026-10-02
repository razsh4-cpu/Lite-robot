---
schema: bipolix.test_session/v1
id: TEST-20261002-017
title: Home_Map mapping and save/load historical operation
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PASS
categories: LOCALIZATION, SENSORS
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20261002-017 — Home_Map mapping and save/load historical operation

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: UNKNOWN; Day-1 historical operation.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

The Day-1 closeout and PDF summaries report RPLIDAR mapping and saved Home_Map operation. Mapping creates a map; AMCL localizes against an existing map. Exact map-save transcripts, map hashes, metadata revisions, failed attempts, and per-run timestamps are missing. The localization gate session is related but does not itself prove each map-save or restore operation. This record preserves the reported historical use without inventing a map manifest.

## Evidence and follow-up

- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p1.
- [TEST_CATALOG.md](../../testing/TEST_CATALOG.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [TEST-20260927-003](TEST-20260927-003-home-map-localization.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
