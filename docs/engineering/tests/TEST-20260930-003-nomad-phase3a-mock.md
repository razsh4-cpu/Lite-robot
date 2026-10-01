---
schema: bipolix.test_session/v1
id: TEST-20260930-003
title: NOMAD Phase-3A mock TeleopIntent pipeline
date: 2026-09-30
classification: OFFLINE_PROVEN
result: PASS
categories: NOMAD, MQTT, XBOX, SAFETY
robot_id: robodog_01
git_sha: 4561e74
evidence: NOMAD docs/integrations/BIPOLIX_MOCK_TELEOP.md
---

# TEST-20260930-003 — NOMAD Phase-3A mock teleop

The production-shaped MQTT contract was validated against a deterministic mock
receiver for authority, epoch, sequence, freshness, deadman, neutral gate,
watchdog, malformed values, reconnect/switch cleanup, and multi-robot
isolation. It recorded intent only.

- Evidence: [NOMAD Phase-3A record](../../../../NOMAD/docs/integrations/BIPOLIX_MOCK_TELEOP.md).
- Relevant commits: `dcbb2e1` through `4561e74` in NOMAD.
- Explicit boundary: no Joy to robot stack, `/cmd_vel`, ROS motion publisher,
  owner lock, command-source write, or Lite3 UDP.
