---
schema: bipolix.test_session/v1
id: TEST-20261002-101
title: Historical evidence capture: Earlier LiDAR orientation, clustering and mapping work
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-070
---

# TEST-20261002-101 — Earlier LiDAR orientation, clustering and mapping work

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-070`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PARTIAL` and evidence class `PRIMARY_PDF_HISTORICAL_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Earlier LiDAR orientation/clustering/mapping claims remain distinct from later AMCL/TF service fixes. Extrinsic metrology and exact calibration run data remain incomplete; later successful localization is not proof of every earlier sensor experiment.

Configuration: RPLIDAR S2/sllidar_ros2;~10Hz;lidar z≈.08m yawπ

## What was executed (historical source scope)

RViz scan; orientation correction; DBSCAN/clustering; mapping/map save and AMCL/Nav2 preview

## Failure, investigation, fix and retest

- Root cause: Orientation confusion; exact metrology unknown
- Fix: Historical yawπ frame correction
- Retest: Later LiDAR product path independently reported
- Currentness: Historical evidence; no current hardware acceptance implied
- Lesson: Do not transplant frame transform into floor-projected NOMAD base without measurement

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `PDF A pp2,8–9`
- `PDF B pp4,6–7`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
