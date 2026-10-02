---
schema: bipolix.test_session/v1
id: TEST-20260917-002
title: Separate stand authorization expired before request
date: 2026-09-17
classification: FAILED
result: FAIL
actual_behavior: Five-second authorization expired before stand input; the robot did not move and the gate stayed closed
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: 2568136
evidence: docs/SUPPORTED_STAND_RESULT_2026-09-17.md
---

# TEST-20260917-002 - Separate stand authorization expired before request

The approved attempt did not actuate. Remote/console latency exceeded the
five-second gap between `authorize_stand` and the separate `stand` request. The
state machine failed closed, requested release, and rejected the late request.

- Final state: idle, `joint_send_enabled=0`, zero software velocity,
  acquisition/ownership `NOT_REQUESTED`; no retry.
- Evidence: [attempt result](../../SUPPORTED_STAND_RESULT_2026-09-17.md) and
  commit `2568136`.
- Fix/relationship: atomic `stand_once` removed the inter-command gap; see
  [FINDING-20260917-001](../findings/FINDING-20260917-001-atomic-stand-authorization.md)
  and later [TEST-20260917-001](TEST-20260917-001-supported-stand.md).

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
