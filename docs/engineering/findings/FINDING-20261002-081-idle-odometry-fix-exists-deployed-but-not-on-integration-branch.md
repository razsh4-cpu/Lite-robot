---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-081
title: Idle odometry fix exists deployed but not on integration branch
date: 2026-10-02
status: KNOWN_ISSUE
categories: DEPLOYMENT, SAFETY, EVIDENCE
evidence: MINIPC_DEPLOYED_STATE_AUDIT.md and allowlisted snapshot
---

# FINDING-20261002-081 — Idle odometry fix exists deployed but not on integration branch

## Finding

Gitb4f6a48 reports stationary Auto gait telemetry integrated into drift/map smear. Deployed driver includes odom_still_after_sec0.5, absent from current integration. Fix is command-intent-based hold, not measured independent odometry; handheld bypass is a limitation. No physical retest performed. Preserve as distinct from odom flooding and ICP.

## Evidence and relationships

Read-only capture2026-10-02; no physical commands or retests. Primary sources and exact affected SHAs/paths in [deployed-state audit](../MINIPC_DEPLOYED_STATE_AUDIT.md) and [snapshot](../evidence/MINIPC_READ_ONLY_20261002.json). Historical experiment dates are only those explicitly supported by the cited Git/bag records; capture date is not experiment date. Source baseline and deployment must remain separate.

## Subsequent source reconciliation

The initial read-only snapshot remains unchanged. The offline continuation now reimplements this concept in the integration branch; see [FINDING-20261002-095](FINDING-20261002-095-field-fix-concepts-reconciled-through-product-owners.md). This addresses source divergence only; no deployment or new physical acceptance occurred.
