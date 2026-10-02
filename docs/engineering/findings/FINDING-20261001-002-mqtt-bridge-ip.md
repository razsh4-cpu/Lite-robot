---
schema: bipolix.engineering_finding/v1
id: FINDING-20261001-002
title: Stale central-broker address stopped live platform status
date: 2026-10-01
status: RESOLVED
categories: MQTT, NETWORKING, NOMAD, DEPLOYMENT
evidence: NOMAD Phase-3B plan bridge update 192.168.2.142 to 192.168.2.177
---

# FINDING-20261001-002 — MQTT bridge destination

The Mini-PC/edge path was running, but the bridge targeted the former laptop
address `192.168.2.142` instead of the active C&C address `192.168.2.177`.
Updating the bridge destination restored topic arrival/FleetRegistry visibility.

- Evidence: [Phase-3B plan](../../../../NOMAD/docs/superpowers/plans/2026-09-30-bipolix-phase3b-live-motion-blocked.md)
  records the `.177` update; the exact incident log is `EVIDENCE MISSING`.
- DO NOT REPEAT: diagnose `never_seen` as robot readiness before tracing edge
  publish → bridge destination → central broker → registry ingestion.
- Deployment lesson: broker host is configuration, never a stale copied
  development-host constant.

## Retrospective session links

[TEST-20261002-032](../tests/TEST-20261002-032-stale-central-mqtt-bridge-destination-incident.md). These preserve scoped history and
remaining evidence limits; linking them does not constitute a new retest.
