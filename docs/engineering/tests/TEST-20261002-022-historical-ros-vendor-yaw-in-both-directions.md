---
schema: bipolix.test_session/v1
id: TEST-20261002-022
title: Historical ROS vendor yaw in both directions
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PASS
categories: ROBOT_CONTROL, ROS2, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf p6–7/p12; /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p5–6
---

# TEST-20261002-022 — Historical ROS vendor yaw in both directions

## Retrospective provenance and result

Capture date: 2026-10-02. Actual physical-run date, site, robot serial, operator,
and exact run SHA are `UNKNOWN`. This records a retained retrospective physical
report, not a new test or independently reproducible physical certification.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN`.

A pp6–7/12 and B pp5–6 report physical yaw in both directions: normalized +0.25 maps to raw -13107 and -0.25 maps to +13106. These retained signs belong to that historical vendor path; they are not a measured rad/s calibration or a current NOMAD yaw-sign acceptance. Exact run date, deployed manifest, and raw trace are missing.

## Evidence and relationships

- [PDF A](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) p6–7/p12.
- [PDF B](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) pp5–6.
- Related first forward pulse: [TEST-20260914-001](TEST-20260914-001-vendor-manual-axis-forward.md).
- Raw logs/bag/video and deployment manifest: `EVIDENCE MISSING`.
- Do not transfer this historical path's result to current SI-scaled NOMAD
  control, another axis, or a different deadman contract.
