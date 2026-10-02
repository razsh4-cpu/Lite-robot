---
schema: bipolix.test_session/v1
id: TEST-20260918-002
title: Supported front-right leg-lift attempts
date: 2026-09-18
classification: PARTIAL
result: PARTIAL
actual_behavior: Correct-direction joint motion occurred but no visible foot clearance was established
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: fe22943
evidence: docs/handoff/HANDOFF_2026-09-18_LEG_LIFT.md
---

# TEST-20260918-002 - Supported front-right leg-lift attempts

The historical handoff records physical Cartesian FR targets of 1, 2, 5, 10,
and later 20 mm. Motion occurred in the intended direction, but no visible
ground clearance was established; a 5 mm request produced about 2.73 mm FK
motion relative to the body.

- Evidence: [leg-lift handoff](../../handoff/HANDOFF_2026-09-18_LEG_LIFT.md).
- Interpretation: leg loading/compliance and inadequate static transfer were
  hypotheses, not proven root causes.
- Related finding: [FINDING-20260918-001](../findings/FINDING-20260918-001-low-level-foot-force-unavailable.md).
- Boundary: no successful physical leg lift was demonstrated. Do not increase
  lift distance or replay these commands from this record.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
