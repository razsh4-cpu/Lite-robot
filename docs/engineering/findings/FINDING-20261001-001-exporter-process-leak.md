---
schema: bipolix.engineering_finding/v1
id: FINDING-20261001-001
title: Timed-out platform-status probes leaked ROS child processes
date: 2026-10-01
status: RESOLVED
categories: PERFORMANCE, RELIABILITY, MINI_PC, ROS2
evidence: git commit e396f55
---

# FINDING-20261001-001 — Exporter process leak

Ping could remain responsive while SSH banner/service responsiveness degraded.
The old exporter timed out short ROS CLI probes without reliably terminating
and reaping their process groups, causing child/task/memory growth. Commit
`e396f55` adds process-group termination/reaping and regression coverage.

- Evidence: commit `e396f55`, [platform exporter architecture](../../architecture/PLATFORM_STATUS_EXPORTER.md),
  and [performance baseline](../../operations/PERFORMANCE_BASELINE.md).
- Root cause: resource exhaustion from accumulating probes, not proof of a
  Wi-Fi driver failure.
- Known good: bounded probe lifecycle; distinguish brief probe spikes from
  monotonic growth.
- Validation limitation: exact soak metrics referenced during the incident are
  not retained as a standalone committed raw dataset (`EVIDENCE MISSING`).
- DO NOT REPEAT: launch periodic ROS CLI subprocesses without killing and
  reaping the complete process group on timeout.
