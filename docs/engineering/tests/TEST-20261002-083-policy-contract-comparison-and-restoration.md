---
schema: bipolix.test_session/v1
id: TEST-20261002-083
title: Historical evidence capture: Policy contract comparison and restoration
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-029
---

# TEST-20261002-083 — Policy contract comparison and restoration

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-029`; source date/period `2026-09-14` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PASS_OFFLINE_ONLY` and evidence class `OFFLINE_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

January/April model comparison restored a coherent ONNX/nominal-pose/timing contract after offline plant-authority investigation. The upstream report of lateral on another robot is not Raz-path direct strafe evidence. Restoration was not a physically accepted walking fix.

Configuration: January12ms paired-.80/1.60 versus April20ms paired-.65/1.30; Kp30/Kd1

## What was executed (historical source scope)

MuJoCo +.25 reference5s and weaker-actuator comparisons

## Failure, investigation, fix and retest

- Root cause: Plant response insufficient in modeled weak-actuator family
- Fix: Restore coherent January contract
- Retest: Hardware still failed useful locomotion
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Never mix policy pose timing/action history contracts

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `docs/POLICY_GAIT_ROOT_CAUSE_2026-09-14.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
