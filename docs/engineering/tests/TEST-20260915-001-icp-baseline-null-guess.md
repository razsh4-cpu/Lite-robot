---
schema: bipolix.test_session/v1
id: TEST-20260915-001
title: ICP baseline rejection and null-guess cascade
date: 2026-09-15
classification: FAILED
result: FAIL
actual_behavior: Baseline replay stopped odometry after a 0.646 correspondence ratio was rejected by the 0.70 threshold
categories: ODOMETRY, ROS2, R_AND_D
robot_id: UNKNOWN
git_sha: f765a2b
evidence: onboard_ros2_ws/src/sensor_visualization/docs/ICP_ODOMETRY_OFFLINE_2026-09-15.md
---

# TEST-20260915-001 - ICP baseline rejection and null-guess cascade

Offline replay of a recorded real scan sequence reproduced the baseline failure:
coverage stopped at 4.695/9 s when a 0.646030 correspondence ratio was rejected
by the 0.70 threshold, followed by 76 null-guess errors while `/scan` continued.

- Evidence: [ICP investigation](../../../onboard_ros2_ws/src/sensor_visualization/docs/ICP_ODOMETRY_OFFLINE_2026-09-15.md)
  and retained replay logs under `logs/icp_replay/`.
- Related finding: [FINDING-20260915-001](../findings/FINDING-20260915-001-icp-null-guess.md).
- Boundary: recorded hardware input plus offline replay is not a new physical
  odometry test and does not make ICP Product authority.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
