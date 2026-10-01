---
schema: bipolix.test_session/v1
id: TEST-20261001-001
title: NOMAD Phase-3B real Mini-PC non-motion integration
date: 2026-10-01
classification: LIVE_STATIC_PROVEN
result: PASS
categories: NOMAD, MQTT, MINI_PC, SAFETY
robot_id: robodog_01
git_sha: a0cda36
evidence: NOMAD docs/integrations/BIPOLIX_NON_MOTION_MVP.md
---

# TEST-20261001-001 — NOMAD Phase-3B live non-motion integration

The real Mini-PC exporter/gateway-only profile and edge broker were observed
through the real MQTT path. With robot telemetry unavailable, authority,
drive-shaped intent, Mission, and Patrol correctly failed closed; velocity
remained zero, physical output false, `COMMAND_SOURCE=NONE`, and owner lock
absent.

- Evidence: [NOMAD non-motion MVP](../../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).
- Relevant NOMAD validation commit: `a0cda36`.
- Physical robot readiness and motion were intentionally not acceptance
  criteria and are not claimed.
