---
schema: bipolix.engineering_finding/v1
id: FINDING-20260928-001
title: Verify active map before interpreting localization confidence
date: 2026-09-28
status: RESOLVED
categories: LOCALIZATION, NAVIGATION, DEPLOYMENT
evidence: docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# FINDING-20260928-001 — Active map identity first

A stable 75–79% scan score was initially interpreted as a localization problem,
but the workflow was using `Home_Map` instead of the newly mapped environment.
Status/preflight now records and displays the active map YAML.

- Evidence: [operations KB](../../operations/ENGINEERING_KNOWLEDGE_BASE.md) and
  [failure record](../../FAILURES_AND_FIXES.md).
- DO NOT REPEAT: tune AMCL, extrinsics, origin, or use a threshold override
  before confirming the selected map is the intended site.
