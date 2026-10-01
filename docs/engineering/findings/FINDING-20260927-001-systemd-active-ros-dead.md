---
schema: bipolix.engineering_finding/v1
id: FINDING-20260927-001
title: systemd active is not ROS readiness
date: 2026-09-27
status: RESOLVED
categories: ROS2, LOCALIZATION, DEPLOYMENT, RELIABILITY
evidence: docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# FINDING-20260927-001 — systemd active is not ROS readiness

Processes could remain `active` while DDS participants, topics, lifecycle
states, telemetry, or TF were absent. Deterministic input/lifecycle ordering,
freshness checks, bounded retries, and localization-only recovery replaced
process-state-only readiness.

- Evidence: [engineering knowledge base](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- Known good: network/DDS → HIGH-LEVEL → fresh odom/scan → Map Server active →
  AMCL active → TF → confidence evaluation.
- DO NOT REPEAT: accept `systemctl is-active` as proof that ROS is usable.
- Remaining validation: repeated-boot/long-duration soak is still useful.
