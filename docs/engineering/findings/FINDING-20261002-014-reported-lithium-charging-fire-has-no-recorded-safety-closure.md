---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-014
title: Reported lithium charging fire has no recorded safety closure
date: 2026-10-02
status: KNOWN_ISSUE
categories: HARDWARE, SAFETY
evidence: /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p10
---

# FINDING-20261002-014 — Reported lithium charging fire has no recorded safety closure

## Finding and applicability

PDF B p10 reports a lithium battery charging fire, firefighter attendance, and rear-shell damage, and says the robot remained operational. Exact date, battery/charger identity, cause, repair, and safety acceptance are UNKNOWN. Continued operation does not prove charging or power-integration safety. Keep this later incident separate from the earlier spark/suspected DC-DC damage.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p10.

- Related records: [TEST-20261002-015](../tests/TEST-20261002-015-battery-connection-spark-and-suspected-dc-dc-damage.md), [TEST-20261002-020](../tests/TEST-20261002-020-lithium-battery-charging-fire-and-reported-shell-damage.md), [FINDING-20261002-010](FINDING-20261002-010-battery-connection-spark-and-suspected-dc-dc-damage-need-separate-closure.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
