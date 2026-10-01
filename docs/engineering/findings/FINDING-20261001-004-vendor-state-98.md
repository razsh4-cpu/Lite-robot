---
schema: bipolix.engineering_finding/v1
id: FINDING-20261001-004
title: Vendor basic-state 98 is valid non-fault telemetry
date: 2026-10-01
status: CURRENT
categories: ROBOT_CONTROL, SAFETY, NOMAD
evidence: Lite-robot Phase-3C exporter/watchdog mapping and NOMAD Phase-3C design
---

# FINDING-20261001-004 — Vendor basic-state 98

Vendor basic-state value `98` is a valid, non-fault state and must not make
platform telemetry unhealthy. It is also not, by itself, authoritative proof
that the robot is `STANDING`; drive remains blocked until the separate fresh
posture/readiness mechanism confirms standing.

- Evidence: [NOMAD Phase-3C design](../../../../NOMAD/docs/superpowers/specs/2026-10-01-bipolix-phase3c-physical-teleop-design.md)
  and current Lite-robot exporter/watchdog source. The associated Lite changes
  are present in the current working tree and are not yet claimed as committed
  deployment evidence.
- Known good: report 98 as valid telemetry, preserve posture as unknown/not
  standing until independently confirmed.
- DO NOT REPEAT: label 98 a fault, change its vendor mapping, or silently map it
  to `STANDING` merely to enable drive.
