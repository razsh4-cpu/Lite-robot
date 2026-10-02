---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-003
title: Installed executable helpers also need an importable module
date: 2026-10-02
status: RESOLVED
categories: DEPLOYMENT, NAVIGATION
evidence: /home/raz/ros-robot-cc/Lite-robot/docs/operations/ENGINEERING_KNOWLEDGE_BASE.md
---

# FINDING-20261002-003 — Installed executable helpers also need an importable module

## Finding and applicability

An extensionless executable install did not satisfy Python imports of lite3_nav_test_override. CMake now preserves executable and .py module installation; commit 4a95852 records the packaging requirement. Resolution refers to source/packaging coverage. Clean installed Mini-PC import and obstacle workflow acceptance remain separate deployment validation.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [ENGINEERING_KNOWLEDGE_BASE.md](../../operations/ENGINEERING_KNOWLEDGE_BASE.md).
- [FAILURES_AND_FIXES.md](../../FAILURES_AND_FIXES.md).
- [CMakeLists.txt](../../../onboard_ros2_ws/src/sensor_visualization/CMakeLists.txt).

- Related records: [TEST-20261002-006](../tests/TEST-20261002-006-importable-obstacle-helper-packaging-repair.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
