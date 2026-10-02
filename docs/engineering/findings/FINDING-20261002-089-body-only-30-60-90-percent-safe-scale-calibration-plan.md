---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-089
title: Historical evidence capture: Body-only 30/60/90 percent safe-scale calibration plan
date: 2026-10-02
status: HISTORICAL
categories: HISTORY, EVIDENCE
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-044
---

# FINDING-20261002-089 — Body-only 30/60/90 percent safe-scale calibration plan

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-044`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `IMPLEMENTED; PHYSICAL RESULT UNKNOWN` and evidence class `COMMITTED_SOURCE` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Committed body-only planner and tests support30/60/90% fractions/reference shift(-0.029043,+0.026558)m and computed safe scaling. Per-level physical traces remain incomplete. Keep later25/50/75 proposals distinct; source support is not progression acceptance.

Configuration: Cartesian body reference (-0.029043,+0.026558,0)m; 0.30/0.60/0.90 fractions of computed joint-limit safe scale; keep all nominal foot heights

## What was executed (historical source scope)

Committed source implements Cartesian IK per sample, independent one-use levels and guarded full sequence; exact historical physical execution UNKNOWN

## Failure, investigation, fix and retest

- Root cause: UNKNOWN
- Fix: NONE
- Retest: UNKNOWN
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: 30/60/90 safe fractions are different from the later proposed 25/50/75 model-validation plan; source names do not prove a run

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `L/state_machine/supported_body_shift_plan.hpp:14`
- `L/tests/supported_body_shift_plan_test.cpp`
- `L/tests/supported_body_shift_once_test.cpp`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
