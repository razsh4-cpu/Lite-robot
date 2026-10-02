---
schema: bipolix.test_session/v1
id: TEST-20261002-012
title: NavFn path-tangent clearance correction
date: 2026-10-02
classification: OFFLINE_PROVEN
result: PASS
categories: NAVIGATION, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# TEST-20261002-012 — NavFn path-tangent clearance correction

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: Reported by 2026-09-27 closeout; exact regression timestamp UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

Curved NavFn paths commonly contained yaw=0, which the independent checker incorrectly interpreted as body orientation. This produced false collision or clearance results for the rectangular footprint. The checker now derives local path tangent after the start pose; the closeout and operations KB report offline regression and dry-planning use. This software PASS does not prove that the defect caused the earlier 0.00 m chair refusal or reconstruct the missing 8 mm snapshot.

## Evidence and follow-up

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20261002-006](../findings/FINDING-20261002-006-zero-yaw-navfn-poses-need-path-tangent-footprint-diagnostics.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
