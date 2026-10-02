---
schema: bipolix.test_session/v1
id: TEST-20261002-096
title: Historical evidence capture: Battery exhausted shutdown
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-047
---

# TEST-20261002-096 — Battery exhausted shutdown

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-047`; source date/period `2026-09-26` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL_OPERATIONAL` and evidence class `HISTORICAL_PHYSICAL_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Troubleshooting reports loss of Mini-PC response and robot battery ending with lying posture. Power loss invalidates old localization/ownership readiness. Not an instruction to deliberately drain a battery; electrical failure cause/recovery acceptance remains bounded.

Configuration: HistoricalDay1/Day2

## What was executed (historical source scope)

Observed targetdisappearance and physicalsafe lying

## Failure, investigation, fix and retest

- Root cause: Power/battery exhaustion
- Fix: Recharge/power restore first
- Retest: Separate newboot preflight
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Poweroffline is not C2/DDSsoftware regression

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
