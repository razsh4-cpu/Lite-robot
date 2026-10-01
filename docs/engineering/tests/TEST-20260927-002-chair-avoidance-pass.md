---
schema: bipolix.test_session/v1
id: TEST-20260927-002
title: Accepted physical Nav2 chair avoidance
date: 2026-09-27
classification: PHYSICALLY_PROVEN
result: PASS
categories: NAVIGATION, LOCALIZATION, SAFETY, SENSORS
robot_id: robot_01
git_sha: abf9900
evidence: docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# TEST-20260927-002 — Accepted physical Nav2 chair avoidance

LiDAR/costmaps detected a real chair; Nav2 selected a right-side path of about
1.47 m; `NavigateToPose` returned `SUCCEEDED` (`error_code=0`); the robot
cleared the chair without recorded contact and stopped. Final localization was
about 95.4%, AUTONOMY released, and final `COMMAND_SOURCE=NONE`.

- Path: Nav2 → `/cmd_vel` → AUTONOMY → arbiter → HIGH-LEVEL → vendor gait.
- Limits: 0.10 m/s forward/back, 0.05 m/s lateral, 0.20 rad/s yaw.
- Primary evidence: [Day-2 closeout](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md)
  and [known-good baseline](../../testing/KNOWN_GOOD_BASELINE.md).
- Limitation: exact installed package hashes at the instant of the run were not
  captured; `abf9900` is the strongest repository baseline.
