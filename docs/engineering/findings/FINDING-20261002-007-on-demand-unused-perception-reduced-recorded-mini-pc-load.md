---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-007
title: On-demand unused perception reduced recorded Mini-PC load
date: 2026-10-02
status: CURRENT
categories: PERFORMANCE, MINI_PC
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/PERFORMANCE_BASELINE.md
---

# FINDING-20261002-007 — On-demand unused perception reduced recorded Mini-PC load

## Finding and applicability

Headless boot, laptop-side RViz, and unused D455 on demand reduced the recorded load/RAM snapshots while keeping robot-critical work onboard. These snapshots do not establish sustained headroom, thermal margin, scheduling jitter, or mission-load reliability. Measure the actual workload and limiting resource before further optimization.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [PERFORMANCE_BASELINE.md](../../operations/PERFORMANCE_BASELINE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p9.
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.

- Related records: [TEST-20261002-007](../tests/TEST-20261002-007-headless-mini-pc-and-on-demand-workload-snapshots.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
