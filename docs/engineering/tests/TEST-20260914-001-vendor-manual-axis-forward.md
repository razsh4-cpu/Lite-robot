---
schema: bipolix.test_session/v1
id: TEST-20260914-001
title: Bounded vendor manual-axis forward pulse
date: 2026-09-14
classification: PHYSICALLY_PROVEN
result: PASS
actual_behavior: A bounded external SimpleCMD pulse produced operator-confirmed forward locomotion and neutral recovery
categories: ROBOT_CONTROL, SAFETY, XBOX
robot_id: UNKNOWN
git_sha: ac56328
evidence: docs/HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md
---

# TEST-20260914-001 - Bounded vendor manual-axis forward pulse

One explicitly approved 0.30 s forward pulse at normalized approximately +0.10
entered the robot-matched vendor `jy_exe` gait path and produced
operator-confirmed physical forward motion. Neutral streams preceded and
followed the pulse; post-state was `6/0/0` at 57% battery.

- Exact path: 12-byte SimpleCMD `0x21010130`, raw 9174, UDP to
  `192.168.1.120:43893`; lateral and yaw remained zero.
- Evidence: [high-level investigation](../../HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md)
  and [Experiments E11-E13](../../EXPERIMENTS.md).
- Related finding: [FINDING-20260914-001](../findings/FINDING-20260914-001-vendor-manual-axis-protocol.md).
- Boundary: no backward/lateral/yaw or continuous teleoperation was proven; the
  referenced `/tmp` JSONL is not committed.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
