---
schema: bipolix.test_session/v1
id: TEST-20261002-004
title: HIGH-LEVEL robot stand temporary-lease acceptance
date: 2026-10-02
classification: PHYSICALLY_PROVEN
result: PASS
categories: ROBOT_CONTROL, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20261002-004 — HIGH-LEVEL robot stand temporary-lease acceptance

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: Reported by 2026-09-27 closeout; exact run timestamp UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

The retrospective Day-1/Day-2 summary reports that robot stand lost its temporary lease; neutral heartbeat and removal of competing C2 fixed the issue. The contemporary closeout reports the accepted HIGH-LEVEL CLI run: SITTING to STANDING in real telemetry, no forward/lateral/yaw velocity, posture command stopped, and temporary lease released to COMMAND_SOURCE=NONE. The failure cause and fix are retrospective written reports; the accepted result is the contemporary physical report. This product posture path is separate from the low-level supported Stand and from current NOMAD browser Stand.

## Evidence and follow-up

- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p8.
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [TEST-20260927-004](TEST-20260927-004-laptop-xbox-manual.md), [FINDING-20260930-001](../findings/FINDING-20260930-001-command-authority.md), [FINDING-20261002-008](../findings/FINDING-20261002-008-temporary-high-level-posture-leases-need-neutral-continuity.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
