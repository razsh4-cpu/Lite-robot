---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-088
title: Historical evidence capture: Real body-shift measured-speed guard abort
date: 2026-10-02
status: HISTORICAL
categories: HISTORY, EVIDENCE
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-037
---

# FINDING-20261002-088 — Real body-shift measured-speed guard abort

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-037`; source date/period `2026-09-18` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL` and evidence class `HISTORICAL_PHYSICAL_TRACE_ANALYSIS_REPORT` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Recorded measured FL-knee speed0.514640808rad/s caused abort. Correlation with abrupt100/2.5→60/0.7 gain transition was an inference, not proven physical cause. Offline selection retained stand gains rather than weakening speed guards. No historical retry was implied.

Configuration: Abruptkp100/2.5→60/.7;5mm plan

## What was executed (historical source scope)

One approved body-shift attempt then trace replay

## Failure, investigation, fix and retest

- Root cause: Gain discontinuity correlated, causal root UNKNOWN
- Fix: Compare A abrupt Bstandgains Csmooth;select B without relaxing limits
- Retest: Offline maxdelta.0229582rad,maxspeed.0215233rad/s
- Currentness: Historical evidence; current hardware state UNKNOWN
- Lesson: Keep real guard failure; remove discontinuity before causal claim

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `docs/BODY_SHIFT_OFFLINE_REVIEW_2026-09-18.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
