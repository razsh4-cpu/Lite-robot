# Repository migration plan — Phase B

This plan follows the Phase-A evidence in
[REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md). Migration Group 1 is complete;
Groups 2 and 3 are complete; Groups 4–13 remain unexecuted.

Rule for every group:

```text
audit exact files
→ record old owners and paths
→ move one small coherent group
→ update all code/build/unit/launch/test/docs references
→ build relevant targets
→ run the maintained full regression suite (242 tests at this audit; never
  fewer than the historical 223-test baseline)
→ run git diff --check
→ review diff and commit the group
→ proceed only after the group is green
```

No group may change a hardware owner, safety permit, lease, watchdog, map,
extrinsic, velocity limit or deployed command behavior as a side effect.

## Proposed target tree

The final tree expresses Product vs R&D while retaining a conventional colcon
workspace for onboard ROS packages:

```text
.
├── product/
│   ├── onboard_ros2_ws/
│   │   └── src/
│   │       ├── bipolix_safety/               # leases, watchdogs, gates
│   │       ├── bipolix_navigation/           # localization, mapping, Nav2
│   │       ├── bipolix_perception/           # LiDAR/D455 sensor management
│   ├── missions/                             # dormant until Day 3 approval
│   ├── c2/                                   # laptop selection/manual source
│   ├── operator/                             # stable operator CLI
│   ├── visualization/                        # laptop RViz only
│   └── deployment/
│       ├── systemd/
│       └── install/
├── platform/
│   ├── robot_interfaces/                     # vendor-neutral contracts
│   ├── robot_adapters/
│   │   └── lite3/                             # DeepRobotics-specific adapter
│   ├── config/
│   │   ├── robot_types/
│   │   ├── robot_instances/
│   │   ├── navigation/
│   │   ├── localization/
│   │   ├── sensors/
│   │   └── safety/
│   ├── calibration/
│   └── sites/
├── rnd/
│   ├── low_level/
│   │   ├── interface/
│   │   ├── state_machine/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── tools/
│   │   └── tests/
│   ├── policies/
│   │   ├── models/
│   │   └── runtime/
│   ├── mujoco/
│   │   ├── models/
│   │   ├── experiments/
│   │   └── simulation/
│   └── evidence/                             # curated manifests/results only
├── third_party/
├── docs/
├── tests/
│   ├── architecture/
│   ├── product/
│   └── acceptance/
├── CMakeLists.txt                            # transitional dispatcher only
├── pytest.ini
├── AGENTS.md
├── LICENSE
└── README.md                                 # platform entry point
```

This is an end state, not a single move. In particular,
`onboard_ros2_ws/src/sensor_visualization` remains intact through the early
groups; later it is split package-by-package while installed executable names
remain compatible.

## Ordered dependency-safe migration groups

### Group 1 — generated-log hygiene (completed)

- **Source:** root `MUJOCO_LOG.TXT` and
  `interface/robot/simulation/MUJOCO_LOG.TXT`.
- **Destination:** `rnd/evidence/legacy/mujoco/`, preserving distinct files as
  `root-MUJOCO_LOG.TXT` and `interface-simulation-MUJOCO_LOG.TXT`.
- **Reason:** both are generated simulator logs, have no code/build/unit/launch
  reference, and previously made generated output look like source.
- **References requiring updates:** none found in code, CMake, Python, shell,
  systemd, launch or tests. Documentation retains the historical source paths
  for provenance. No ignore-rule change was included in this group.
- **Tests:** static reference scan; relevant MuJoCo configure/build smoke; the maintained full regression suite; `git diff --check`.
- **Risk:** **LOW**.
- **Rollback:** revert the single migration commit; files return to exact paths.
- **Prerequisites:** none.
- **Result:** completed in commit
  `497743e04da11ca0a3cb1a19b2f0bbbcc6e56b06`; offline build passed, CTest
  passed `25/25`, Python regression passed `242`, and `git diff --check`
  passed. No Mini-PC or physical robot was accessed, and runtime and safety
  behavior were unchanged.

### Group 2 — host/editor and manual-backup hygiene (completed)

- **Source:** `.marscode/deviceInfo.json`, first-party `*.before_*`, `*.pre_*`
  and `*.save` snapshots (exclude legitimate third-party filenames such as
  Eigen CI `before_script`).
- **Destination:** curated `docs/handoff_evidence/source_snapshots/` only where
  evidence must remain; otherwise Git history, with ignore rules preventing
  recurrence.
- **Reason:** these are machine/editor state or historical copies, not build
  inputs; several are byte-identical duplicates.
