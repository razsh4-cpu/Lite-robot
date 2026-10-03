---
schema: bipolix.test_session/v1
id: TEST-20261003-001
title: Independent autonomy no-motion staging against existing INERT runtime
date: 2026-10-03
classification: PARTIAL
result: PARTIAL
actual_behavior: Staged localization build passed; privileged activation pending
categories: NAVIGATION, LOCALIZATION, DEPLOYMENT, SAFETY
robot_id: robot_01
git_sha: 534ab2df1c2566190dd47a9ae914988ff0d570ae
evidence: Source tests and read-only SSH observations; physical acceptance pending
---

# TEST-20261003-001 — independent no-motion integration

## Objective / PASS / FAIL / ABORT

Prepare existing sensors/TF/odom/map/AMCL/Nav2 and NavigationPort without acquiring
AUTONOMY or transmitting autonomous motion. PASS requires actual fresh live
inputs, 80% x3, correct RViz alignment and planning-only path. FAIL: missing/stale
input or wrong map. ABORT: competing authority, transmit enabled, SABLE active,
duplicate runtime/sensor owner, or any physical motion intent.

## Current evidence

- Sole UDP43897 receiver: existing HIGH-LEVEL PID19131 at inspection; do not treat
  the PID as persistent identity. Actual command-line transmit=false,
  zero_only=true, require_deadman=true; COMMAND_SOURCE=NONE.
- Existing immutable runtime bundle: `fc2e73458e7de1fdd10440bd2bd380c39ae8cdd8`.
  Runtime bridge SHA256 `149ced353a8e3940e6e004fa527ab379041518789d2bb379e4a3033219b24cde`.
  No runtime/relay/unit changes were made during staging.
- SABLE edge unexpectedly active; SABLE ROS inactive. Sudo needs operator password.
  Do not claim SABLE is stopped or navigation is live before the apply step.
- Existing Home_Map: `/home/abx/Desktop/robotdog_ws/src/maps/Home_Map/map.yaml`.
  YAML SHA256 `ac57071029281d82d983d9eced88449d95d28f52a7dd90ed1a5174f02f6c445b`;
  PGM SHA256 `952eb7310fc910c0371d90b8a4ed2d500bc81465aa0cf916bbc0c36a7a872cba`.
  Grayscale trinary, 150x133 cells, 0.05m resolution. Structural validity does
  not prove suitability/alignment for the robot's current physical environment.
- Only localization package built in a new staging workspace: 1 package passed.
  Package discovery initially failed because this existing Python package lacks
  an AMENT prefix hook. Use the established explicit prefix; do not modify the
  active runtime environment or install another telemetry receiver.
- Real Jazzy NavigationPort/runtime construction passed with execution approval
  false and source NONE; no goal sent. Nav2/LiDAR launch-description expansion
  passed. This is construction/package validation, not active lifecycle proof.
- Focused local checks: 88 passed, 3 manual/takeover tests deselected; shell
  syntax/diff checks passed. Knowledge validation still reports pre-existing
  sibling/external evidence links unavailable inside this worktree.
- Dedicated Nav2 command topic `/autonomy_validation/cmd_vel`; private preview
  `/day2/preview_goal` uses ComputePathToPose, not NavigateToPose execution.
- GUI/RViz remains laptop-side. No vendor control package, Xbox source or GUI
  was deployed or started by this staging operation.

## Remaining validation / rollback

Operator sudo activation, then actual graph/lifecycle/freshness/AMCL score,
costmaps, obstacle returns and RViz/private path preview. Missing standing,
hardware readiness or localization must remain blocked, not fabricated.

Rollback stops only `lite3-autonomy-validation.service` and
`lite3-nav2-safety-monitor.service`. Existing independent runtime remains running;
SABLE stays off. Physical AUTONOMY/motion activation is separate authorization.

See [integration plan](../../../backend/lite3/LIVE_VALIDATION_PLAN.md).
