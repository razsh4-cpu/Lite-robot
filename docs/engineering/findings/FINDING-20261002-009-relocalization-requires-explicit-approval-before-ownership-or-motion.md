---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-009
title: Relocalization requires explicit approval before ownership or motion
date: 2026-10-02
status: RESOLVED
categories: SAFETY, LOCALIZATION
evidence: /home/raz/Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf p2
---

# FINDING-20261002-009 — Relocalization requires explicit approval before ownership or motion

## Finding and applicability

PDF D p2 reports that relocalize began without approval; exact ownership or physical movement consequences are UNKNOWN. The existing offline acceptance verifies literal approval, default-no behavior, cancellation, zero/release, and the normal confidence gate. Resolution concerns software permission gating. Dedicated end-to-end physical CLI acceptance remains open.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [test_lite3_relocalize_cli.py](../../../tests/operator/test_lite3_relocalize_cli.py).

- Related records: [TEST-20260929-001](../tests/TEST-20260929-001-relocalize-approval.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
