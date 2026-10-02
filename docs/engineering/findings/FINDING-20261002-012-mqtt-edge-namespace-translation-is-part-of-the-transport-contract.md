---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-012
title: MQTT edge namespace translation is part of the transport contract
date: 2026-10-02
status: RESOLVED
categories: MQTT, NOMAD
evidence: /home/raz/ros-robot-cc/NOMAD/docs/integrations/BIPOLIX_PHASE3B_LIVE_BLOCKED.md
---

# FINDING-20261002-012 — MQTT edge namespace translation is part of the transport contract

## Finding and applicability

Nested NOMAD commit 9739f4c aligns local edge control/platform_* topics with namespaced C&C topics, retaining payload robot_id checks. The later Phase-3B live non-motion record validates aggregate transport. Trace exporter, edge broker, bridge namespace/destination, central broker, and registry separately; online gateway presence does not imply robot readiness.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [BIPOLIX_PHASE3B_LIVE_BLOCKED.md](../../../../NOMAD/docs/integrations/BIPOLIX_PHASE3B_LIVE_BLOCKED.md).
- [BIPOLIX_NON_MOTION_MVP.md](../../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).

- Related records: [TEST-20261001-001](../tests/TEST-20261001-001-nomad-phase3b-live-static.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
