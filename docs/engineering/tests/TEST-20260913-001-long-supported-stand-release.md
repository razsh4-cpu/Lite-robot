---
schema: bipolix.test_session/v1
id: TEST-20260913-001
title: Long supported stand and controlled release
date: 2026-09-13
classification: PHYSICALLY_PROVEN
result: PASS
actual_behavior: Robot held TARGET_REACHED for about 203 seconds and returned to lying after explicit release
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: ac56328
evidence: docs/EXPERIMENTS.md E6-E8
---

# TEST-20260913-001 - Long supported stand and controlled release

A mechanically supported low-level stand reached standing, held for about 203 s,
and returned to lying after an explicit release. The operator observation and
retained tail metrics are physical evidence for that historical research build,
not for the current Product posture path.

- Observed: `TARGET_REACHED`; explicit release closed the joint-send gate and
  returned acquisition to `NOT_REQUESTED`; telemetry remained fresh.
- Retained tail: RMS max 0.0696 and maximum tracking error 0.0526 rad over the
  final 24.3 s; the bounded buffer did not retain the whole hold.
- Evidence: [Experiments E6-E8](../../EXPERIMENTS.md) and commit `ac56328`.
- Limitation: the original success transcript was not located, robot ID is
  unknown, and SDK ownership acknowledgement remained unavailable.
- Supersession: the indefinite hold policy was later replaced by a bounded
  absolute hold; see [FINDING-20260917-002](../findings/FINDING-20260917-002-absolute-stand-hold-deadline.md).

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
