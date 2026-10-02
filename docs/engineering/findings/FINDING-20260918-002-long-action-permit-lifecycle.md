---
schema: bipolix.engineering_finding/v1
id: FINDING-20260918-002
title: Longer low-level actions exposed permit-lifecycle ambiguity
date: 2026-09-18
status: HISTORICAL
categories: ROBOT_CONTROL, SAFETY, R_AND_D
evidence: docs/handoff/HANDOFF_2026-09-18_LEG_LIFT.md
---

# FINDING-20260918-002 - Long-action permit lifecycle ambiguity

A longer body-shift/leg-lift action aborted with a generic guard failure while
the last reported tilt, speed, and tracking values remained within limits. The
handoff identified expiry of a permit renewed only at action entry as the
leading hypothesis.

- Evidence: [TEST-20260918-003](../tests/TEST-20260918-003-body-shift-guard-abort.md)
  and [historical handoff](../../handoff/HANDOFF_2026-09-18_LEG_LIFT.md).
- Root cause: `INCONCLUSIVE`; the primary trace is an uncommitted `/tmp` path.
- Lesson: log the exact failed predicate and distinguish renewable health from
  absolute duration before changing limits or retrying hardware.
- DO NOT REPEAT: increase lift or weaken guards to get past a generic abort.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
