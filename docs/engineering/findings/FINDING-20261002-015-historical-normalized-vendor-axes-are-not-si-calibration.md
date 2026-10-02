---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-015
title: Historical normalized vendor axes are not SI calibration
date: 2026-10-02
status: CURRENT
categories: ROBOT_CONTROL, ROS2, SAFETY
evidence: /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf p7/p12
---

# FINDING-20261002-015 — Historical normalized vendor axes are not SI calibration

PDF A records conservative normalized caps x ±0.10 and yaw ±0.25, with x
+0.10→raw +9174, x -0.10→raw -9175, yaw +0.25→raw -13107, and yaw
-0.25→raw +13106. Preserve sign inversion and asymmetric conversion. Those
values are explicitly not calibrated m/s or rad/s. The x +0.10 / yaw +0.15
curve of about 0.77 s had y=0; the historical adapter disabled lateral pending
dedicated validation. Protocol case 0x0131 existence does not prove strafe.

Current NOMAD uses a separate SI-scaled path. Its sign, scale, and physical
axis acceptance need their own evidence; copying historical gains or rates
does not supply it. Publication rates for the later PDF-mentioned ROS runs
are `UNKNOWN`, distinct from the earlier 20 Hz first-pulse investigation.

- [PDF A](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) pp6–8/10/12.
- [Backward report](../tests/TEST-20261002-021-historical-ros-vendor-backward-motion.md).
- [Yaw report](../tests/TEST-20261002-022-historical-ros-vendor-yaw-in-both-directions.md).
- [Curve report](../tests/TEST-20261002-023-historical-ros-forward-and-yaw-curved-motion.md).
- [Neutral/shutdown report](../tests/TEST-20261002-024-historical-ros-deadman-release-neutral-and-shutdown.md).
- DO NOT REPEAT: treat normalized command fractions, a curve, or protocol syntax
  as calibrated SI motion or independent body-frame lateral proof.
