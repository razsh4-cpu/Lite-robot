---
schema: bipolix.engineering_finding/v1
id: FINDING-20260927-004
title: Unbounded HIGH-LEVEL odometry publication overloaded ROS executors
date: 2026-09-27
status: RESOLVED
categories: ODOMETRY, ROS2, PERFORMANCE
evidence: docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md
---

# FINDING-20260927-004 - Bound odometry publication rate

The product HIGH-LEVEL bridge originally published `/odom` and TF at approximately
154 Hz. This created unnecessary executor/DDS pressure without adding useful
navigation information. Publication was capped at 50 Hz while heartbeat and
fresh telemetry processing remained independent.

- Evidence: [Day-2 closeout](../../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
- Known good: HIGH-LEVEL telemetry remains the sole Product odometry/TF owner;
  bounded publication does not mean bounded internal freshness checks.
- DO NOT REPEAT: publish every vendor callback directly into the navigation graph
  or introduce a second odometry/TF owner.

## Recovery and correction provenance

Recovered from Git commit `173f61d` on 2026-10-02 without changing the ID.
The recovered text said approximately 1 kHz; its cited contemporary closeout
and operations knowledge base report approximately 154 Hz. This record now
uses the source-backed value; no new rate measurement was performed.

## Retrospective session links

[TEST-20261002-027](../tests/TEST-20261002-027-bounded-product-odometry-publication-repair.md). These preserve scoped history and
remaining evidence limits; linking them does not constitute a new retest.
