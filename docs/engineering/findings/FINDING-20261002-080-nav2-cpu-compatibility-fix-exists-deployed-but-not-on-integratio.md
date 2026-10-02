---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-080
title: Nav2 CPU compatibility fix exists deployed but not on integration branch
date: 2026-10-02
status: KNOWN_ISSUE
categories: DEPLOYMENT, SAFETY, EVIDENCE
evidence: MINIPC_DEPLOYED_STATE_AUDIT.md and allowlisted snapshot
---

# FINDING-20261002-080 — Nav2 CPU compatibility fix exists deployed but not on integration branch

## Finding

Git141b497 reports MPPI SIGILL on J6413; inspected CPU has no AVX/AVX2. Deployed installed navigation source matches b4f6a48 and contains CPU-based RPP selection. Current bipolix_robot lacks it. Root cause is source-backed binary instruction mismatch; new physical/runtime retest UNKNOWN. Do not deploy integration wholesale and restore the known failing MPPI default.

## Evidence and relationships

Read-only capture2026-10-02; no physical commands or retests. Primary sources and exact affected SHAs/paths in [deployed-state audit](../MINIPC_DEPLOYED_STATE_AUDIT.md) and [snapshot](../evidence/MINIPC_READ_ONLY_20261002.json). Historical experiment dates are only those explicitly supported by the cited Git/bag records; capture date is not experiment date. Source baseline and deployment must remain separate.

## Subsequent source reconciliation

The initial read-only snapshot remains unchanged. The offline continuation now reimplements this concept in the integration branch; see [FINDING-20261002-095](FINDING-20261002-095-field-fix-concepts-reconciled-through-product-owners.md). This addresses source divergence only; no deployment or new physical acceptance occurred.
