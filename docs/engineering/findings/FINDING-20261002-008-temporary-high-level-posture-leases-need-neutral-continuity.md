---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-008
title: Temporary HIGH-LEVEL posture leases need neutral continuity
date: 2026-10-02
status: HISTORICAL
categories: SAFETY, ROBOT_CONTROL
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# FINDING-20261002-008 — Temporary HIGH-LEVEL posture leases need neutral continuity

## Finding and applicability

The Day-1/Day-2 summary reports temporary robot stand lease loss, neutral-heartbeat repair, and competing-C2 removal. The contemporary closeout reports SITTING→STANDING, no planar velocity, release, and NONE. Keep this product posture path distinct from MotionSDK supported Stand. Current browser Stand and dedicated down CLI do not inherit its physical proof.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- [Lite3_Full_Project_Complete_HE_2026-09-27.pdf](../../../../../Desktop/robot_dog/Lite3_Full_Project_Complete_HE_2026-09-27.pdf) p8.
- [Lite3_Day1_Day2_Summary_HE.pdf](../../../../../Desktop/robot_dog/Lite3_Day1_Day2_Summary_HE.pdf) p2.

- Related records: [TEST-20260927-004](../tests/TEST-20260927-004-laptop-xbox-manual.md), [FINDING-20260930-001](FINDING-20260930-001-command-authority.md), [TEST-20261002-004](../tests/TEST-20261002-004-high-level-robot-stand-temporary-lease-acceptance.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
