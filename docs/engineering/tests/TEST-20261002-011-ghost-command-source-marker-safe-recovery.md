---
schema: bipolix.test_session/v1
id: TEST-20261002-011
title: Ghost command-source marker safe recovery
date: 2026-10-02
classification: PARTIAL
result: PARTIAL
categories: SAFETY, ROBOT_CONTROL
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# TEST-20261002-011 — Ghost command-source marker safe recovery

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: Reported by 2026-09-27 closeout; exact run timestamp UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

A LAPTOP_XBOX or AUTONOMY marker could remain after the real owner had exited or failed, blocking later acquisition. The reported live recovery used the existing neutral/zero, cancellation, and release path and restored NONE. A marker alone is not the kernel lock or a live process. All-source cleanup parity remains a documented regression target; the live workaround does not establish complete resolution.

## Evidence and follow-up

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p1.
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p7.

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [TEST-20260927-004](TEST-20260927-004-laptop-xbox-manual.md), [TEST-20260929-001](TEST-20260929-001-relocalize-approval.md), [FINDING-20260930-001](../findings/FINDING-20260930-001-command-authority.md), [FINDING-20261002-002](../findings/FINDING-20261002-002-command-source-markers-do-not-establish-real-ownership.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
