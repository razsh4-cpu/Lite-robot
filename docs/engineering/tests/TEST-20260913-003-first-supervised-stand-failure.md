---
schema: bipolix.test_session/v1
id: TEST-20260913-003
title: First supervised stand guard rejection
date: 2026-09-13
classification: FAILED
result: FAIL
actual_behavior: Stand entered STANDING_UP then aborted with send guard rejected output
categories: ROBOT_CONTROL, SAFETY, R_AND_D
robot_id: UNKNOWN
git_sha: ac56328
evidence: docs/EXPERIMENTS.md E2
---

# TEST-20260913-003 - First supervised stand guard rejection

The first recorded supervised stand entered `STANDING_UP`, produced slight
movement/noise, then failed closed through `ABORTING` and `RELEASE_REQUESTED`
with `send guard rejected output`. It did not reach standing.

- Evidence: [Experiments E2](../../EXPERIMENTS.md),
  [failures and fixes](../../FAILURES_AND_FIXES.md), and retained handoff
  evidence under `docs/handoff_evidence/20260913/`.
- Exact cause: `INCONCLUSIVE`; the historical log lacks synchronized
  target/measured vectors and branch-specific rejection.
- Follow-up: later successful stands do not erase this failure. Diagnostics,
  preflight, timing, and atomic authorization were improved before subsequent
  runs.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
