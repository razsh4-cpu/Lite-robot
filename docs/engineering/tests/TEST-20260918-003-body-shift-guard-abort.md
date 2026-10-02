---
schema: bipolix.test_session/v1
id: TEST-20260918-003
title: Supported body-shift guard abort
date: 2026-09-18
classification: FAILED
result: FAIL
actual_behavior: A physical body-shift action aborted before leg lift with supported body shift guard failure
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: fe22943
evidence: docs/handoff/HANDOFF_2026-09-18_LEG_LIFT.md
---

# TEST-20260918-003 - Supported body-shift guard abort

The run progressed through `STANDING_UP` and `BODY_SHIFT_SHIFT_WEIGHT`, then
failed closed with `supported body shift guard failure` and requested release.
The trace contained about 4,148 records. Last reported roll, pitch, tracking
error, and raw speed were individually inside reviewed limits.

- Evidence: [leg-lift handoff](../../handoff/HANDOFF_2026-09-18_LEG_LIFT.md).
- Root cause status: `INCONCLUSIVE`. Permit expiry during the longer action was
  the leading hypothesis; it was not proven by the retained prose alone.
- Relationship: [FINDING-20260918-002](../findings/FINDING-20260918-002-long-action-permit-lifecycle.md).
- Boundary: the run never reached `BODY_SHIFT_LIFT_FR`.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