- **References requiring updates:** handoff documents that name snapshots;
  confirm CMake glob does not accidentally compile renamed `.cpp` backups (the
  current `state_machine/*.c*` glob can match backup-like C++ names depending on
  suffix).
- **Tests:** CMake target source list comparison before/after; root C++ build;
  the maintained full regression suite; static reference scan.
- **Risk:** **LOW/MEDIUM** because of the broad CMake glob.
- **Rollback:** revert group commit.
- **Prerequisites:** Group 1 recommended, not mandatory.
- **Result:** unique historical snapshots were moved to
  `docs/handoff_evidence/source_snapshots/group2-legacy-backups/`; exact
  duplicates and `.marscode/deviceInfo.json` were removed; `.marscode/` is
  narrowly ignored. Offline build passed, CTest passed `25/25`, the Python
  regression suite passed `242`, and no runtime or safety source was changed.

### Group 3 — root MuJoCo experiment entry points (completed)

- **Source:** `grid_162.py`, `sensitivity_test.py`, and `single_leg_sweep.py`.
- **Destination:** `rnd/mujoco/experiments/`.
- **Reason:** remove R&D experiments from repository root and place them beside
  their simulation responsibility.
- **References requiring updates:** replace hard-coded
  `/home/raz/ros-robot-cc/Lite-robot`; update runner/model/artifact discovery,
  handoff docs and any human command examples. `single_leg_sweep.py` required a separate Group-3B commit because its
  prior repository-root discovery depended on its root-level location.
- **Tests:** AST/CLI dry validation with subprocess mocked; one offline smoke
  fixture; root MuJoCo build; the maintained full regression suite.
- **Risk:** **LOW/MEDIUM**.
- **Rollback:** revert commit; output artifacts are not rewritten by migration.
- **Prerequisites:** Group 1 so generated log behavior is understood.
- **Group 3 result:** `grid_162.py` and `sensitivity_test.py` moved to
  `rnd/mujoco/experiments/`. Their experiment parameters, MuJoCo runner,
  model and artifact destinations are unchanged; hard-coded home paths were
  replaced by repository-marker discovery. Group 3B moved `single_leg_sweep.py` to the same
  authoritative experiments directory with identical CLI and output semantics. Python compilation, three-working-directory
  path checks and mocked runner smokes passed for both subgroups; Group 3B also
  preserved the `--smoke`/`--batch` CLI. Offline build passed, CTest passed
  `25/25`, and the Python regression suite passed `242`.

### Group 4 — formalize pure generic Product contracts

- **Source:** `src/robot_interfaces`, `src/robot_adapters/lite3`,
  `src/missions`, and `config/robots/lite3`.
- **Destination:** initially package in place; later
  `platform/robot_interfaces`, `platform/robot_adapters/lite3`,
  `platform/config/robots/lite3`, and `product/missions` after packaging is proven.
- **Reason:** remove test-only `sys.path` injection and make dependency direction
  explicit without connecting to runtime.
- **References requiring updates:** `tests/architecture/conftest.py`, imports,
  architecture docs and packaging metadata. No ROS/hardware imports may enter
  the generic interface.
- **Tests:** all architecture contract/config/mission tests, install/import test,
  the maintained full regression suite.
- **Risk:** **LOW** for in-place packaging; **MEDIUM** for physical move.
- **Rollback:** retain prior import compatibility shim for one release; revert
  commit if imports differ.
- **Prerequisites:** none, but execute after hygiene groups for a clean baseline.
- **Group 4A result:** the three pure Python components are now independently
  packaged in place with explicit `pyproject.toml` metadata. The Lite3 adapter
  declares its dependency on the generic robot-interface distribution; missions
  remain independent and dormant. Declarative pytest paths replace the removed
  test-only `sys.path` mutation. No file location, public import, runtime entry
  point, configuration authority, or behavior changed. Isolated source-package
  builds and architecture tests passed.
- **Group 4B result:** architectural ownership was approved explicitly. The
  generic interface and robot configuration moved to `platform/`; the
  DeepRobotics-specific adapter moved to `platform/robot_adapters/lite3`; and
  robot-agnostic mission contracts moved to `product/missions`. Public Python
  imports, package metadata, contract semantics, and offline-only status are
  unchanged. No runtime or deployment path consumes these components.

### Group 5 — split laptop operator validation tools from stable CLI

- **Source:** `operator/`.
- **Destination:** `product/operator/cli`, `product/operator/deployment`,
  `product/operator/diagnostics`, and `product/operator/validation`.
