---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-093
title: Historical evidence capture: Distro paho compatibility defect→shim
date: 2026-10-02
status: HISTORICAL
categories: HISTORY, EVIDENCE
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-084
---

# FINDING-20261002-093 — Distro paho compatibility defect→shim

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-084`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `UNKNOWN → PASS → PASS` and evidence class `HISTORICAL_CLAIM / OFFLINE_PROVEN / LIVE_STATIC_PROVEN` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Distro paho compatibility shim repaired gateway software API differences in historical source. Do not promote import compatibility to broker connectivity or physical readiness. Existing Phase3B negative-path evidence remains separate.

Configuration: See listed primary sources; exact deployed run configuration UNKNOWN

## What was executed (historical source scope)

[
  {
    "stage": "problem",
    "result": "UNKNOWN",
    "classification": "HISTORICAL_CLAIM",
    "observation": "GatewayclientAPIneeded distrocompatibility; precise liveexception notretained."
  },
  {
    "stage": "fix/retest",
    "result": "PASS",
    "classification": "OFFLINE_PROVEN",
    "observation": "NestedNOMADcommit e1990e1 mqtt_compat and tests."
  },
  {
    "stage": "integration",
    "result": "PASS",
    "classification": "LIVE_STATIC_PROVEN",
    "observation": "Latera0cda36aggregategatewayvalidation."
  }
]

## Failure, investigation, fix and retest

- Root cause: Only the explicitly reported mechanism in the stages is supported; exact per-run cause UNKNOWN when not captured
- Fix: NestedNOMADcommit e1990e1 mqtt_compat and tests.
- Retest: NestedNOMADcommit e1990e1 mqtt_compat and tests.; Latera0cda36aggregategatewayvalidation.
- Currentness: Evidence-bounded historical scope; exact physical acceptance only when explicitly recorded
- Lesson: Findingwithcommitevidence; associateaggregateintegrationtestwithoutclaimingisolatedliveretest.

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `/home/raz/ros-robot-cc/NOMAD/ros2_ws/src/nomad_bipolix_gateway/nomad_bipolix_gateway/mqtt_compat.py`
- `/home/raz/ros-robot-cc/NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
