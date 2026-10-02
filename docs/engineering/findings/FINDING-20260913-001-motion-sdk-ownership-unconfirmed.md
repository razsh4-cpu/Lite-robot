---
schema: bipolix.engineering_finding/v1
id: FINDING-20260913-001
title: MotionSDK ownership request has no authoritative acknowledgement
date: 2026-09-13
status: CURRENT
categories: ROBOT_CONTROL, SAFETY, R_AND_D
evidence: docs/DECISIONS.md
---

# FINDING-20260913-001 - MotionSDK ownership remains unconfirmed

The low-level MotionSDK path can submit the existing acquisition request but
provides no authoritative positive ownership acknowledgement. Historical tools
therefore reported `REQUEST_SENT / OWNERSHIP_UNCONFIRMED` and kept the generic
joint gate closed unless a separate tightly scoped test permit applied.

- Evidence: [decisions](../../DECISIONS.md), [Experiments E1/E5](../../EXPERIMENTS.md),
  and retained acquisition/stand records.
- Known good: distinguish request submission from ownership and preserve the
  one-use, mechanically supported, fail-closed permit boundary.
- DO NOT REPEAT: infer authority from request transmission, telemetry reception,
  or lack of motion.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