- **Reason:** distinguish installed user commands from one-shot deployment and
  physical-test tooling.
- **References requiring updates:** installed shell wrappers, command registry,
  tests, README/docs, `scp` source paths and user systemd units.
- **Tests:** every operator test, fresh-shell wrapper tests with robot offline,
  approval/no-motion fixtures, the maintained full regression suite.
- **Risk:** **MEDIUM/HIGH** because normal-terminal commands use exact paths.
- **Rollback:** compatibility wrappers at previous paths for one release plus
  revertable install manifest.
- **Prerequisites:** Group 4 package/import conventions.
- **Group 5A result:** all five operator Python regression modules moved from
  `operator/` to `tests/operator/`. Test fixtures now resolve the unchanged
  operator sources explicitly from the repository root. No command source,
  installed wrapper, executable, service, deployment file, or CLI behavior
  changed.

### Group 6 — laptop C2 and visualization packaging

- **Source:** `c2/`, `laptop_visualization/`.
- **Destination:** `product/c2/` and `product/visualization/`, installed through
  a laptop package or stable `$HOME/.local` prefix.
- **Reason:** eliminate `/home/raz/ros-robot-cc/...` source-tree execution and
  make laptop deployment reproducible.
- **References requiring updates:** both user systemd units, connect/disconnect
  wrappers, robot registry path, RViz watcher/session scripts, docs and tests.
- **Tests:** joystick fixture tests, C2 lease/no-takeover tests, RViz
  single-instance tests, offline Mini-PC behavior, the maintained full regression suite.
- **Risk:** **HIGH** because C2 is a safety-relevant motion source and RViz has
  one canonical config requirement.
- **Rollback:** keep installed previous package/version and a service-unit
  rollback command; never run two C2 publishers.
- **Prerequisites:** Group 5 stable wrapper/install convention.

### Group 7 — retire or quarantine the legacy root Xbox deployment

- **Source:** root `scripts/lite3_*` control/readiness files and `systemd/`.
- **Destination:** `rnd/low_level/deployment/legacy_xbox/` or a documented
  `legacy/` quarantine; Product equivalents remain in ROS package.
- **Reason:** same-named divergent services/scripts currently obscure which
  architecture is canonical.
- **References requiring updates:** `tests/xbox_startup_service_test.sh`, root
  units, docs and any installed `/home/abx/Lite-robot` units discovered during a
  later live deployment audit.
- **Tests:** exact behavior tests for the legacy group; Product Xbox reconnect
  tests; no duplicate service-name/install test; the maintained full regression suite.
- **Risk:** **HIGH** until every deployed host confirms the old units are not
  enabled.
- **Rollback:** retain tagged legacy package/unit bundle; reinstall only with
  Product high-level units stopped and an explicit safety plan.
- **Prerequisites:** Groups 5–6 and a read-only deployed-unit audit.

### Group 8 — split Product ROS package by responsibility

- **Source:** `onboard_ros2_ws/src/sensor_visualization`.
- **Destination:** adapter-specific implementation under
  `platform/robot_adapters/lite3/`; Product-owned `bipolix_safety`,
  `bipolix_navigation`, and `bipolix_perception` packages remain within the
  colcon Product workspace. Keep compatibility executables/launch aliases
  during migration.
- **Reason:** the current package spans every Product layer and its name is
  misleading.
- **References requiring updates:** CMake/package manifests, every launch file,
  every systemd `ExecStart`, operator deploy scripts, tests, RViz package-share
  lookups and documentation. The external `/home/abx/emos-plugin-lite3` codec
  dependency must be packaged/configured, not silently copied.
- **Tests:** package builds and install-space execution; static owner checks;
  UDP single-owner tests; source/lease/watchdog tests; Nav2/localization/sensor
  tests; the maintained full regression suite; later staged live read-only acceptance.
- **Risk:** **HIGH**.
- **Rollback:** install versioned old workspace and units; stop all affected
  units, restore prior install prefix/unit set, daemon-reload, restart with
  `COMMAND_SOURCE=NONE`.
- **Prerequisites:** Groups 4–7, install-prefix abstraction, and a versioned
  deployment/rollback manifest.

### Group 9 — consolidate state estimation and legacy launch alternatives

- **Source:** overlapping localization launches and alternative telemetry
  bridges in both ROS packages.
- **Destination:** canonical Product navigation/state-estimation package;
  explicit R&D package for receive-only/ICP alternatives.
- **Reason:** prevent accidental duplicate UDP, `/odom`, `map→odom` or lifecycle
  ownership.
