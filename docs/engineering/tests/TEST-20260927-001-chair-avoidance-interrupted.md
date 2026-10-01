---
schema: bipolix.test_session/v1
id: TEST-20260927-001
title: Chair avoidance attempt interrupted by power loss
date: 2026-09-27
classification: PARTIAL
result: PARTIAL
categories: NAVIGATION, SAFETY, HARDWARE
robot_id: robot_01
git_sha: abf9900
evidence: docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20260927-001 — Chair avoidance interrupted

The Lite3 detected and passed the chair and travelled about 1.64 m with
localization around 92%, exercising forward/lateral/yaw through the product
path. Mini-PC power/link interruption prevented proof of terminal goal result
and final release, so this is not a PASS.

- Primary evidence: [Day-2 closeout](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- Root cause supported by the record: external power/cable interruption; no
  Nav2 planner/controller root cause was established.
- Follow-up: the later accepted session is
  [TEST-20260927-002](TEST-20260927-002-chair-avoidance-pass.md).
