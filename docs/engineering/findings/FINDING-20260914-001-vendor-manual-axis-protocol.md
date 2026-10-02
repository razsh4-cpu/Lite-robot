---
schema: bipolix.engineering_finding/v1
id: FINDING-20260914-001
title: Vendor manual-axis locomotion requires full source-qualified SimpleCMD codes
date: 2026-09-14
status: CURRENT
categories: ROBOT_CONTROL, XBOX, SAFETY
evidence: docs/HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md
---

# FINDING-20260914-001 - Vendor manual-axis protocol

The robot-matched `jy_exe` path accepts packed 12-byte SimpleCMD frames and
requires the full source/category-qualified codes: forward `0x21010130`, lateral
`0x21010131`, and yaw `0x21010135`. Bare `0x0130` fails the category check;
legacy 320/321/325 encodings did not enter locomotion on this build.

- Validation: a bounded forward pulse is physically proven in
  [TEST-20260914-001](../tests/TEST-20260914-001-vendor-manual-axis-forward.md).
- Evidence: [high-level investigation](../../HIGH_LEVEL_CONTROL_INVESTIGATION_2026-09-14.md)
  and current codec constants.
- DO NOT REPEAT: retry legacy codes, guess packet sources, or bypass exclusive
  command ownership. The current Product path wraps this protocol with arbiter,
  freshness, neutral, and watchdog protections.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