- **References requiring updates:** launch files, package dependencies, CMake,
  systemd, tests and docs.
- **Tests:** single publisher/receiver ownership, TF authority, lifecycle
  recovery, map/AMCL gate, full regression and later live read-only validation.
- **Risk:** **HIGH**.
- **Rollback:** retain prior launch/unit package and restore as one atomic set.
- **Prerequisites:** Group 8.

### Group 10 — move root Low-Level C++ tree under R&D

- **Source:** `main.cpp`, `interface/`, `state_machine/`, `types/`, `utils/`,
  low-level portions of `tools/` and root C++ tests.
- **Destination:** `rnd/low_level/`.
- **Reason:** make the Product/R&D separation physical after Product is already
  packaged independently.
- **References requiring updates:** root CMake include directories, globbing,
  relative includes such as `../tools/lite3_leg_kinematics.hpp`, tests, docs and
  deployment scripts.
- **Tests:** every C++ target/configuration (offline, MuJoCo and hardware-link
  compile only), the maintained full regression suite. No physical executable run as part of migration.
- **Risk:** **HIGH**.
- **Rollback:** revert atomic move/build commit; never deploy moved hardware
  binaries until separately approved.
- **Prerequisites:** Groups 3, 7–9.

### Group 11 — move ONNX policy subsystem

- **Source:** `policy/`, `run_policy/`, policy tests and policy-specific tools.
- **Destination:** `rnd/policies/{models,runtime,tests}`.
- **Reason:** isolate Physical-AI policy research from patrol vendor-gait path.
- **References requiring updates:** CMake, `LITE3_POLICY_MODEL`, model resolver,
  root/legacy service environment, transfer scripts and docs.
- **Tests:** model path and contract tests, zero/forward fixture tests, ONNX
  load-only test, full regression.
- **Risk:** **HIGH** due model/deployment coupling.
- **Rollback:** compatibility environment/path plus prior binary package.
- **Prerequisites:** Group 10.

### Group 12 — models and third-party dependency normalization

- **Source:** `Lite3_description/`, `third_party/` and broken/incomplete Gitlink
  metadata.
- **Destination:** keep `third_party/` stable; select one licensed Lite3 model
  authority under `rnd/mujoco/models` by reference/submodule/package rather than
  duplicating it.
- **Reason:** remove duplicated meshes and make dependency provenance/ABI
  reproducible.
- **References requiring updates:** simulators, sweep scripts, CMake library
  paths, `.gitmodules`, licenses and deployment manifest.
- **Tests:** clean-clone/submodule test, both x86/arm configure checks, MuJoCo
  model-load tests, full regression.
- **Risk:** **HIGH** because binaries, Gitlinks, licensing and model geometry are
  involved.
- **Rollback:** pin and restore exact dependency SHAs/binary hashes.
- **Prerequisites:** Groups 3, 10 and 11.

### Group 13 — artifact/evidence lifecycle

- **Source:** `artifacts/` and large `docs/handoff_evidence` payloads.
- **Destination:** curated `rnd/evidence/<session-id>` manifests; large raw data
  in an approved artifact store or Git LFS if selected.
- **Reason:** keep reproducible evidence without making generated campaigns look
  like maintained source.
- **References requiring updates:** experiment scripts, reports and handoff docs.
- **Tests:** manifest/hash verification and report regeneration smoke.
- **Risk:** **MEDIUM**; technical runtime risk is low, evidence-loss risk is high.
- **Rollback:** retain immutable archive/checksums and revert index changes.
- **Prerequisites:** evidence retention decision; Groups 1–3 recommended.

## Migration gates applying to every group

1. Record `git status --short --branch` and full SHA.
2. Prove which files are authoritative before moving duplicates.
3. Search CMake, Python, shell, systemd, launch, tests, docs and absolute paths.
4. Use `git mv`; do not copy-and-delete concurrent work.
5. Build only offline/static targets unless a later task explicitly authorizes
   deployment or physical validation.
6. Run focused tests, the maintained full suite (242 tests at this audit, and
   never fewer than the historical 223-test baseline) and
   `git diff --check`.
7. Confirm no generated/build/cache file was accidentally added.
8. Commit exactly one group with rollback notes.

## Recommended next migration group

**Group 4 — pure generic Product contracts** is complete. Group 4A added
in-place package metadata and Group 4B applied the approved Platform/Product
ownership. **Group 5A — operator test separation** is complete. Continue Group 5 by
classifying deployment, diagnostics, validation, and stable CLI consumers before
moving any installed or motion-capable operator path.
