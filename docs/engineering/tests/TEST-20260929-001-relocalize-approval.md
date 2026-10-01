---
schema: bipolix.test_session/v1
id: TEST-20260929-001
title: Relocalize approval and cancellation safety
date: 2026-09-29
classification: OFFLINE_PROVEN
result: PASS
categories: LOCALIZATION, SAFETY, ROBOT_CONTROL
robot_id: robot_01
git_sha: b98a1af
evidence: tests/operator/test_lite3_relocalize_cli.py
---

# TEST-20260929-001 — Relocalize approval and cancellation

Focused offline tests verify read-only status, default-no approval, explicit
approval gating, deterministic/idempotent cancellation, zero/release cleanup,
and the `>=80%` ×3 success condition. No physical relocalization is claimed.

- Evidence: [`test_lite3_relocalize_cli.py`](../../../tests/operator/test_lite3_relocalize_cli.py)
  and [test catalog T011](../../testing/TEST_CATALOG.md).
- Dedicated physical CLI maneuver: `PARTIAL` in the historic catalog and still
  not promoted here.
