---
schema: bipolix.test_session/v1
id: TEST-20261002-091
title: Historical evidence capture: Retained 72 jointscale sweep
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: FAIL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-039
---

# TEST-20261002-091 — Retained 72 jointscale sweep

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-039`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL` and evidence class `LOCAL_SIMULATION_ARTIFACTS` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Local read-only CSV review on2026-10-02 verified72 retained rows, all with abort reason FR did not remain unloaded during hold. The simulation was not rerun; run date/model manifest remain incomplete.

Configuration: artifacts/joint_leg_lift_sweep; date UNKNOWN

## What was executed (historical source scope)

72syntheticshift/liftscale trials

## Failure, investigation, fix and retest

- Root cause: Contact/gain/control family limitations; hardware cause UNKNOWN
- Fix: Later calibrated robust campaign
- Retest: Robust campaign also no unload
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Preserve failed local artifacts; dates cannot derive from mtime

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `artifacts/joint_leg_lift_sweep/results.csv`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
[Retained CSV review](../evidence/RETAINED_SIMULATION_REVIEW_20261002.json); no simulation rerun or physical experiment.
