---
schema: bipolix.test_session/v1
id: TEST-20260913-002
title: Bounded RL-zero and stop release
date: 2026-09-13
classification: PHYSICALLY_PROVEN
result: PASS
actual_behavior: Two supported zero-input RL runs remained stable and released safely
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: ac56328
evidence: docs/EXPERIMENTS.md E9-E10
---

# TEST-20260913-002 - Bounded RL-zero and stop release

Two mechanically supported zero-input RL sessions completed on hardware. One
ran to its 5.0000066 s deadline (412 policy cycles); the second was explicitly
stopped at 1.4127 s (117 cycles). Recorded normalized input remained `0,0,0`.

- Result: operator reported physical stability and safe return to lying; the
  gate closed and acquisition returned to `NOT_REQUESTED`.
- Evidence: [Experiments E9-E10](../../EXPERIMENTS.md), incorporated by
  commit `ac56328`.
- Boundary: this proves neither nonzero policy input nor locomotion. Do not use
  zero-input stability to authorize RL gait motion.
- Limitation: primary `/tmp` traces were referenced but are not committed.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
