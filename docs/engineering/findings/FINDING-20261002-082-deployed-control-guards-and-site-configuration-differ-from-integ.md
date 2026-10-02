---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-082
title: Deployed control guards and site configuration differ from integration
date: 2026-10-02
status: KNOWN_ISSUE
categories: DEPLOYMENT, SAFETY, EVIDENCE
evidence: MINIPC_DEPLOYED_STATE_AUDIT.md and allowlisted snapshot
---

# FINDING-20261002-082 — Deployed control guards and site configuration differ from integration

## Finding

Deployed mainb4f6a48 lacks new ControlAuthority/manual lock and driver battery guard. Site teleop/driver limits2/1.5/2 exceed repo defaults.5/.3/.6; odom sign[1,1,1] differs from[-1,1,1]. Intent and calibration UNKNOWN. Installed module hashes establish source resolution, not physical acceptance. Target laptop Xbox path not yet deployed; Mini-PC-local Xbox not required.

## Evidence and relationships

Read-only capture2026-10-02; no physical commands or retests. Primary sources and exact affected SHAs/paths in [deployed-state audit](../MINIPC_DEPLOYED_STATE_AUDIT.md) and [snapshot](../evidence/MINIPC_READ_ONLY_20261002.json). Historical experiment dates are only those explicitly supported by the cited Git/bag records; capture date is not experiment date. Source baseline and deployment must remain separate.
