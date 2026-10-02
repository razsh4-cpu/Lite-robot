---
schema: bipolix.test_session/v1
id: TEST-20261002-082
title: Historical evidence capture: Convergence and supported stand entry
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PASS
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-028
---

# TEST-20261002-082 — Convergence and supported stand entry

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-028`; source date/period `2026-09-13` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PASS` and evidence class `HISTORICAL_OPERATOR_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

The retained stand-convergence report preserves operator-observed standing/fall, six-second monitor deadline and velocity spikes preventing0.5s dwell. Changed50ms RMS+position-range criterion passed inert counterfactual replay; physical retest does not follow from replay. Subsequent indefinite hold was superseded by absolute hold deadline. Do not erase either failed stand or later hold-policy change.

Configuration: RMS50ms and positionrange

## What was executed (historical source scope)

E6 stand_once supported

## Failure, investigation, fix and retest

- Root cause: Convergence too sensitive to isolated speeds; authorization timing
- Fix: Atomic entry and RMS/position convergence
- Retest: E7 release; E8 long hold
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Hold policy changed later; preserve original build evidence

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `docs/EXPERIMENTS.md E6-E8; docs/STAND_CONVERGENCE_REVIEW_2026-09-13.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
