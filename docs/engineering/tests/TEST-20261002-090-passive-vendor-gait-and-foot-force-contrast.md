---
schema: bipolix.test_session/v1
id: TEST-20261002-090
title: Historical evidence capture: Passive vendor gait and foot-force contrast
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-038
---

# TEST-20261002-090 — Passive vendor gait and foot-force contrast

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-038`; source date/period `2026-09-18` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PARTIAL` and evidence class `HISTORICAL_PASSIVE_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Passive vendor recording reported useful contact force and coordinated gait; low-level custom path reported zero contact channels. Vendor swing cannot be copied into a static three-leg primitive, and unavailable force cannot prove unloading.

Configuration: Receiver-only original remote ownership;~1000Hz

## What was executed (historical source scope)

Recorded q,dq,torque,attitude,forces during vendor gait

## Failure, investigation, fix and retest

- Root cause: Zero low-level force reason UNKNOWN
- Fix: Require calibrated independent loads
- Retest: No calibrated hardware unload proof
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Do not copy isolated threeleg FR from trot

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `docs/handoff/HANDOFF_2026-09-18_LEG_LIFT.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
