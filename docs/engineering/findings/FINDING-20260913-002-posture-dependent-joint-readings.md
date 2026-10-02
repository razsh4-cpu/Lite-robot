---
schema: bipolix.engineering_finding/v1
id: FINDING-20260913-002
title: Joint readings changed after normal lying preparation without mapping edits
date: 2026-09-13
status: HISTORICAL
categories: ROBOT_CONTROL, HARDWARE, R_AND_D
evidence: docs/EXPERIMENTS.md E2-E5
---

# FINDING-20260913-002 - Posture-dependent joint readings

Abnormal right HipY readings that blocked a later attempt disappeared after a
normal battery/startup/original-controller lying procedure. No sign, mapping,
gain, range, or target change was made. A 35 s passive observation then recorded
34,999 finite callbacks with all joints inside unchanged ranges.

- Evidence: [Experiments E2-E5](../../EXPERIMENTS.md) and retained handoff
  snapshots under `docs/handoff_evidence/20260913/`.
- Lesson: reproduce physical posture/startup state before diagnosing a mapping
  defect from one raw telemetry snapshot.
- Limitation: battery reset versus leg arrangement was not isolated; this does
  not prove firmware calibration behavior.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
