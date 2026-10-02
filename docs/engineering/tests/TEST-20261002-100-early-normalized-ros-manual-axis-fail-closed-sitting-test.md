---
schema: bipolix.test_session/v1
id: TEST-20261002-100
title: Historical evidence capture: Early normalized ROS manual-axis fail-closed sitting test
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-067
---

# TEST-20261002-100 — Early normalized ROS manual-axis fail-closed sitting test

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-067`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PASS_NEGATIVE_PATH` and evidence class `PRIMARY_PDF_HISTORICAL_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Historical ROS normalized axis gate while sitting refused physical transmit/motion. Negative-path proof does not establish stand confirmation or new product network acceptance. PDF is retrospective source, not new raw log.

Configuration: sensor_visualization/lite3_manual_axis_control; forward±.10;300ms;state6;battery25%;transmitfalse default

## What was executed (historical source scope)

Dry-run strace then separately enabled live path while sitting

## Failure, investigation, fix and retest

- Root cause: Standing/deadman readiness absent
- Fix: Fail-closed neutral behavior
- Retest: Later separately reported direction tests
- Currentness: Historical evidence; no current hardware acceptance implied
- Lesson: A negative-path live pass does not prove locomotion

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `PDF A pp5–6`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
