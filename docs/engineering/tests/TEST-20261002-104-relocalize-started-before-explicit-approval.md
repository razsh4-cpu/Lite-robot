---
schema: bipolix.test_session/v1
id: TEST-20261002-104
title: Historical evidence capture: Relocalize started before explicit approval
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: HISTORY, EVIDENCE
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: HISTORICAL_MASTER_INVENTORY.json HIST-076
---

# TEST-20261002-104 — Relocalize started before explicit approval

## Provenance and scope

Retrospective capture2026-10-02; no experiment executed by this record. Inventory scope `HIST-076`; source date/period `UNKNOWN` is preserved as reported, not newly established. Exact physical-run timestamp, operator, robot serial and manifest are UNKNOWN unless explicitly supported by the cited source. Historical source result `FAIL→FIX→OFFLINE_PASS` and evidence class `PRIMARY_PDF_HISTORICAL_REPORT_AND_COMMITTED_TESTS` remain source-bound. This conservative capture does not promote them into a new physical PASS.

## Objective and observations

Relocalization began before approval in historical report; explicit yes/cancel guard was added and later offline approval/cancel record exists. Preserve unsafe-start failure separately from subsequent software pass and pending physical session.

Configuration: Bounded recovery CLI; AUTONOMY lease

## What was executed (historical source scope)

Historical unsafe approval behavior reviewed; explicit y/N guard introduced

## Failure, investigation, fix and retest

- Root cause: Approval gating absent/too late in historical CLI
- Fix: Explicit default-no approval before ownership
- Retest: TEST-20260929-001 offline cancel/approval; complete physical CLI still incomplete
- Currentness: Historical evidence; no current hardware acceptance implied
- Lesson: Historical failure is distinct from the later correct offline record

Where the inventory states UNKNOWN or refers to the source, this record does not fill the gap by inference. Missing raw traces and exact manifests remain `EVIDENCE_INCOMPLETE`. A later software/model PASS never erases the earlier failure.

## Primary sources and relationships

- `PDF B p9`
- `PDF D p2`
- `L/docs/engineering/tests/TEST-20260929-001-relocalize-approval.md`

[Master inventory](../HISTORICAL_MASTER_INVENTORY.md) and [structured full event/stage fields](../HISTORICAL_MASTER_INVENTORY.json) retain complete executions/observations and primary provenance.
