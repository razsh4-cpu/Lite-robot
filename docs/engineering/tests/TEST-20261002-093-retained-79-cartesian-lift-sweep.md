---
schema: bipolix.test_session/v1
id: TEST-20261002-093
title: Historical evidence capture: Retained 79 Cartesian lift sweep
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: FAIL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-041
---

# TEST-20261002-093 — Retained 79 Cartesian lift sweep

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-041`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL` and evidence class `LOCAL_SIMULATION_ARTIFACTS` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Local read-only CSV review verified79 rows:74 clearance failures,1 contact restoration failure and4 roll/pitch failures. Preserve all failure types; do not call the sweep accepted.

Configuration: artifacts/leg_lift_sweep;dateUNKNOWN

## What was executed (historical source scope)

79shift/lift parameter trials

## Failure, investigation, fix and retest

- Root cause: Threshold failure in modeled family
- Fix: Subsequent grid/robust work
- Retest: Different gains/families not comparable
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: No successful physical clearance follows from simulation

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `artifacts/leg_lift_sweep/results.csv`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
[Retained CSV review](../evidence/RETAINED_SIMULATION_REVIEW_20261002.json); no simulation rerun or physical experiment.
