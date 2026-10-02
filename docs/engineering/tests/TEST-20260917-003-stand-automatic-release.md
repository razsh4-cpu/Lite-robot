---
schema: bipolix.test_session/v1
id: TEST-20260917-003
title: Supported stand automatic release
date: 2026-09-17
classification: PARTIAL
result: PARTIAL
actual_behavior: Software trace passed the two-second automatic-release contract; operator reported normal stand and return but independent physical evidence is incomplete
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: 11b5ad4
evidence: docs/SUPPORTED_STAND_AUTO_RELEASE_RESULT_2026-09-17.md
---

# TEST-20260917-003 - Supported stand automatic release

The software sequence reached `TARGET_REACHED` and automatically entered
`ABORTING`/`RELEASE_REQUESTED` after a measured 2.0005399 s hold. The trace had
5,372 records, maximum tracking error 0.0823028 rad, and no dropped records.

- Operator observation: robot stood normally and returned to the ground.
- Evidence: [automatic-release result](../../SUPPORTED_STAND_AUTO_RELEASE_RESULT_2026-09-17.md)
  and commit `86b0d04`; external evidence files are named with SHA-256 hashes in
  that report but are not present in this repository.
- Classification rationale: software acceptance passed, while independent
  physical evidence and final posture measurement are incomplete.
- Related finding: [FINDING-20260917-002](../findings/FINDING-20260917-002-absolute-stand-hold-deadline.md).

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
