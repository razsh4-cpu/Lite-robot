---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-013
title: Configured LiDAR extrinsics are not complete calibration metrology
date: 2026-10-02
status: HISTORICAL
categories: TF, SENSORS
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/architecture/CONFIGURATION_CALIBRATION_DATA.md
---

# FINDING-20261002-013 — Configured LiDAR extrinsics are not complete calibration metrology

## Finding and applicability

Retained Lite launch/architecture defines base_link→lidar_link z=0.08 m and yaw=π, with AMCL owning map→odom and the sole runtime owning odom→base_link. PDFs report earlier orientation confusion and correction, but measurement method/date and calibration artifacts are incomplete. Preserve configuration provenance without claiming complete metrology. Do not copy these heights into a floor-projected base frame or create a competing TF publisher.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [CONFIGURATION_CALIBRATION_DATA.md](../../architecture/CONFIGURATION_CALIBRATION_DATA.md).
- [Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) p8.
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p4/p6/p11.

- Related records: [TEST-20260927-003](../tests/TEST-20260927-003-home-map-localization.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
