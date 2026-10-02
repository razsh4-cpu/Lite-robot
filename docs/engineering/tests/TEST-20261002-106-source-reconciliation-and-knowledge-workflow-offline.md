---
schema: bipolix.test_session/v1
id: TEST-20261002-106
title: CPU and idle-odometry source reconciliation with offline knowledge workflow
date: 2026-10-02
classification: OFFLINE_PROVEN
result: PASS
categories: ROS2, ODOMETRY, NAVIGATION, SAFETY, KNOWLEDGE
robot_id: UNKNOWN
git_sha: 0c48b4d5ad3aa5270744795fc85eb414981249f4
evidence: SAFE_AUTONOMOUS_CLOSURE.md and continuation validation evidence
---

# TEST-20261002-106 — Offline source reconciliation

## Objective and acceptance

Integrate justified field concepts through existing SABLE navigation/driver owners and prove future capture without hardware. PASS: inert regressions verify CPU selection/caps, dispatch-bound idle hold/time handling, and synthetic sandbox knowledge discovery/read-before-decision/index validation; no guards weakened, site limits/sign not promoted. FAIL: unsafe controller selection, rejected/neutral command unlocking odom, canonical synthetic record promotion, lost authority/stop guard. ABORT: robot command, ownership, live graph, deployment, secret/privileged/destructive operation.

## Configuration and execution

Product working-tree baseline0c48b4d on bipolix_robot; exact tested files and subsequent commit SHAs recorded in continuation verification. The baseline SHA does not identify the dirty implementation alone. Pure node-method tests use inert objects, never instantiate the hardware driver or bind vendor sockets. Navigation composition imports source/ROS definitions without ROS initialization/graph. The existing-tool dry run reads canonical rules/records before a mock evidence-class decision and writes only an external SYNTHETIC sandbox.

TDD retained initial9 idle failures→pass, encoded-zero edge failure→pass; CPU missing-feature18failures→pass then unsafe RPP cases3failures→pass; workflow5missing-feature failures→pass and grounding-rule regression→pass. Final fresh command results are authoritative in the continuation verification artifact; no full live ROS package test or physical proof inferred.

## Observations and limitations

CPU absent/unknownAVX chooses compatible RPP; explicit unsafe MPPI refused; original and effective caps checked. Driver last-drive time advances only after complete successful guarded nonzero output (encoded-neutral axis excluded);0.5s hold configurable,0disables. Pose x/y held/twistzero; heading/IMU remain telemetry. Push/handheld/coasting may be suppressed, local UDPsend is not vendor acknowledgement. Full physical matrix remains unexecuted.

[Related finding](../findings/FINDING-20261002-095-field-fix-concepts-reconciled-through-product-owners.md), [synthetic proof](../evidence/SYNTHETIC_WORKFLOW_PROOF_20261002.json), [site review](../SITE_CONFIGURATION_RECONCILIATION.md).
