---
schema: bipolix.test_session/v1
id: TEST-20261002-087
title: Historical evidence capture: One-leg kinematics and deterministic simulation
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PASS
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-035
---

# TEST-20261002-087 — One-leg kinematics and deterministic simulation

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-035`; source date/period `2026-09-17` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `PASS` and evidence class `OFFLINE_SIMULATION_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Two deterministic MuJoCo report runs passed with simulation-only contact normalization. FK agreement1.01e-16m and clearance6.4315mm are reported offline metrics; gains/contact model are not approved hardware settings.

Configuration: Pinned MJCF b452a1f;MuJoCo2.2.2;PD180/3.5,sphere-only contacts

## What was executed (historical source scope)

FK/IK checks;vertical and+5mmFR forward simulation

## Failure, investigation, fix and retest

- Root cause: Native shank meshes overlap sphere by.5mm
- Fix: Runtime sphere-only contact normalization
- Retest: Two deterministic PASS; later bounded campaigns fail
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Simulation-only normalized contact/gains never hardware approval

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `docs/ONE_LEG_LIFT_SIMULATION.md; git fc5fe7e`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
