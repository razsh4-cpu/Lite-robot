---
schema: bipolix.test_session/v1
id: TEST-20261002-102
title: Historical evidence capture: Earlier D455 RGB/depth and center-depth range checks
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-071
---

# TEST-20261002-102 — Earlier D455 RGB/depth and center-depth range checks

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-071`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PARTIAL` and evidence class `PRIMARY_PDF_HISTORICAL_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Historical PDFs describe RGB/depth/center-depth checks. Exact range ground truth, calibration and raw frames were not retained in this audit. Driver preparation or camera image availability does not validate integrated obstacle perception.

Configuration: ROS2 D455 streams;RViz;exact extrinsic UNKNOWN

## What was executed (historical source scope)

Depth stream and center-depth/range display checks

## Failure, investigation, fix and retest

- Root cause: UNKNOWN
- Fix: On-demand workload policy later
- Retest: Exact depth accuracy/extrinsics unproven
- Currentness: Historical evidence; no current hardware acceptance implied
- Lesson: Earlier hardware use can be recorded while current product perception remains unvalidated

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `PDF A pp2,8`
- `PDF B pp4,9`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
