---
schema: bipolix.test_session/v1
id: TEST-20261002-024
title: Historical ROS deadman release neutral and shutdown
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PASS
categories: ROBOT_CONTROL, ROS2, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf p7–9/p12; /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p5–6
---

# TEST-20261002-024 — Historical ROS deadman release neutral and shutdown

## Retrospective provenance and result

Capture date: 2026-10-02. Actual physical-run date, site, robot serial, operator,
and exact run SHA are `UNKNOWN`. This records a retained retrospective physical
report, not a new test or independently reproducible physical certification.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN`.

A p7 reports physical deadman release, automatic zero, and clean shutdown through the historical ROS path; its axis node sends five neutral packets on shutdown. The historical gates require fresh input, fresh true deadman, fresh telemetry/state 6, battery at least 25%, finite values, and no competing controller, with a 300 ms timeout and transmit default false. Missing exact run timing/trace means no independently measured stop-latency claim. Legacy Xbox RB edge authorization and current Phase-3C continuous RB must remain distinct contracts.

## Evidence and relationships

- [PDF A](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) p7–9/p12.
- [PDF B](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) pp5–6.
- Related first forward pulse: [TEST-20260914-001](TEST-20260914-001-vendor-manual-axis-forward.md).
- Raw logs/bag/video and deployment manifest: `EVIDENCE MISSING`.
- Do not transfer this historical path's result to current SI-scaled NOMAD
  control, another axis, or a different deadman contract.
