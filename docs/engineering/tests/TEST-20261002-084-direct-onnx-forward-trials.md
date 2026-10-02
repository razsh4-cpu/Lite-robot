---
schema: bipolix.test_session/v1
id: TEST-20261002-084
title: Historical evidence capture: Direct ONNX forward trials
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: FAIL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-030
---

# TEST-20261002-084 — Direct ONNX forward trials

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-030`; source date/period `2026-09-14` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL` and evidence class `HISTORICAL_PHYSICAL_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Direct joint-policy trials produced lean/stepping/falls without useful safe translation. Correct contract and offline simulation improvements did not close sim-to-real tracking. Product pilot selected existing vendor gait instead.

Configuration: Coherent policy/pose/timing; bounded joint-level path

## What was executed (historical source scope)

Supervised forward attempts

## Failure, investigation, fix and retest

- Root cause: Unresolved sim-to-real dynamics/tracking; precise physical cause UNKNOWN
- Fix: Paused product ONNX; vendor gait selected
- Retest: Vendor forward pulse physically reported separately
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Kinematic/software agreement cannot prove plant authority

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `docs/HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md; docs/POLICY_GAIT_ROOT_CAUSE_2026-09-14.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
