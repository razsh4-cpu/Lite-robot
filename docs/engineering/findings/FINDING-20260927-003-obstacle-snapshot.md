---
schema: bipolix.engineering_finding/v1
id: FINDING-20260927-003
title: Clearance analysis requires a reconstructable snapshot
date: 2026-09-27
status: RESOLVED
categories: NAVIGATION, SENSORS, SAFETY
evidence: docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# FINDING-20260927-003 — Reconstructable obstacle evidence

An 8 mm clearance claim could not later be reconstructed because scan, both
costmaps, TF, candidate paths, footprint/settings, and limiting pose/cell were
not retained as one bounded session. The obstacle-test snapshot format now
captures those inputs; per-pose limiting-source evidence remains mandatory for
future analysis.

- Evidence: [operations KB](../../operations/ENGINEERING_KNOWLEDGE_BASE.md) and
  [obstacle runbook](../../operations/OBSTACLE_TEST.md).
- DO NOT REPEAT: present a precise clearance as durable evidence without the
  source snapshot needed to reproduce it.

## Retrospective session links

[TEST-20261002-005](../tests/TEST-20261002-005-earlier-chair-planning-safe-refusal.md), [TEST-20261002-018](../tests/TEST-20261002-018-reconstructable-obstacle-snapshot-software-repair.md). These preserve scoped history and
remaining evidence limits; linking them does not constitute a new retest.
