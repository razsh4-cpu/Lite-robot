---
schema: bipolix.engineering_finding/v1
id: FINDING-20260930-001
title: Physical motion has one robot-side authority
date: 2026-09-30
status: CURRENT
categories: ROBOT_CONTROL, SAFETY, XBOX, NOMAD
evidence: docs/architecture/SAFETY_AND_ARBITRATION.md
---

# FINDING-20260930-001 — Single command authority

The command arbiter, `owner.lock`, and observable `COMMAND_SOURCE` distinguish
`NONE`, `LOCAL_XBOX`, `LAPTOP_XBOX`, and `AUTONOMY`. NOMAD operator lease and
Bipolix reservation are higher-level permissions, not replacements for actual
robot-side ownership.

- Evidence: [safety architecture](../../architecture/SAFETY_AND_ARBITRATION.md),
  [ADR-005](../../architecture/decisions/ADR-005-motion-through-existing-safety-path.md),
  and [NOMAD Phase-3C design](../../../../NOMAD/docs/superpowers/specs/2026-10-01-bipolix-phase3c-physical-teleop-design.md).
- Known good: NOMAD physical teleop terminates at the guarded adapter, shared
  `LaptopXboxLease`, protected Joy topic, HIGH-LEVEL, and sole vendor UDP owner.
- DO NOT REPEAT: direct NOMAD→Lite3 UDP, second `/cmd_vel` mux, direct writes to
  ownership files, or overlapping legacy and MQTT Xbox producers.
