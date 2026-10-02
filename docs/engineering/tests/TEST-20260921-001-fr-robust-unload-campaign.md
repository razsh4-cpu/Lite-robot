---
schema: bipolix.test_session/v1
id: TEST-20260921-001
title: Front-right robust unload simulation campaign
date: 2026-09-21
classification: FAILED
result: FAIL
actual_behavior: Eighty nominal candidates produced zero robust unload passes; lift search was not started
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: NOT_APPLICABLE
git_sha: 25b9865
evidence: docs/FR_ROBUST_SIMULATION_2026-09-21.md
---

# TEST-20260921-001 - Front-right robust unload simulation campaign

The isolated offline campaign evaluated 80 nominal body-only candidates and
three selected candidates across 100 paired model variations each. None met the
unload prerequisite, so no lift search was executed.

- Evidence: [campaign report](../../FR_ROBUST_SIMULATION_2026-09-21.md),
  retained JSON, and commit `25b9865`.
- Result boundary: safety-pass rates did not imply unloading; no trajectory was
  ready for hardware and no physical command was sent.
- Related finding: [FINDING-20260921-001](../findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md).

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
