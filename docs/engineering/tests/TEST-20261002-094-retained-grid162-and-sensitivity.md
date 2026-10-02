---
schema: bipolix.test_session/v1
id: TEST-20261002-094
title: Historical evidence capture: Retained grid162 and sensitivity
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-042
---

# TEST-20261002-094 — Retained grid162 and sensitivity

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-042`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PASS_LOCAL_MODEL_ONLY` and evidence class `LOCAL_SIMULATION_ARTIFACTS` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Local read-only CSV review verified162 rows,147 declared pass and15 clearance failures. A separate model/campaign from the72/180/79 families; passing flags are offline results only and sensitivity applicability remains model-dependent.

Configuration: PD140/180/220-class highergain simulation; varied friction/timing

## What was executed (historical source scope)

162gridruns and sensitivity family

## Failure, investigation, fix and retest

- Root cause: Declared synthetic thresholds/gains differ from physical limits
- Fix: Later robustbounded campaign
- Retest: Zero robustunload later
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: A local pass is config-bound; never product/hardware capability

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `artifacts/grid_162/results.csv;artifacts/single_leg_sensitivity`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
[Retained CSV review](../evidence/RETAINED_SIMULATION_REVIEW_20261002.json); no simulation rerun or physical experiment.
