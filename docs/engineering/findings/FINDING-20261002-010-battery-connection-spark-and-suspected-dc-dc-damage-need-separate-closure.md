---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-010
title: Battery connection spark and suspected DC-DC damage need separate closure
date: 2026-10-02
status: KNOWN_ISSUE
categories: HARDWARE, SAFETY
evidence: /home/raz/Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf p10
---

# FINDING-20261002-010 — Battery connection spark and suspected DC-DC damage need separate closure

## Finding and applicability

PDF B p10 reports a spark during battery connection while charging and suspected Mini-PC DC-DC damage. Cause, measured damage, component identity, repair, and retest remain UNKNOWN. Preserve suspected versus confirmed damage and do not merge this event with the later fire, Wi-Fi fault, exporter starvation, or chair cable interruption.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p10.

- Related records: [TEST-20261002-015](../tests/TEST-20261002-015-battery-connection-spark-and-suspected-dc-dc-damage.md), [TEST-20261002-020](../tests/TEST-20261002-020-lithium-battery-charging-fire-and-reported-shell-damage.md), [FINDING-20261002-014](FINDING-20261002-014-reported-lithium-charging-fire-has-no-recorded-safety-closure.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
