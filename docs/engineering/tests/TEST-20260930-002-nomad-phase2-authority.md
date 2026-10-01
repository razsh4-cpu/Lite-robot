---
schema: bipolix.test_session/v1
id: TEST-20260930-002
title: NOMAD Phase-2 remote-authority reservation
date: 2026-09-30
classification: OFFLINE_PROVEN
result: PASS
categories: NOMAD, MQTT, SAFETY, XBOX
robot_id: robodog_01
git_sha: fa6810e
evidence: NOMAD docs/integrations/BIPOLIX_REMOTE_AUTHORITY.md
---

# TEST-20260930-002 — NOMAD Phase-2 authority reservation

Offline tests covered ACQUIRE/RENEW/RELEASE, TTL, generation/session identity,
replay/idempotency, conflicts, disconnect cleanup, safe robot switching, and
multi-robot isolation. NOMAD operator lease, remote reservation, and actual
`COMMAND_SOURCE` remained separate; reservation did not acquire robot motion.

- Evidence: [NOMAD authority record](../../../../NOMAD/docs/integrations/BIPOLIX_REMOTE_AUTHORITY.md).
- Relevant commits: `4da8ae2` through `fa6810e` in NOMAD.
- `COMMAND_SOURCE` activation / `owner.lock` acquisition / motion: none.
