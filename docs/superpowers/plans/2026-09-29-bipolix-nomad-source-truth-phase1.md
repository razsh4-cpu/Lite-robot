# Bipolix Source-Truth and NOMAD Phase-1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile the current physically proven Bipolix/Lite3 implementation into private Git, then complete the strictly read-only NOMAD Phase-1 platform-status gateway on `raz/bipolix-integration`.

**Architecture:** Lite-robot remains authoritative for onboard ROS2, safety, arbitration, navigation, state, and hardware adapters. NOMAD consumes a versioned vendor-neutral MQTT status contract and displays authoritative Bipolix state without creating any motion or ownership path. Reconciliation is targeted: Mini-PC remains read-only, generated/runtime state is excluded, and approved safety rulings select the 180-second test override, deployed LOCAL_XBOX service behavior, and stricter Git health checks.

**Tech Stack:** C++/CMake/CTest, Python/pytest/ROS2 Jazzy configuration, systemd, MQTT, Python backend, Vue/TypeScript frontend, Vitest/ESLint.

**Spec:** `/home/raz/.codex/attachments/209b09b6-58b1-4c05-88d8-1e0321ca2bb7/Pasted text.txt`

## Global Constraints

- Mini-PC is read-only: no deployment, service restart, ROS command, UDP command, ownership acquisition, or hardware motion.
- Bipolix localization test override is exactly 180 seconds and remains test-session-only.
- Production LOCAL_XBOX service preserves the deployed Mini-PC behavior; legacy/R&D variants are retained only when consumers justify them.
- Health/readiness uses real lifecycle, TF, and freshness checks and fails closed.
- NOMAD Phase 1 exposes `robot.platform_status/v1` with `motion_commands_supported: false` and no motion-capable API or transport.
- NOMAD work remains only on `raz/bipolix-integration`; no merge, PR, or NOMAD push.
- Existing non-Bipolix NOMAD profiles remain unchanged.

## Review Focus

- Stale/missing status must render as stale/offline/unknown, never healthy.
- Two lease domains must remain distinct: NOMAD operator lease versus Bipolix robot-side command ownership.
- Bipolix deployment profile must not activate duplicate Nav2, AMCL, odometry, TF, command arbitration, telemetry UDP, or robot-side execution.
- Multiple fixture robots must remain isolated in MQTT ingestion and UI selection.
- No Phase-1 source file may publish velocity, acquire ownership, call Nav2 actions, issue posture commands, or open Lite3 UDP command sockets.

---

### Task 1: Reconcile approved Bipolix safety decisions

**Files:**
- Modify: `onboard_ros2_ws/src/sensor_visualization/scripts/lite3_nav_test_override.py`
- Modify: `onboard_ros2_ws/src/lite3_state_estimation/lite3_state_estimation/localization_guard.py`
- Modify: `onboard_ros2_ws/src/sensor_visualization/test/test_nav_test_override.py`
- Modify: `systemd/lite3-local-xbox-control.service`
- Modify: `tests/xbox_startup_service_test.sh`
- Modify: `onboard_ros2_ws/src/sensor_visualization/CMakeLists.txt`
- Create: `docs/architecture/SOURCE_OF_TRUTH_RECONCILIATION_2026-09-29.md`

**Interfaces:**
- Consumes: approved master directive and existing command-source/localization contracts.
- Produces: one coherent Git-controlled implementation matching the approved 180-second and deployed LOCAL_XBOX decisions.

- [ ] Change tests first to require the 180-second TTL and deployed LOCAL_XBOX service dependencies; run focused tests and observe the expected failures.
- [ ] Apply the minimal source/unit changes and remove only the redundant CMake install declaration proven absent from deployed source.
- [ ] Record file authority and legacy/generated classifications without importing artifacts.
- [ ] Run focused tests again and commit the reconciliation.

### Task 2: Validate and publish Bipolix source of truth

**Files:**
- Verify: complete Lite-robot tree.

**Interfaces:**
- Consumes: Task 1 reconciled source.
- Produces: validated private Git SHA used by NOMAD integration.

- [ ] Run static/Python checks, offline build, CTest, full regression, stale-reference search, and `git diff --check`.
- [ ] Review the complete diff for generated/runtime state and authority changes.
- [ ] Commit any validation-document corrections separately if necessary.
- [ ] Push the current Lite-robot branch to its verified private `origin` and record the exact SHA.

### Task 3: Revalidate and implement NOMAD contract/backend gateway using TDD

**Files:**
- Modify/Create: exact NOMAD contract, backend ingestion, FleetRegistry, fixture, deployment-profile and test files identified by repository inspection.

**Interfaces:**
- Consumes: current Lite-robot authoritative status semantics.
- Produces: `robot.platform_status/v1` MQTT ingestion and read-only fleet status with explicit freshness and schema rejection.

- [ ] Re-read the synchronized Bipolix source and confirm the approved authority boundary remains valid.
- [ ] Add failing contract/backend tests for versioning, malformed payloads, stale/offline/unknown state, multiple robots, isolation, and absence of motion support.
- [ ] Implement the minimum vendor-neutral schema, MQTT ingestion, FleetRegistry integration, deterministic fixtures, and Bipolix deployment exclusions.
- [ ] Run focused and relevant full backend/contract tests; commit logical backend/profile changes.

### Task 4: Implement NOMAD read-only UI using TDD

**Files:**
- Modify/Create: existing NOMAD fleet/robot status components and tests identified by repository inspection.

**Interfaces:**
- Consumes: Task 3 FleetRegistry platform status.
- Produces: robot-selected Bipolix status rendering without independent authority inference.

- [ ] Add failing UI tests for robot switching, state rendering, stale/offline/refusal display, capability unknowns, and motion unsupported.
- [ ] Implement minimal UI additions using existing patterns while preserving Xbox/lease behavior.
- [ ] Run focused frontend tests, typecheck, ESLint, and full relevant frontend suite; commit UI changes.

### Task 5: Final offline validation and branch checkpoint

**Files:**
- Verify: NOMAD branch and committed specification/deployment documentation.

**Interfaces:**
- Consumes: Tasks 3-4.
- Produces: validated `raz/bipolix-integration` Phase-1 checkpoint with no motion path.

- [ ] Run contract, backend, frontend, Python/static, typecheck, ESLint, and `git diff --check` validations.
- [ ] Search source for prohibited motion/ownership/Nav2/UDP constructs in the Phase-1 gateway.
- [ ] Review complete branch diff, create final logical commit(s), and confirm NOMAD `main` untouched.
- [ ] Stop without NOMAD push, merge, PR, or Phase-2 implementation.
