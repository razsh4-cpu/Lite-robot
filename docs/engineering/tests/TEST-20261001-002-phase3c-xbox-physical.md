---
schema: bipolix.test_session/v1
id: TEST-20261001-002
title: First bounded NOMAD Phase-3C Xbox forward and stop
date: 2026-10-01
classification: PLANNED
result: PLANNED
actual_behavior: UNKNOWN
categories: XBOX, NOMAD, MQTT, ROBOT_CONTROL, SAFETY
robot_id: robodog_01
git_sha: UNKNOWN
evidence: EVIDENCE MISSING
---

# TEST-20261001-002 — Planned Phase-3C Xbox physical test

## Objective

Validate only: neutral → fresh RB press/hold → minimal forward input → short
bounded movement → RB release → immediate ZERO/STOP.

## Required preconditions

- exactly one intended physical command producer;
- robot connected, fresh, healthy, and separately confirmed `STANDING`;
- valid NOMAD lease and matching Bipolix reservation;
- `LAPTOP_XBOX` through the existing arbiter only;
- new control epoch, neutral observation, fresh RB rising edge, continuous RB;
- existing 0.10 m/s forward cap, freshness/sequence/expiry, 300 ms watchdog;
- verified ZERO on release/timeout/disconnect and operator abort readiness.

Vendor basic-state `98` is valid non-fault telemetry but is not standing proof.
It must not be treated as a fault or silently treated as `STANDING`.

## PASS / FAIL / ABORT

- PASS: short expected forward movement, RB release produces immediate stop,
  ownership cleanup is confirmed, no unexpected direction.
- FAIL: no bounded response or acceptance criteria not met.
- ABORT: continued motion after RB release, wrong direction, stale telemetry,
  authority conflict, unhealthy HIGH-LEVEL, watchdog/zero failure.

Actual behavior, metrics, operator, site, runtime SHA, logs/video, and result
remain `UNKNOWN` / `EVIDENCE MISSING` until the separately approved physical
session occurs. This record does not authorize that session.
