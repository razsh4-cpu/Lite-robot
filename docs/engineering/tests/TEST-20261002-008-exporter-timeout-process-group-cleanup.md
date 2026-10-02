---
schema: bipolix.test_session/v1
id: TEST-20261002-008
title: Exporter timeout process-group cleanup
date: 2026-10-02
classification: OFFLINE_PROVEN
result: PASS
categories: ROS2, RELIABILITY, PERFORMANCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/engineering/findings/FINDING-20261001-001-exporter-process-leak.md
---

# TEST-20261002-008 — Exporter timeout process-group cleanup

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: 2026-10-01 software change; exact incident/soak timestamps UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

The historical incident left ping responsive while SSH banner/service response degraded as timed-out ROS CLI probes accumulated children, tasks, and memory. Commit e396f55 terminates and reaps the full process group and adds regression coverage. This record preserves the incident as a historical claim and the code/regression as offline evidence. Exact live incident and post-fix soak metrics are missing; the software fix does not close the independent Wi-Fi risk.

## Evidence and follow-up

- [FINDING-20261001-001-exporter-process-leak.md](../findings/FINDING-20261001-001-exporter-process-leak.md).
- [PERFORMANCE_BASELINE.md](../../operations/PERFORMANCE_BASELINE.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: [FINDING-20261001-001](../findings/FINDING-20261001-001-exporter-process-leak.md).
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
