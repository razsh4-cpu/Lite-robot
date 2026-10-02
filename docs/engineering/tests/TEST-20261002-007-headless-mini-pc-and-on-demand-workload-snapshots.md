---
schema: bipolix.test_session/v1
id: TEST-20261002-007
title: Headless Mini-PC and on-demand workload snapshots
date: 2026-10-02
classification: LIVE_STATIC_PROVEN
result: PASS
categories: MINI_PC, PERFORMANCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/PERFORMANCE_BASELINE.md
---

# TEST-20261002-007 — Headless Mini-PC and on-demand workload snapshots

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: Reported by 2026-09-27 closeout; exact snapshot timestamps UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

The closeout records load 9.02 / 7.69 / 5.11, RAM about 1.7 GiB, and RealSense about 98% of one core before cleanup. After headless boot, laptop-side RViz, and unused RealSense on demand, load was 1.33 / 1.08 / 0.56, RAM about 1.0 GiB, and RealSense 0% when unused. Robot-critical services remained onboard. These are recorded before/after snapshots, not sustained workload, scheduling latency, thermal, headroom, or network-soak guarantees.

## Evidence and follow-up

- [PERFORMANCE_BASELINE.md](../../operations/PERFORMANCE_BASELINE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p9.
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20261002-007](../findings/FINDING-20261002-007-on-demand-unused-perception-reduced-recorded-mini-pc-load.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
