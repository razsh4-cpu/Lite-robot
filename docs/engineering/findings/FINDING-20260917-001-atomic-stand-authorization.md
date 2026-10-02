---
schema: bipolix.engineering_finding/v1
id: FINDING-20260917-001
title: Time-bounded authorization and action must be atomic
date: 2026-09-17
status: RESOLVED
categories: ROBOT_CONTROL, SAFETY, R_AND_D
evidence: docs/SUPPORTED_STAND_RESULT_2026-09-17.md
---

# FINDING-20260917-001 - Atomic stand authorization

Separating a five-second authorization from the following console action allowed
remote/output latency to consume the permit before the request was accepted.
The safe failure caused no motion, but wasted an approved physical attempt.

- Failure: [TEST-20260917-002](../tests/TEST-20260917-002-stand-authorization-expiry.md).
- Fix: `stand_once` holds the lifecycle lock while it arms and queues exactly one
  request; no gains, target, send gate, or algorithm were loosened.
- Validation: later [TEST-20260917-001](../tests/TEST-20260917-001-supported-stand.md)
  reached standing.
- Lesson: make short-lived authorization plus action submission one atomic API.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
