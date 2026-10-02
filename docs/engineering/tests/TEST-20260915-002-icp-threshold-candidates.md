---
schema: bipolix.test_session/v1
id: TEST-20260915-002
title: ICP correspondence-threshold replay candidates
date: 2026-09-15
classification: OFFLINE_PROVEN
result: PASS
actual_behavior: Ratio 0.30 and 0.50 replay candidates completed the selected motion windows without null-guess failure
categories: ODOMETRY, ROS2, R_AND_D
robot_id: UNKNOWN
git_sha: f765a2b
evidence: onboard_ros2_ws/src/sensor_visualization/docs/ICP_ODOMETRY_OFFLINE_2026-09-15.md
---

# TEST-20260915-002 - ICP correspondence-threshold replay candidates

Controlled offline replays changed only the correspondence threshold. Ratios
0.30 and 0.50 completed 8.791/9 s of the final-motion window (89 odometry
outputs/90 scans); the 0.50 candidate also completed earlier and middle pulses.

- Evidence: [ICP investigation](../../../onboard_ros2_ws/src/sensor_visualization/docs/ICP_ODOMETRY_OFFLINE_2026-09-15.md)
  and the corresponding retained JSON/log pairs under `logs/icp_replay/`.
- Relationship: follows failed [TEST-20260915-001](TEST-20260915-001-icp-baseline-null-guess.md).
- Boundary: these are replay candidates only. Product odometry now comes from
  HIGH-LEVEL telemetry, and no candidate was promoted to physical proof.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
