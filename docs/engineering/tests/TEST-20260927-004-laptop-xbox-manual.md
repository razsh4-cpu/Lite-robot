---
schema: bipolix.test_session/v1
id: TEST-20260927-004
title: Laptop Xbox guarded manual control path
date: 2026-09-27
classification: PHYSICALLY_PROVEN
result: PASS
categories: XBOX, ROBOT_CONTROL, SAFETY
robot_id: robot_01
git_sha: abf9900
evidence: docs/testing/TEST_CATALOG.md
---

# TEST-20260927-004 — Laptop Xbox guarded manual path

Existing project records classify the laptop Xbox/C2 path and safe release as
physically proven during manual localization/posture work. It used the
exclusive `LAPTOP_XBOX` source rather than a second low-level controller.

- Primary evidence: [test catalog T005/T006](../../testing/TEST_CATALOG.md),
  [known-good baseline](../../testing/KNOWN_GOOD_BASELINE.md), and
  [component inventory](../../architecture/COMPONENT_INVENTORY.md).
- Exact per-axis run log/video: `EVIDENCE MISSING`.
- Scope: this historical proof does not by itself prove the newer NOMAD
  Phase-3C browser→MQTT adapter.
