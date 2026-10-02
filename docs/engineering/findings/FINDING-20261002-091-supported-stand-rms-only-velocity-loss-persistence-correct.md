---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-091
title: Historical evidence capture: Supported stand RMS-only velocity loss persistence correction
date: 2026-10-02
status: HISTORICAL
categories: HISTORY, EVIDENCE
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-066
---

# FINDING-20261002-091 — Supported stand RMS-only velocity loss persistence correction

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-066`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL→FIX→REPORTED_PASS` and evidence class `PRIMARY_PDF_HISTORICAL_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Once stand was established, first RMS window could outlive an isolated raw motion and falsely turn it into persistent loss. Source requires RMS-only violation across two50ms windows (100ms). This fixes persistence after establishment, separate from initial convergence definition; physical retest not inferred.

Configuration: Measured-speed threshold0.15rad/s; RMS50ms;100ms RMS-only persistence

## What was executed (historical source scope)

Historical supported hold followed by software convergence/hold investigation

## Failure, investigation, fix and retest

- Root cause: Brief RMS-only transient interpreted as sustained hold loss; distinct from later raw-speed .51464rad/s body-shift abort
- Fix: 100ms persistence for RMS-only hold loss; tilt/position/stale/invalid retained
- Retest: Stable stand/release reported; raw synchronized bundle missing
- Currentness: Historical evidence; no current hardware acceptance implied
- Lesson: Preserve chronology: CURRENT_STATUS older50ms text differs from source100ms; never apply this to raw body-shift speed guard

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `PDF A p4 /home/raz/Desktop/robot_dog/Lite3_Robot_Dog_Full_Development_Documentation_HE_EN.pdf`
- `L/state_machine/supervised_stand_monitor.hpp:83`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
