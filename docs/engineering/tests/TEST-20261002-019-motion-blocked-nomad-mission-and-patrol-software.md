---
schema: bipolix.test_session/v1
id: TEST-20261002-019
title: Motion-blocked NOMAD Mission and Patrol software
date: 2026-10-02
classification: OFFLINE_PROVEN
result: PASS
categories: NOMAD, NAVIGATION, MQTT
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/ros-robot-cc/NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md
---

# TEST-20261002-019 — Motion-blocked NOMAD Mission and Patrol software

## Retrospective provenance and acceptance

Recorded on 2026-10-02 from retained evidence. Actual experiment date: 2026-10-01 software record; exact offline run timestamp UNKNOWN.
Exact operator, site, robot serial, and physical-run deployment manifest are
`UNKNOWN`. Related source commits identify software history, not an exact run
SHA. This record does not authorize an experiment or report a new run.

Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless supplied
by the primary report. The objective of this capture is to preserve failure,
fix, retest, and remaining proof boundaries without inventing missing stages.

## Procedure, observation, and result

Commit c3c3e96 and the non-motion MVP record describe deterministic MOCK Mission/Patrol contracts and preview behavior with motion_commands_supported=false and physical_output_performed=false. Later real Mini-PC negative-path validation rejected requests while the robot was offline. The software/mock result does not prove physical NOMAD mission arrival, cancellation, multi-goal patrol, pause/resume, takeover, or obstacle response. Standalone prior chair success does not transfer to this orchestration path.

## Evidence and follow-up

- [BIPOLIX_NON_MOTION_MVP.md](../../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).

- Raw logs/bag/video: `EVIDENCE MISSING` unless explicitly retained by the source.
- Related records: NONE.
- Preserve the result at its recorded scope; a software pass does not establish
  physical safety, deployment identity, or an unrecorded later retest.
