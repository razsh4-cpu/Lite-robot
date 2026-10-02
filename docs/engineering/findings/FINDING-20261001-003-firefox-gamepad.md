---
schema: bipolix.engineering_finding/v1
id: FINDING-20261001-003
title: Linux joystick presence does not imply Firefox Gamepad visibility
date: 2026-10-01
status: CURRENT
categories: XBOX, NOMAD, SAFETY
evidence: NOMAD frontend Phase-3C Gamepad implementation and focused tests
---

# FINDING-20261001-003 — Firefox Gamepad activation and polling

`/dev/input/js0` proved Linux input availability, not browser exposure. Firefox
required a focused page/user controller interaction and robust handling of
`gamepadconnected` plus polling; strict assumptions about a `standard` mapping
could leave the UI `DISCONNECTED` despite the device existing.

- Evidence: current NOMAD Phase-3C UI source/tests in
  [RobotConsolePage.vue](../../../../NOMAD/frontend/web/src/pages/RobotConsolePage.vue)
  and [AuthorityPanel.vue](../../../../NOMAD/frontend/web/src/components/console/AuthorityPanel.vue).
- Live historical observation: UI later displayed `CONNECTED`, neutral, axes,
  and RB. A committed screenshot/log reference is `EVIDENCE MISSING`, so this
  finding does not itself promote the upcoming physical test.
- DO NOT REPEAT: equate `/dev/input/js0` with Gamepad API readiness or bypass
  neutral/fresh-RB gates to compensate for browser activation behavior.

## Retrospective session links

[TEST-20261002-031](../tests/TEST-20261002-031-firefox-gamepad-visibility-failure-and-reported-ui-recovery.md). These preserve scoped history and
remaining evidence limits; linking them does not constitute a new retest.
