---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-084
title: Retained bags and clock metadata impose evidence limits
date: 2026-10-02
status: CURRENT
categories: DEPLOYMENT, SAFETY, EVIDENCE
evidence: MINIPC_DEPLOYED_STATE_AUDIT.md and allowlisted snapshot
---

# FINDING-20261002-084 — Retained bags and clock metadata impose evidence limits

## Finding

Two September24 MCAP payloads remain, while September15 references lack payloads; zero-message smoke records are not PASS. Bag aggregate odom rates~200Hz differ from September27~154Hz capture. Service timestamps conflict with uptime/current date; clock cause UNKNOWN. Preserve source-specific chronology and absent payloads; never invent retest or calibration.

## Evidence and relationships

Read-only capture2026-10-02; no physical commands or retests. Primary sources and exact affected SHAs/paths in [deployed-state audit](../MINIPC_DEPLOYED_STATE_AUDIT.md) and [snapshot](../evidence/MINIPC_READ_ONLY_20261002.json). Historical experiment dates are only those explicitly supported by the cited Git/bag records; capture date is not experiment date. Source baseline and deployment must remain separate.
