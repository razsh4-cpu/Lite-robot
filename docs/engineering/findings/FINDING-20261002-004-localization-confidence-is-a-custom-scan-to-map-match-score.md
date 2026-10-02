---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-004
title: Localization confidence is a custom scan-to-map match score
date: 2026-10-02
status: CURRENT
categories: LOCALIZATION, TF
evidence: /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p7
---

# FINDING-20261002-004 — Localization confidence is a custom scan-to-map match score

## Finding and applicability

The project localization guard uses scan wall-hit match fraction, not an official AMCL probability. PDF B reports a >80% diagnostic score while AMCL pose differed by about 22.5 cm from the reference; its measurement provenance is incomplete. Keep active map identity, TF alignment, covariance, and physical reference accuracy separate from the >=80% ×3 navigation gate. Exact owner-reported 80.9% and 98.3–100% samples have not been recovered.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p7.
- [TROUBLESHOOTING.md](../../../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).
- [localization_guard.py](../../../onboard_ros2_ws/src/lite3_state_estimation/lite3_state_estimation/localization_guard.py).

- Related records: [TEST-20260927-003](../tests/TEST-20260927-003-home-map-localization.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.

## Retrospective session links

[TEST-20261002-029](../tests/TEST-20261002-029-stationary-saved-pose-hypothesis-exhausted-at-55-1-percent.md). These preserve scoped history and
remaining evidence limits; linking them does not constitute a new retest.
