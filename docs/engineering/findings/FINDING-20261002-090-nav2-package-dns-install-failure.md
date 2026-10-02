---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-090
title: Historical evidence capture: Nav2 package DNS install failure
date: 2026-10-02
status: HISTORICAL
categories: HISTORY, EVIDENCE
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-048
---

# FINDING-20261002-090 — Nav2 package DNS install failure

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-048`; source date/period `2026-09-26` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL` and evidence class `HISTORICAL_DEPLOYMENT_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

APT could not resolve packages.ros.org. This was DNS/route readiness failure, not proof of invalid Nav2 package/distribution. Do not change package names to hide network failure. Recovery commands in source are historical procedure, not executed by this audit.

Configuration: ROSJazzy;packages.ros.org

## What was executed (historical source scope)

HistoricalAPTattempt

## Failure, investigation, fix and retest

- Root cause: DNS/default-route failure
- Fix: RestoreDNS beforeAPT
- Retest: UNKNOWN
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Do not change package/distribution to mask DNS

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
