---
schema: bipolix.test_session/v1
id: TEST-20260927-003
title: Home_Map localization acceptance gate
date: 2026-09-27
classification: LIVE_STATIC_PROVEN
result: PASS
categories: LOCALIZATION, TF, SENSORS
robot_id: robot_01
git_sha: abf9900
evidence: docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20260927-003 — Home_Map localization acceptance

The saved map, LiDAR alignment, AMCL pose, and required TF chain supported the
three-consecutive-sample `>=80%` navigation gate. The accepted chair session
ended around 95.4%. Saved pose is only an initial hypothesis; global fallback
and short operator-assisted disambiguation remain part of the documented flow.

- Primary evidence: [Day-2 closeout](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md),
  [test catalog T010](../../testing/TEST_CATALOG.md).
- Map origin, LiDAR extrinsics, and AMCL tuning were not changed to force the
  result.
