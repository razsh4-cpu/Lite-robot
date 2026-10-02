---
schema: bipolix.engineering_finding/v1
id: FINDING-20260917-002
title: Renewable health permits must not extend an absolute action deadline
date: 2026-09-17
status: RESOLVED
categories: ROBOT_CONTROL, SAFETY, R_AND_D
evidence: docs/SUPPORTED_STAND_SUCCESS_2026-09-17.md
---

# FINDING-20260917-002 - Absolute stand hold deadline

Fresh `TARGET_REACHED` samples renewed a private health permit, unintentionally
allowing a successful low-level stand to hold indefinitely instead of releasing
after two seconds. Operator `stop` safely closed the gate in the observed run.

- Fix: an independent absolute deadline starts at first `TARGET_REACHED` and
  uses the shared abort/release path; health renewal cannot extend it.
- Evidence: [stand success and discrepancy](../../SUPPORTED_STAND_SUCCESS_2026-09-17.md).
- Validation: offline suite 13/13 and partial physical/software acceptance in
  [TEST-20260917-003](../tests/TEST-20260917-003-stand-automatic-release.md).
- Lesson: separate renewable liveness permits from non-renewable action budgets.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
