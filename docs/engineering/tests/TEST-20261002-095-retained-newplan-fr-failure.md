---
schema: bipolix.test_session/v1
id: TEST-20261002-095
title: Historical evidence capture: Retained newplan FR failure
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: FAIL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-043
---

# TEST-20261002-095 — Retained newplan FR failure

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-043`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL` and evidence class `LOCAL_SIMULATION_ARTIFACTS` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Retained newplan summary completed=false: FR clearance0.0004387758402m versus5mm acceptance, unload fraction0. Nominal and CLI-like fields coexist in summary; exact effective configuration cannot be assumed without run manifest. No rerun or physical command.

Configuration: MuJoCo2.3.7;metadata mixed PD180/3.5 and newplan60/.7

## What was executed (historical source scope)

Newplan simulation retainedsummary/trace

## Failure, investigation, fix and retest

- Root cause: Model/config boundary and inadequate clearance
- Fix: No proven fix
- Retest: Robust campaign later
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Preserve parameter metadata inconsistency rather than flattening

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `artifacts/one_leg_lift_newplan/summary.json`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
[Retained CSV review](../evidence/RETAINED_SIMULATION_REVIEW_20261002.json); no simulation rerun or physical experiment.
