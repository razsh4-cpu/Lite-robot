---
schema: bipolix.test_session/v1
id: TEST-20260918-001
title: Supported body-shift physical progression
date: 2026-09-18
classification: HISTORICAL_CLAIM
result: PASS
actual_behavior: Handoff records report successful 6 mm, 10 mm, and 15 mm supported shifts
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: fe22943
evidence: docs/handoff/HANDOFF_2026-09-18_LEG_LIFT.md
---

# TEST-20260918-001 - Supported body-shift physical progression

The contemporary handoff reports that mechanically supported body shifts of
6 mm, 10 mm, and 15 mm worked, and that 15 mm was selected for later leg-lift
experiments.

- Evidence: [leg-lift handoff](../../handoff/HANDOFF_2026-09-18_LEG_LIFT.md)
  and commit `fe22943`.
- Classification rationale: the document is a direct historical report, but
  exact per-run timestamps, complete traces, acceptance criteria, and operator
  observations are not retained in Git.
- Boundary: this is low-level R&D evidence, not Product gait capability and not
  authorization to repeat a trajectory.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
