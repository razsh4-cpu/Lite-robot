---
schema: bipolix.engineering_finding/v1
id: FINDING-20260918-001
title: Low-level validation foot-force channels were zero
date: 2026-09-18
status: KNOWN_ISSUE
categories: SENSORS, HARDWARE, ROBOT_CONTROL, R_AND_D
evidence: docs/handoff/HANDOFF_2026-09-18_LEG_LIFT.md
---

# FINDING-20260918-001 - Low-level foot force unavailable

Contact-force values changed during passive vendor gait observation, but all
four channels were zero during the custom low-level validation runs. They could
not establish FR unloading before the historical lift attempts.

- Evidence: [leg-lift handoff](../../handoff/HANDOFF_2026-09-18_LEG_LIFT.md)
  and [real-test readiness](../../REAL_TEST_READINESS_2026-09-17.md).
- Affected session: [TEST-20260918-002](../tests/TEST-20260918-002-fr-leg-lift-attempts.md).
- DO NOT REPEAT: infer unloading from zero channels, video clearance alone, or
  support-triangle geometry. Use independently calibrated load evidence before
  a future unloading claim.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
