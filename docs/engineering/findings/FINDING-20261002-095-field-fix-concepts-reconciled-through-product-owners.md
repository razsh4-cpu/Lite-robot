---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-095
title: Deployed field-fix concepts reconciled through existing product owners
date: 2026-10-02
status: CURRENT
categories: DEPLOYMENT, NAVIGATION, ODOMETRY, SAFETY
evidence: Git141b497/b4f6a48 field reports and current offline regressions
---

# FINDING-20261002-095 — Field fix source reconciliation

Original failures: aptMPPI reportedly SIGILL on J6413 without AVX; stationary Auto telemetry reportedly drifted EKF/SLAM. Investigation distinguished deployed b4f6a48 installed hashes from current0c48b4d branch. Safe fix: reimplement CPU fallback in existing navigation composition and guarded-dispatch-based stillness in existing Lite3 driver. Existing network/authority/mux/vendor writer remain owners; no parallel stack or deployed-file import.

Offline retest: [session](../tests/TEST-20261002-106-source-reconciliation-and-knowledge-workflow-offline.md). Source fix acceptance is offline only; deployed integration and physical retest remain UNKNOWN/pending. RPP dependency was declared, never installed on the Mini-PC by this task. Command-intent odometry is not measured localization; handheld/pushed/coasting applicability limits remain explicit.

Do not repeat: deploy whole branches by age/location, restore AVX-only binary selection, mistake telemetry noise for physical displacement, let rejected intent unlock odometry, import uncalibrated site limits/sign, or promote synthetic/offline results to physical proof. [Initial deployed audit](../MINIPC_DEPLOYED_STATE_AUDIT.md) preserves earlier absence and unchanged capture state.
