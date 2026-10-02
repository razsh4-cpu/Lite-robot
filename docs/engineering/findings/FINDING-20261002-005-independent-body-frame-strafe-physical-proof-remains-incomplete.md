---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-005
title: Independent body-frame strafe physical proof remains incomplete
date: 2026-10-02
status: KNOWN_ISSUE
categories: ROBOT_CONTROL, NAVIGATION, NOMAD
evidence: /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf p7/p10/p12
---

# FINDING-20261002-005 — Independent body-frame strafe physical proof remains incomplete

## Finding and applicability

Historical PDF A deliberately disables lateral and forces linear.y=0 for its recorded adapter. Static vendor lateral syntax does not prove physical acceptance. The owner-reported direct NOMAD strafe attempt failed with UNKNOWN cause. A world-frame Nav2 detour can result from turn plus forward travel; without time-aligned body command/yaw/displacement evidence it cannot establish independent body-frame strafe. Retain the autonomous goal PASS while qualifying the separate axis proof.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf](../../../../../Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf) p7/p10/p12.
- [LITE3_HISTORY_AUDIT.md](../../../../../Documents/NOMAD/docs/LITE3_HISTORY_AUDIT.md).

- Related records: [TEST-20260927-001](../tests/TEST-20260927-001-chair-avoidance-interrupted.md), [TEST-20260927-002](../tests/TEST-20260927-002-chair-avoidance-pass.md), [TEST-20261002-013](../tests/TEST-20261002-013-owner-reported-direct-nomad-strafe-failure.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
