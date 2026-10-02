---
schema: bipolix.test_session/v1
id: TEST-20261002-092
title: Historical evidence capture: Retained 180 thigh-knee angle sweep
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: FAIL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-040
---

# TEST-20261002-092 — Retained 180 thigh-knee angle sweep

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-040`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL` and evidence class `LOCAL_SIMULATION_ARTIFACTS` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Local read-only CSV review verified180 rows:162 unload failures and18 roll/pitch failures. These are retained model outputs, not physical attempts or a new simulation run.

Configuration: artifacts/joint_angle_sweep; date UNKNOWN

## What was executed (historical source scope)

180jointangle/curl trials

## Failure, investigation, fix and retest

- Root cause: Model family limitation; physical cause UNKNOWN
- Fix: Robust force/contactaudit later
- Retest: No hardware inference
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Joint scaling is not Cartesian scaling

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `artifacts/joint_angle_sweep/results.csv`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
[Retained CSV review](../evidence/RETAINED_SIMULATION_REVIEW_20261002.json); no simulation rerun or physical experiment.
