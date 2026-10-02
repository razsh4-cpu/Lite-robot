---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-083
title: Legacy status domain and advertised capabilities are not product readiness
date: 2026-10-02
status: KNOWN_ISSUE
categories: DEPLOYMENT, SAFETY, EVIDENCE
evidence: MINIPC_DEPLOYED_STATE_AUDIT.md and allowlisted snapshot
---

# FINDING-20261002-083 — Legacy status domain and advertised capabilities are not product readiness

## Finding

Legacy exporter runs domain0 while SABLE launch uses23. It reports OFFLINE and unavailable localization, but advertises lateral capability. Domain mismatch may explain blindness; sole cause UNKNOWN. Do not infer robot disconnection or physically validated strafe from exporter constants. Use fresh authoritative state6; state98 remains non-standing.

## Evidence and relationships

Read-only capture2026-10-02; no physical commands or retests. Primary sources and exact affected SHAs/paths in [deployed-state audit](../MINIPC_DEPLOYED_STATE_AUDIT.md) and [snapshot](../evidence/MINIPC_READ_ONLY_20261002.json). Historical experiment dates are only those explicitly supported by the cited Git/bag records; capture date is not experiment date. Source baseline and deployment must remain separate.
