---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-087
title: Historical evidence capture: Original vendor controller transport investigation
date: 2026-10-02
status: HISTORICAL
categories: HISTORY, EVIDENCE
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-032
---

# FINDING-20261002-087 — Original vendor controller transport investigation

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-032`; source date/period `2026-09-14` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `INCONCLUSIVE` and evidence class `PASSIVE_REPORT_AND_STATIC_ANALYSIS` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Static full0x21010130 SimpleCMD framing was distinguished from bare low-word guesses. Passive original-controller captures showed heartbeat but not axis-bearing transport; native handset transport remained UNKNOWN. Do not claim its physical transport was reverse engineered completely.

Configuration: Passive captured original-controller successful movement

## What was executed (historical source scope)

TTY/device/IPC audit and sourcefiltered captures

## Failure, investigation, fix and retest

- Root cause: Original controller axis transport remains UNKNOWN
- Fix: Use separately proven external manual axes
- Retest: Forward source-backed pulse
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Heartbeat capture is not axis transport proof

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `docs/HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
