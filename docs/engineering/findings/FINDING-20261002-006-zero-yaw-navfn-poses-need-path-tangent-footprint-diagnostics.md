---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-006
title: Zero-yaw NavFn poses need path-tangent footprint diagnostics
date: 2026-10-02
status: RESOLVED
categories: NAVIGATION, SAFETY
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# FINDING-20261002-006 — Zero-yaw NavFn poses need path-tangent footprint diagnostics

## Finding and applicability

The checker treated NavFn yaw=0 as physical orientation on curved paths and falsely evaluated the rectangular footprint. Deriving local path tangent after the start pose repaired the software diagnostic with offline regression. Do not infer that this bug caused the earlier zero-clearance chair refusal without its raw snapshot; the 8 mm claim also remains unauditable.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).

- Related records: [TEST-20261002-012](../tests/TEST-20261002-012-navfn-path-tangent-clearance-correction.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
