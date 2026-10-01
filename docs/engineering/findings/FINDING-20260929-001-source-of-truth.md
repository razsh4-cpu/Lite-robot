---
schema: bipolix.engineering_finding/v1
id: FINDING-20260929-001
title: Deployed source was hybrid, not one authoritative copied tree
date: 2026-09-29
status: RESOLVED
categories: DEPLOYMENT, MINI_PC, SAFETY
evidence: docs/architecture/SOURCE_OF_TRUTH_RECONCILIATION_2026-09-29.md
---

# FINDING-20260929-001 — Source-of-truth reconciliation

Laptop development, Mini-PC source copies, installed units, and Git differed.
Content hashes and actual consumers showed that neither an entire deployed tree
nor old Git could be preferred wholesale. Safety decisions were reconciled
file-by-file; build/install/log/cache/runtime state was excluded.

- Evidence: [reconciliation record](../../architecture/SOURCE_OF_TRUTH_RECONCILIATION_2026-09-29.md).
- Known good: Git is the source destination; deployment artifacts derive from
  reviewed source/config and carry an explicit manifest where possible.
- DO NOT REPEAT: use timestamps or deployment location alone to declare
  authority, or import generated ROS artifacts into Git.
