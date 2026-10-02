---
schema: bipolix.test_session/v1
id: TEST-20261002-005
title: Earlier chair planning safe refusal
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: NAVIGATION, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p8
---

# TEST-20261002-005 — Earlier chair planning safe refusal

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: UNKNOWN; earlier snapshot than final accepted closeout.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

PDF B p8 reports chair detection, 17 Nav2-valid paths, selection LEFT, a goal about 1.30 m forward and 0.60 m left, path length about 1.49 m, and independent minimum clearance 0.00 m at the initial pose. Motion remained NONE and Day 2 remained open in that snapshot. This is a preserved reported safety refusal, not a completed physical avoidance PASS. The PDF gives no candidate index. The raw snapshot is absent, so neither an actual initial collision nor the separate zero-yaw checker defect is established as its cause. Later power-interrupted and accepted chair runs remain separate records.

## Evidence and follow-up

- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p8.
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p3.

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20260927-003](../findings/FINDING-20260927-003-obstacle-snapshot.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
