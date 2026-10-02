---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-002
title: Command-source markers do not establish real ownership
date: 2026-10-02
status: KNOWN_ISSUE
categories: SAFETY, RELIABILITY
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# FINDING-20261002-002 — Command-source markers do not establish real ownership

## Finding and applicability

The historical stale LAPTOP_XBOX/AUTONOMY marker could block later acquisition after the real owner was gone. Safe recovery restored NONE, but parity across every source remains partial. Compare marker, kernel lock, and process liveness together. Cleanup must zero through the existing path, clear old authorization, and remain idempotent.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p1.
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p7.

- Related records: [TEST-20260927-004](../tests/TEST-20260927-004-laptop-xbox-manual.md), [TEST-20260929-001](../tests/TEST-20260929-001-relocalize-approval.md), [FINDING-20260930-001](FINDING-20260930-001-command-authority.md), [TEST-20261002-011](../tests/TEST-20261002-011-ghost-command-source-marker-safe-recovery.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
