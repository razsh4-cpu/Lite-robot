---
schema: bipolix.engineering_finding/v1
id: FINDING-20260914-002
title: Direct ONNX MotionSDK locomotion was not a reliable pilot path
date: 2026-09-14
status: DO_NOT_USE
categories: ROBOT_CONTROL, SAFETY, R_AND_D
evidence: docs/HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md
---

# FINDING-20260914-002 - Direct ONNX locomotion is not the pilot path

Multiple bounded physical forward trials through direct ONNX/MotionSDK joint
control produced lean/posture response, attempted stepping, and falls/releases
rather than safe useful translation. Model, nominal pose, stand height, timing,
observation/action contract, and last-action semantics also changed together
across upstream revisions, invalidating mixed comparisons.

- Evidence: [high-level investigation](../../HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md)
  and [policy root-cause record](../../POLICY_GAIT_ROOT_CAUSE_2026-09-14.md).
- Current alternative: the vendor gait controller via the guarded manual-axis
  path; see [TEST-20260914-001](../tests/TEST-20260914-001-vendor-manual-axis-forward.md).
- DO NOT REPEAT: treat simulation distance or a mixed policy/default/timing stack
  as physical locomotion readiness.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
