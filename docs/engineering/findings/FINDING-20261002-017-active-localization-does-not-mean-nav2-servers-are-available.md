---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-017
title: Active localization does not mean Nav2 servers are available
date: 2026-10-02
status: RESOLVED
categories: NAVIGATION, DEPLOYMENT, SAFETY
evidence: docs/FAILURES_AND_FIXES.md
---

# FINDING-20261002-017 — Active localization does not mean Nav2 servers are available

Map Server/AMCL active and Nav2 planner unavailable can be a deliberate inactive navigation service, not a localization failure. The read-only obstacle status never starts Nav2. Only the motion workflow may start the existing service after every other precondition passes, then verify all required servers and costmaps. The documented software fix still requires distinct installed live acceptance; it neither acquires AUTONOMY nor authorizes movement by itself.

This is retrospective capture; exact run SHA, timestamps, and missing retest
measurements remain `UNKNOWN`. Resolution labels software behavior only where
reported, not current physical safety or sustained reliability.

- [Primary report](../../FAILURES_AND_FIXES.md).
- Related sessions: [TEST-20261002-030](../tests/TEST-20261002-030-obstacle-preflight-separated-localization-from-inactive-nav2.md).
- DO NOT REPEAT: infer lifecycle readiness from process state or one fresh
  sensor stream; erase pending installed acceptance after software repair.
