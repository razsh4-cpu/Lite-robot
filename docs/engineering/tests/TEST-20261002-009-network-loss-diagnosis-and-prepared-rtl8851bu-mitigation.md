---
schema: bipolix.test_session/v1
id: TEST-20261002-009
title: Network-loss diagnosis and prepared rtl8851bu mitigation
date: 2026-10-02
classification: PARTIAL
result: PARTIAL
categories: NETWORKING, MINI_PC, RELIABILITY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20261002-009 — Network-loss diagnosis and prepared rtl8851bu mitigation

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: Reported by 2026-09-27 closeout; exact incident timestamps UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

Intermittent Mini-PC network/SSH loss occurred without a proven panic, OOM, thermal shutdown, or filesystem failure. The strongest reported evidence was rtl8851bu UBSAN array-index errors with concurrent station/AP-style interfaces. Station-only NetworkManager policy, unmanaged AP interface, disabled power saving, and preserved address were prepared. Preparation is not an accepted installation or long-soak result. Repeated boot and mission-load reliability closure remain open, separate from power interruption, exporter resource starvation, and MQTT addressing.

## Evidence and follow-up

- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p9–10.
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20260927-002](../findings/FINDING-20260927-002-rtl8851bu.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
