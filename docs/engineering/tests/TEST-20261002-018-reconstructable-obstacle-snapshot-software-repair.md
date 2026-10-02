---
schema: bipolix.test_session/v1
id: TEST-20261002-018
title: Reconstructable obstacle snapshot software repair
date: 2026-10-02
classification: OFFLINE_PROVEN
result: PASS
categories: NAVIGATION, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# TEST-20261002-018 — Reconstructable obstacle snapshot software repair

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: 2026-09-28 wrapper software; original investigation timestamp UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

An 8 mm clearance claim could not later be reconstructed because the required scan, both costmaps, TF, paths, footprint/settings, and limiting pose/cell were not retained together. The bounded obstacle snapshot software now captures those inputs with per-pose and limiting-source evidence, and the operations KB reports offline regression coverage. This PASS covers the software repair. The original precision claim stays unauditable and the next installed live artifact set still requires verification.

## Evidence and follow-up

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [OBSTACLE_TEST.md](../../operations/OBSTACLE_TEST.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20260927-003](../findings/FINDING-20260927-003-obstacle-snapshot.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
