---
schema: bipolix.test_session/v1
id: TEST-20261002-010
title: Wrong-map localization and active-map preflight repair
date: 2026-10-02
classification: PARTIAL
result: PARTIAL
categories: LOCALIZATION, DEPLOYMENT
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# TEST-20261002-010 — Wrong-map localization and active-map preflight repair

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: 2026-09-28 written finding; exact experiment timestamp UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

Stable 75–79% scan-match scores in a new environment were associated with selecting the old Home_Map. Tooling and the runbook were changed to expose the active YAML before interpreting confidence or offering an override. The reusable finding records the software repair; the operations KB still qualifies live deployment verification with the intended map. This record therefore remains PARTIAL and does not invent a post-fix exact confidence sequence or calibration change.

## Evidence and follow-up

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [FAILURES_AND_FIXES.md](../../FAILURES_AND_FIXES.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20260928-001](../findings/FINDING-20260928-001-active-map-identity.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
