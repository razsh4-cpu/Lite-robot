---
schema: bipolix.test_session/v1
id: TEST-20261002-080
title: Mini-PC read-only deployed-state evidence audit
date: 2026-10-02
classification: LIVE_STATIC_PROVEN
result: PARTIAL
actual_behavior: Read-only state inspected; no robot commands
categories: DEPLOYMENT, EVIDENCE, SAFETY
robot_id: UNKNOWN
git_sha: b4f6a48a56e96c524515d811abc92608ef1e1f3f
evidence: MINIPC_DEPLOYED_STATE_AUDIT.md
---

# TEST-20261002-080 — Mini-PC read-only evidence audit

Objective: distinguish source, historical tests, installed code and current services without modifying the Mini-PC. Reachability checked before SSH. Actual execution: read-only metadata, hashes, allowlisted configuration, service state, bag metadata and CPU flags. Observations, root causes, provenance, known bad approaches, gaps and required future retests are in [audit](../MINIPC_DEPLOYED_STATE_AUDIT.md). Result PARTIAL means bounded evidence access, not partial physical motion. No physical capability was tested. Related findings FINDING-20261002-080 through084. Full raw handoff/runtime text blocked by automatic review; protected broker configuration unreadable.
