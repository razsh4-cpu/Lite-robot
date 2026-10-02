---
schema: bipolix.test_session/v1
id: TEST-20261002-023
title: Historical ROS forward-and-yaw curved motion
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PASS
categories: ROBOT_CONTROL, ROS2, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf p7–8; /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p5–6
---

# TEST-20261002-023 — Historical ROS forward-and-yaw curved motion

## Retrospective provenance and result

Capture date: 2026-10-02. Actual physical-run date, site, robot serial, operator,
and exact run SHA are `UNKNOWN`. This records a retained retrospective physical
report, not a new test or independently reproducible physical certification.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN`.

A pp7–8 and B pp5–6 report a stronger curve with normalized x=+0.10 and z=+0.15 for about 0.77 s, with y=0; forward travel and turning were reported observed. The curve is not direct strafe proof and normalized values are not calibrated m/s or rad/s. Exact run date, independent measured trajectory, and raw log/video are missing.

## Evidence and relationships

- [PDF A](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) p7–8.
- [PDF B](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) pp5–6.
- Related first forward pulse: [TEST-20260914-001](TEST-20260914-001-vendor-manual-axis-forward.md).
- Raw logs/bag/video and deployment manifest: `EVIDENCE MISSING`.
- Do not transfer this historical path's result to current SI-scaled NOMAD
  control, another axis, or a different deadman contract.
