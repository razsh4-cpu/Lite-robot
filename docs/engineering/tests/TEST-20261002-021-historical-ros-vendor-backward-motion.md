---
schema: bipolix.test_session/v1
id: TEST-20261002-021
title: Historical ROS vendor backward motion
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PASS
categories: ROBOT_CONTROL, ROS2, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf p6–7/p12; /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p5–6
---

# TEST-20261002-021 — Historical ROS vendor backward motion

## Retrospective provenance and result

Capture date: 2026-10-02. Actual physical-run date, site, robot serial, operator,
and exact run SHA are `UNKNOWN`. This records a retained retrospective physical
report, not a new test or independently reproducible physical certification.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN`.

A pp6–7/12 and B pp5–6 report backward physical motion through the vendor axis/ROS path. A retains normalized x=-0.10 mapping to raw -9175; forward +0.10 maps to +9174, preserving asymmetry. The separate first bounded forward pulse remains TEST-20260914-001 and is not repeated here as a new independent PASS. Run dates, publication rate for these later ROS runs, measured SI scale, and raw per-run log/video are missing.

## Evidence and relationships

- [PDF A](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) p6–7/p12.
- [PDF B](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) pp5–6.
- Related first forward pulse: [TEST-20260914-001](TEST-20260914-001-vendor-manual-axis-forward.md).
- Raw logs/bag/video and deployment manifest: `EVIDENCE MISSING`.
- Do not transfer this historical path's result to current SI-scaled NOMAD
  control, another axis, or a different deadman contract.
