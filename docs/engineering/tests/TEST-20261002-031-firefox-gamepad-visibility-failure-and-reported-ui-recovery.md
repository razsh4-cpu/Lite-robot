---
schema: bipolix.test_session/v1
id: TEST-20261002-031
title: Firefox Gamepad visibility failure and reported UI recovery
date: 2026-10-02
classification: HISTORICAL_CLAIM
result: PARTIAL
categories: XBOX, NOMAD, SAFETY
robot_id: UNKNOWN
git_sha: UNKNOWN
evidence: docs/engineering/findings/FINDING-20261001-003-firefox-gamepad.md
---

# TEST-20261002-031 — Firefox Gamepad visibility failure and reported UI recovery

## Retrospective provenance and acceptance

Capture date: 2026-10-02. Actual experiment date and exact deployed run SHA,
operator, robot serial, site and manifest are `UNKNOWN`. The dated source
report bounds the historical observation; it does not establish a new test.
Historical predeclared PASS/FAIL/ABORT criteria are `UNKNOWN` unless given
by that source. No new ROS, motion, hardware, service or deployment action
is authorized or reported here.

## Failure, fix, result and remaining proof

Linux joystick presence did not expose the device through Firefox Gamepad API. Focus and controller interaction, connection events plus polling, and mapping handling addressed the software path. The finding reports that the UI later showed CONNECTED, neutral, axes and RB, but the original screenshot/log is missing. Preserve that observation as a historical UI claim, not physical motion acceptance or permission to bypass neutral/fresh-RB/continuous-deadman guards.

## Evidence and relationships

- [Primary retained report](../findings/FINDING-20261001-003-firefox-gamepad.md).
- Related records: [FINDING-20261001-003](../findings/FINDING-20261001-003-firefox-gamepad.md), [TEST-20261001-002](TEST-20261001-002-phase3c-xbox-physical.md).
- Original raw logs/bag/video and isolated retest manifest: `EVIDENCE MISSING`.
- Preserve this session's evidence scope; do not infer physical PASS or current
  deployment/readiness from source presence, a software test, or another run.
