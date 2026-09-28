# Repository audit — Phase A

Evidence date: 2026-09-28
Audited commit: `a8926266069e71f7b254c6465ac8e84a78b47303`
Post-audit repository state: Migration Group 1 completed at
`497743e04da11ca0a3cb1a19b2f0bbbcc6e56b06`; Group 2 is recorded by the
commit containing this updated audit; Group 3 is recorded by the commits
containing this revision.

This is a static repository audit. No file was moved, renamed or deleted, no
runtime was started, and no robot or Mini-PC was contacted. Classification is
based on build files, package manifests, imports/includes, launch files,
systemd units, tests, documentation, Git tracking state and hard-coded paths.
The later Group 1 migration moved only the two audited legacy MuJoCo logs; it
also used no Mini-PC or physical-robot access and changed no runtime or safety
behavior. The maintained Python regression baseline is `242 passed`.

## Executive findings

1. The physically proven patrol Product is primarily the ROS 2 source under
   `onboard_ros2_ws/src`, plus laptop-side `c2/`, `operator/` and
   `laptop_visualization/`. It does **not** use the root C++ `rl_deploy` tree as
   its normal locomotion runtime.
2. The root C++ build (`main.cpp`, `interface/`, `state_machine/`, `run_policy/`,
   `policy/`, most of `tools/`, `types/`, `utils/`) is the Low-Level / ONNX /
   Physical-AI R&D path. It remains safety-relevant because it can operate real
   hardware, but it is not the patrol Product command path.
3. `onboard_ros2_ws/src/sensor_visualization` has become a broad Product package
   containing robot adapter, safety, navigation, sensor, health and deployment
   code. Its name no longer describes its responsibility. Splitting it now
   would be high risk because its CMake install names and systemd paths are
   deployed contracts.
4. Root `scripts/` and `systemd/` overlap with files inside the ROS package.
   Same-named files are divergent, not harmless copies. The ROS-package copies
   are the current high-level Product source; the root copies are the older
   direct `Lite-robot/build/lite3_xbox_control` path and remain covered by C++
   tests.
5. The ROS workspace's `build/`, `install/` and `log/` trees, all root build
   trees, `__pycache__` and `.pytest_cache` are generated and untracked. In
   contrast, 404 experiment outputs under `artifacts/` and several editor-style
   backup files are tracked. The two tracked MuJoCo logs were subsequently
   archived by Migration Group 1 under `rnd/evidence/legacy/mujoco/`.
6. Deployment is path-sensitive. Product units currently mix
   `/home/abx/ros2_ws` and `/home/abx/Desktop/robotdog_ws`; laptop launchers use
   `/home/raz/ros-robot-cc/...`; legacy low-level units use
   `/home/abx/Lite-robot`; and the HIGH-LEVEL bridge loads an external codec
   from `/home/abx/emos-plugin-lite3`. These paths make many apparently simple
   moves high risk.
7. Product and R&D can be separated cleanly at the architectural boundary, but
   only incrementally. The current ROS workspace should remain intact until
   installed executable names, systemd units and deployment paths have package
   tests and an explicit rollback.

## Audit legend

- **Authority**: `authoritative`, `supporting`, `duplicate`, `legacy`, or
  `unknown` describes current repository/deployment ownership, not code quality.
- **Kind**: `source`, `generated`, `artifact`, `documentation`, `third-party`,
  or a combination.
- **Machine**: `Laptop`, `Mini-PC`, `Shared/offline`, or `N/A`.
- **Risk**: migration risk, not execution risk.

## Every top-level directory

| Path | Real responsibility and references | Layer / domain | Kind; authority | Machine | Safety/runtime impact | Move risk and recommendation |
|---|---|---|---|---|---|---|
| `.git/` | Git object database, refs and worktree metadata; consumed only by Git | Repository infrastructure | generated metadata; authoritative for history | N/A | No runtime impact; destructive changes lose history | **HIGH**; remain exactly where it is |
| `.marscode/` | Local editor state; Group 2 removed its tracked host identifier and added a narrow ignore rule | Developer tooling | generated local metadata; non-authoritative | Laptop | None | **LOW**; remain ignored and untracked |
| `.pytest_cache/` | Pytest cache; ignored and untracked | Testing cache | generated | Laptop/offline | None | **LOW**; remain ignored, delete locally only as housekeeping |
| `__pycache__/` | Python bytecode; ignored and untracked | Runtime/test cache | generated | Shared | None | **LOW**; remain ignored |
| `artifacts/` | Outputs of leg-lift, body-shift, sensitivity and robustness experiments. Producers include root sweep scripts and `tools/*sweep*` | R&D / evidence | generated experiment artifact; partially retained evidence | Offline R&D | No Product runtime; evidence may matter to research decisions | **MEDIUM**; do not mass-move. 404 files are tracked (`grid_162` 325, `single_leg_sensitivity` 43, `single_leg_sweep` 36); other 2,694+ files are ignored. Define evidence retention first |
| `build/` | Default CMake outputs for low-level executables/tests | R&D build | generated, ignored, untracked | Offline/Mini-PC development | Binaries can command hardware if run; not deployment authority | **LOW** as cache, but never treat it as source; rebuild rather than migrate |
| `build-low-level/` | One low-level simulation/test binary in current checkout | R&D build | generated, ignored, untracked | Offline | No Product runtime | **LOW**; rebuild rather than migrate |
| `build-mujoco/` | CMake MuJoCo outputs and tests | R&D build | generated, ignored, untracked | Offline | Simulation only unless a hardware binary is separately invoked | **LOW**; rebuild rather than migrate |
| `build-offline/` | Main offline CMake/test output tree | R&D/testing build | generated, ignored, untracked | Offline | Test binaries include safety fixtures; not deployed source | **LOW**; rebuild rather than migrate |
| `build-robust-fr/` | Robust front-right leg simulation build | R&D build | generated, ignored, untracked | Offline | None on Product | **LOW**; rebuild rather than migrate |
| `c2/` | Laptop Xbox discovery/validation, robot selection, control/release CLI, ROS C2 publisher, registry and user units; referenced by its tests, docs and installed wrappers | Product / Operator-C2 | source/config; current laptop authority, with deployment-path debt | Laptop | Manual ownership and safe release are safety-critical | **HIGH**; keep until wrappers and user units stop referring to `/home/raz/ros-robot-cc/c2` |
| `platform/` | Vendor-neutral robot contracts, robot-specific adapters and target robot configuration; imported only by architecture tests | Platform contracts/adapters/config | source/config; authoritative architectural baseline, not deployed runtime | Shared/offline | No sockets, nodes or commands; future safety boundary | **MEDIUM**; preserve Platform ownership and migrate consumers deliberately |
| `product/` | Robot-agnostic mission contracts; imported only by architecture tests and intentionally dormant | Product missions | source; authoritative contract baseline, not deployed runtime | Shared/offline | No runtime effect; must not bypass generic Robot Interface | **LOW/MEDIUM**; preserve public imports and dormant status |
| `docs/` | Architecture, operations, requirements, tests, experiment reports and committed handoff evidence | Documentation/evidence | documentation and captured artifacts; authoritative by document scope | Shared | Architecture/safety procedures are operationally important | **MEDIUM**; keep top-level. Large evidence needs a retention policy, not blind relocation |
| `interface/` | C++ Low-Level robot/user-command abstractions, MotionSDK hardware transport, permits/lease, Xbox input and simulation adapters. Built by root CMake as static `interface` library | R&D / Low-Level Control; some reusable safety concepts | source; authoritative for root C++ path | Offline and legacy Mini-PC hardware path | **Very high**: direct ownership, joint commands and vendor SDK | **HIGH**; do not move until root CMake and all C++ includes are made target-scoped and low-level deployment is isolated |
| `laptop_visualization/` | Canonical laptop RViz session/watcher scripts, robot marker and RViz config; user service executes absolute path | Product / Operator visualization | source/config; current laptop authority | Laptop | Read-only visualization, but wrong config can mislead operator | **HIGH** due installed service and absolute paths; keep until package-relative install/wrapper exists |
| `Lite3_description/` | 2,185 STL meshes plus 3 MJCF XML files. Only code reference is legacy `interface/robot/simulation/mujoco_simulation.py` | R&D / MuJoCo model | vendor/model asset; supporting, likely redundant with `third_party/deep_robotics_model` | Offline | No current Product runtime | **MEDIUM**; candidate for later model consolidation after geometry/hash/license validation |
| `onboard_ros2_ws/` | Colcon workspace. `src/sensor_visualization` contains the current HIGH-LEVEL bridge, sensors, safety sources, localization, Nav2, health, units and tools. `src/lite3_state_estimation` owns odometry/localization helpers. Nested `build/install/log` are generated | Product runtime plus some development/R&D utilities | mixed source/generated; **authoritative Product source is `src/` only** | Mini-PC; configs observed by Laptop | Highest Product impact: UDP 43897 owner, commands, odom, TF, scan, localization and Nav2 | **HIGH**; preserve workspace and package executable names for now |
| `operator/` | Laptop CLIs, deployment/install scripts, Day-2 planning/execution tools, reliability tools and unit templates | Product Operator/Deployment plus engineering validation | source; mixed authoritative operator wrappers and one-off deployment/validation tooling | Laptop, installing to Mini-PC | Several commands can acquire ownership or trigger motion after approval | **HIGH**; first inventory into stable CLI vs deployment vs experiment; installed wrapper paths must be preserved |
| `policy/` | `policy.onnx` and PyTorch-to-ONNX converter | R&D / Policies | binary model + source converter; authoritative for root ONNX runner | Offline/legacy low-level Mini-PC | Model can produce joint-level policy output through R&D runtime | **HIGH**; keep with `run_policy` until model manifest and deploy path replace `LITE3_POLICY_MODEL` assumptions |
| `run_policy/` | ONNX policy loader, model resolver and policy interface; root CMake static library | R&D / Policies and Low-Level Control | source; authoritative for root RL/ONNX path | Offline/legacy hardware path | Joint-policy safety impact | **HIGH**; move only with root CMake, model and state-machine boundary together |
| `rnd/` | Curated R&D hierarchy containing legacy evidence plus the Group-3 MuJoCo experiment entry points under `mujoco/experiments/` | R&D / MuJoCo / evidence | source plus artifact archive; authoritative for migrated experiments | Offline R&D | Simulation-only entry points; no Product runtime or safety impact | **LOW/MEDIUM**; continue only through reviewed dependency-safe migrations |
| `scripts/` | Legacy direct local-Xbox connection/lease/readiness scripts plus file-transfer and sweep launchers. Root C++ test and root units reference them | Mixed: legacy low-level runtime, R&D deployment/experiments | source; legacy/divergent relative to ROS-package scripts | Mini-PC legacy path and Laptop | Xbox/ownership scripts are safety-critical if installed | **HIGH** for control scripts; **LOW/MEDIUM** for transfer/sweep scripts. Do not merge same-named files by assumption |
| `state_machine/` | C++ Idle/Stand/JointDamping/RL states, local Xbox state machine, low-level supported body/leg plans and control parameters; globbed into root executables | R&D / Low-Level Control | source; authoritative for root C++ runtime | Offline and legacy real-hardware validation | Direct robot-state/joint-command safety impact | **HIGH**; remain exactly where it is during Product/R&D split |
| `systemd/` | Older direct local-Xbox services using `/home/abx/Lite-robot/build/lite3_xbox_control`; tested by `tests/xbox_startup_service_test.sh` | Legacy Low-Level deployment | source/config; legacy, not canonical high-level Product units | Mini-PC legacy path | Can start hardware-facing C++ runtime | **HIGH**; do not delete/move until confirmed absent from every deployed host and tests are retired/replaced |
| `tests/` | Root C++ low-level tests, fake SDK, Xbox service tests and `tests/architecture` Product contract tests | Mixed R&D safety tests and Product architecture tests | source/tests; authoritative verification | Offline | Protects permits, ownership, watchdogs and contracts | **MEDIUM/HIGH**; split only after build/test discovery is updated with no loss of coverage |
| `third_party/` | Vendored Eigen, MotionSDK, MuJoCo and ONNX Runtime; Gamepad source; robot model Gitlink. Root CMake links these directly. Includes binary `.so` files | Vendor / third-party | third-party source/binary/Gitlinks; authoritative dependencies for R&D | Shared builds | MotionSDK and runtimes are ABI-critical | **HIGH**; remain exactly where it is. Git metadata is inconsistent: Gitlinks exist for `Lite3_MotionSDK/URDF` and `gamepad/example/fmt`, but `.gitmodules` declares only `deep_robotics_model` |
| `tools/` | Mostly low-level validators, simulations, kinematics, body/leg sweep tooling and robustness pipeline; root CMake builds several. Includes hardware-facing validation console and Xbox executable | R&D / Low-Level Control and engineering tools | source; historical backup snapshots moved to curated evidence by Group 2 | Offline and explicit legacy hardware validation | Some tools can command hardware; others are pure analysis/simulation | **HIGH** as a whole. Split hardware tools from offline tools only after target-by-target CMake changes |
| `types/` | Legacy C++ robot/action/user-command/feedback structs used across `interface`, `state_machine`, `run_policy`, tests and utils | R&D / Low-Level shared types | source; authoritative for root C++ path | Shared low-level build | Broad compile-time dependency; includes Eigen and OS timing | **HIGH**; remain until namespaces/includes are refactored in a dedicated low-level phase |
| `utils/` | Legacy C++ math, JSON and UDP/file streaming helpers; URDF-to-MJCF conversion script | R&D shared utilities | source; authoritative/supporting for root C++ path | Offline/legacy hardware | `data_streaming.hpp` has network/file behavior; `basic_function` feeds policy | **HIGH** for C++ helpers, **LOW** for conversion script if isolated; do not move wholesale |

## Every root-level file

| File | Actual use and references | Classification | Risk / disposition |
|---|---|---|---|
| `.gitignore` | Excludes build trees, caches and selected experiment outputs; does not exclude already tracked artifacts/backups | Repository configuration; authoritative | **MEDIUM**; keep. Extend only in a separate hygiene change after deciding artifact policy |
| `.gitmodules` | Declares only `third_party/deep_robotics_model`, while the index contains two additional Gitlinks | Third-party metadata; incomplete/fragmented | **MEDIUM**; keep, repair metadata before any dependency relocation |
| `AGENTS.md` | Repository-wide Git, robot safety, validation and architecture instructions | Documentation/policy; authoritative | **HIGH**; remain at repository root |
| `CMakeLists.txt` | Builds the root low-level/RL runtime, interface library, validation tools, simulations and C++ tests; directly names root paths and third-party ABI assets | R&D build source; authoritative | **HIGH**; remain until Low-Level tree migration is deliberately staged |
| `LICENSE` | Repository Apache-2.0 license text | Legal documentation; authoritative | **HIGH** legal significance; remain at root |
| `PROGRESS.md` | Historical/current project progress with host paths | Documentation; supporting and partly historical | **LOW** to reorganize later; keep while links/handoff use it |
| `README.md`, `README_EN.md` | Root low-level RL controller build/use documentation, not a complete description of the current patrol Product | Documentation; authoritative for legacy/R&D build, incomplete for platform | **MEDIUM**; retain and eventually label/move under R&D while adding a platform root README |
| `fix_policy_path.py` | One-off symlink repair from repository model to parent `policy/`; referenced only by a handoff document | R&D deployment helper; legacy/obsolete candidate | **LOW**; archive after policy deployment is manifest-based; do not run during Product setup |
| `main.cpp` | Root `rl_deploy` entry point; constructs C++ `StateMachine(RobotType::Lite3)` | R&D Low-Level runtime source | **HIGH**; remain with state machine and CMake |
| `pytest.ini` | Limits default Python discovery to `test_*.py` | Test configuration; authoritative | **MEDIUM**; remain at root while tests span multiple trees |

## Current Product runtime (Patrol / high-level)

These are the exact repository areas that implement or support the current
patrol Product. “Product” does not mean every file is currently enabled.

### Mini-PC authoritative runtime

- `onboard_ros2_ws/src/sensor_visualization/scripts/xbox_lite3_motion_host_bridge.py`
  and `launch/lite3_high_level_runtime.launch.py`: persistent HIGH-LEVEL
  transport, heartbeat, telemetry, `/odom`, `odom→base_link`, protected command
  inputs and the sole production UDP `43897` receiver.
- `scripts/lite3_high_level_runtime.sh` and
  `systemd/lite3-high-level-runtime.{service,default}`: installed runtime entry.
- `launch/lite3_lidar_bringup.launch.py`, URDF sensor mount files and
  `systemd/lite3-lidar.service`: `/scan` and `base_link→lidar_link`.
- `onboard_ros2_ws/src/lite3_state_estimation/`: odometry helpers,
  localization guard, AMCL/map launch and tests. Its
  `high_level_state_bridge.py` is an alternative receive-only bridge and is
  **not** allowed beside the production UDP owner.
- Localization Product path:
  `lite3_localization_{start,supervisor}.sh`,
  `lite3_localization_lifecycle_ready.py`, `lite3_ros_inputs_ready.py`,
  `lite3_localization_gate.py`, `lite3_map_manager.py`, AMCL configuration,
  `lite3-localization.service` and `lite3-mapping.service`.
- Navigation Product path: `nav2_day2.launch.py`, `nav2_day2.yaml`,
  `navigate_to_pose_day2.xml`, `plan_from_rviz_goal.py`,
  `lite3_nav2_preflight.py`, `lite3_nav2_safety_monitor.py`, and the Nav2 units.
- Safety/ownership Product path:
  `lite3_autonomy_command_source.py`, `lite3_laptop_xbox_source.py`,
  `lite3_posture_guard.py`, `lite3_release_autonomy.sh`,
  `lite3_nav_test_override.py`, relocalization scripts and their units.
- Health/deployment Product path: `lite3_system_health.sh`,
  `lite3_high_level_ros_watchdog.py`, network/readiness/headless scripts and
  systemd units.
- Optional Product perception: D455 service, D455 probe and RViz profiles.
  It is on-demand and not required by the current LiDAR Nav2 MVP.
- Dormant Product scaffold: `lite3_mission_manager.py` and
  `config/named_locations.yaml`; not yet a Day-3 production mission runtime.

### Laptop authoritative/supporting Product

- `c2/`: registry, joystick validation, C2 relay and safe ownership CLIs.
- `operator/lite3_{robot,map,relocalize,nav}_cli.py`, command registry and
  obstacle-test implementation; deployment/install scripts are supporting
  operations rather than onboard runtime.
- `laptop_visualization/`: canonical operator RViz config, marker and watcher.
- `platform/robot_interfaces`, `platform/robot_adapters/lite3` and `product/missions`: pure
  architecture contracts/scaffolds; currently exercised only by offline tests.
  Each component now has independent packaging metadata; no deployed
  runtime consumes these packages.
- `platform/config/robots/lite3`: target generic configuration; not yet the values read
  by the deployed Nav2/HIGH-LEVEL processes.
- `product/operator/diagnostics`: uninstalled, read-only localization and host
  reliability collection tools; no deployed consumer.
- `product/operator/validation`: uninstalled planning-only Nav2 preview tools;
  no motion action, command-source, or hardware-control path.

### Product package files that are development/legacy candidates

The broad ROS package also installs old or explicit-development paths:
`lite3_cmd_vel_adapter.py`, `lite3_cmd_vel_arbiter.py`,
`lite3_manual_axis_control.py`, keyboard/vendor-gait launch files, calibration
launches, packet inspection, ICP experiments, `lite3_telemetry_bridge.cpp`, and
several unreferenced visualization/localization launches. They are not the
canonical patrol owner and must not be launched alongside an authoritative
owner without an explicit test plan.

## Low-Level / MuJoCo / ONNX / Physical-AI R&D

The R&D boundary is:

- root `CMakeLists.txt` and `main.cpp`;
- `interface/`, `state_machine/`, `types/`, `utils/`;
- `policy/` and `run_policy/`;
- most of `tools/`, especially body-shift, leg-lift, kinematics, MuJoCo and
  robustness code;
- `rnd/mujoco/experiments/{grid_162.py,sensitivity_test.py,single_leg_sweep.py}`
  and their artifacts;
- `Lite3_description/`, `third_party/mujoco`,
  `third_party/onnxruntime`, `third_party/deep_robotics_model` and relevant
  portions of MotionSDK/Eigen;
- root C++ tests except `tests/architecture` and the high-level service static
  tests;
- generated `build*` directories and tracked/untracked simulation evidence.

The R&D validation console, local Xbox executable and `HardwareInterface` can
reach real hardware. “R&D” therefore means separate product responsibility, not
lower safety importance.

## Generated, cache and artifact status

| Area | Generated? | Git status at audit | Required action |
|---|---:|---|---|
| `build/`, `build-low-level/`, `build-mujoco/`, `build-offline/`, `build-robust-fr/` | Yes | ignored/untracked | Keep out of Git; reproduce from CMake |
| `onboard_ros2_ws/build`, `install`, `log` | Yes | ignored/untracked | Keep out of Git; only `src` is authoritative |
| `__pycache__`, nested `__pycache__`, `.pytest_cache` | Yes | ignored/untracked | Keep ignored |
| `artifacts/grid_162`, `single_leg_sensitivity`, `single_leg_sweep` | Yes, retained evidence | 404 files tracked | Decide evidence policy/LFS/archive before changing |
| other `artifacts/*` campaigns | Yes | ignored/untracked | Keep out of Git unless curated evidence is promoted |
| `rnd/evidence/legacy/mujoco/{root,interface-simulation}-MUJOCO_LOG.TXT` | Yes, retained legacy evidence | tracked; moved by Migration Group 1 with content hashes preserved | Keep as curated R&D evidence; no runtime/build consumers |
| `docs/handoff_evidence/source_snapshots/group2-legacy-backups/` | Curated historical source snapshots | tracked; unique snapshots archived by Group 2 | Retain with provenance manifest; exact duplicates remain recoverable from Git history |
| `.marscode/` | Host/editor state | ignored/untracked after Group 2 | Keep local host metadata out of Git |
| `Lite3_description` meshes | Vendor/model assets, not generated by this build | tracked | Treat as third-party model data; do not delete as cache |

## Concrete duplication and fragmentation

1. **Two Robot Interface concepts**:
   `interface/robot/robot_interface.h` is a joint-level C++ R&D hardware API;
   `platform/robot_interfaces/bipolix_robot_interfaces` is a vendor-neutral Platform
   contract. Their names overlap but their abstraction level does not. They
   should be renamed/separated eventually, not merged mechanically.
2. **Types split**: root `types/` contains legacy Eigen/joint/control structs;
   generic Product types are dataclasses/enums in
   `platform/robot_interfaces/.../contracts.py`; ROS messages are used directly in
   `sensor_visualization`. This is three representation layers with no formal
   translation package yet.
3. **Arbitration split**: C++ `CommandSourceLease`, Python source-specific file
   locks/state files, older `lite3_cmd_vel_arbiter.py`, and C2 lease logic express
   related concepts. The deployed Product authority is the `/run/lite3-control`
   lease plus protected source adapters; the standalone Python cmd-vel arbiter
   belongs to an older launch path.
4. **Duplicate Xbox/readiness names**: root and ROS-package copies of
   `lite3_xbox_device_valid.sh`, `lite3_xbox_diagnose.sh`,
   `lite3_readiness_status.sh` and `lite3-xbox.service` differ in behavior and
   deployment root. Root files serve the old direct C++ path; ROS-package files
   serve the current persistent HIGH-LEVEL architecture.
5. **Visualization split**: laptop canonical RViz/watcher lives in
   `laptop_visualization`; the ROS package also installs multiple RViz files and
   launch files that can start RViz. Onboard Product services correctly use
   `use_rviz:=false`, but the sources remain fragmented.
6. **Localization launch overlap**: `lite3_state_estimation` has the current
   map/AMCL guard launch; `sensor_visualization` also contains
   `saved_map.launch.py`, `stationary_localization.launch.py` and
   `lidar_map_visualization.launch.py`. The latter are unreferenced development
   candidates and could create competing lifecycle/TF owners.
7. **Model duplication**: `Lite3_description` and
   `third_party/deep_robotics_model/Lite3/Lite3_mjcf` both contain Lite3 MJCF
   assets. Only the former is referenced by one legacy Python simulator; the
   sweep tools use the latter.
8. **Backup clones**: several `tools/*before*` files are byte-identical to other
   source files. They are not independent implementations.
9. **Operator mixing**: `operator/` combines stable user CLIs, install scripts,
   reliability diagnostics, one-shot physical test executors and captured-test
   analysis. That makes ownership and deployment review harder.
10. **Broad ROS package**: `sensor_visualization` owns far more than sensors or
    visualization. Splitting by Product layer is justified, but is a later
    high-risk migration because installed executable names are contractual.

## Hard-coded path dependencies

### Laptop

- `/home/raz/ros-robot-cc/c2/...` in the C2 user service.
- `/home/raz/ros-robot-cc/laptop_visualization/...` in RViz scripts/service.
- Several operator installers derive or copy to fixed laptop locations.
- Migrated experiment entry points under `rnd/mujoco/experiments/` now
  discover the repository root from repository markers, independent of the user
  home directory and the process working directory.

### Mini-PC

- `/home/abx/ros2_ws`: source/install working directory used by HIGH-LEVEL,
  LiDAR, health, Xbox, RealSense and parts of AUTONOMY.
- `/home/abx/Desktop/robotdog_ws`: installed executables used by localization,
  Nav2 gates/safety, relocalization and some deployment scripts.
- `/home/abx/Lite-robot`: legacy root C++ Xbox runtime and ONNX policy.
- `/home/abx/emos-plugin-lite3`: external Motion Host protocol/codec dependency
  used by the production bridge and some probes.
- `/home/abx/.config/lite3`, `/home/abx/.local/state/lite3-maps`: intentional
  host state but should become documented configurable data roots.

### Intentional absolute runtime locations

- `/run/lite3-control` is volatile ownership/readiness state and should remain a
  single explicit runtime contract, preferably exposed through one shared
  library/config constant.
- `/opt/ros/jazzy/setup.bash` is an installation prerequisite, not a repository
  path; deployment should validate it.

Migration should first introduce environment/config/package-prefix resolution,
then change one consumer group. Replacing strings globally would break the
currently deployed split workspaces.

## Dangerous moves / remain exactly where they are for now

- `onboard_ros2_ws/src` packages, package names, installed executable names and
  systemd unit source paths.
- `xbox_lite3_motion_host_bridge.py`, the sole UDP `43897` production ownership
  path, and its external codec dependency.
- `lite3_state_estimation` ownership of odometry/localization helpers and the
  authoritative TF chain.
- current Nav2, AMCL, map and LiDAR configuration/extrinsics.
- `c2/`, `operator/` and `laptop_visualization/` files referenced by installed
  wrappers/user services.
- root `interface/`, `state_machine/`, `run_policy/`, `policy/`, `types/` and
  `utils/`, because root CMake uses directory-wide include paths and globs.
- `third_party/` binary/runtime dependencies and Gitlinks.
- tracked experimental evidence until retention and provenance are recorded.

## Group-2 disposition and remaining obsolete candidates

- curated first-party historical snapshots under `docs/handoff_evidence/source_snapshots/group2-legacy-backups/`; exact duplicates were removed by Group 2 and remain recoverable from Git history;
- archived/generated MuJoCo logs under `rnd/evidence/legacy/mujoco/` (retain as
  curated legacy evidence unless a later retention policy says otherwise);
- `.marscode/` local editor metadata is now ignored and untracked;
- `fix_policy_path.py` after policy packaging is fixed;
- unreferenced legacy ROS launch/config files after installed-host audit;
- old root Xbox systemd/scripts after confirming no deployed machine uses the
  direct `lite3_xbox_control` service;
- duplicate Lite3 model tree after geometry/license/reference validation;
- `interface/test.cpp`, whose includes refer to absent/old Raisim headers and
  which is not built by current CMake.

## Answers to the required architecture questions

1. **Patrol/Product:** current high-level ROS workspace runtime, laptop C2,
   operator tooling, visualization and pure platform contracts listed above.
2. **R&D:** root C++ MotionSDK/state-machine/ONNX path, MuJoCo/models/sweeps and
   associated tests/artifacts.
3. **Overlaps:** robot interface/type representations, command arbitration,
   Xbox/readiness scripts, RViz, localization launches, model assets and mixed
   operator/tools directories.
4. **Generic-interface fragmentation:** legacy joint-level C++ `interface/` +
   legacy C++ `types/` + generic Python `platform/robot_interfaces` + ROS-native
   messages. They require adapters, not a wholesale merge.
5. **Generated files:** build/install/log/cache trees are correctly untracked;
   experiment artifacts still need an evidence-lifecycle policy; legacy logs and
   unique manual snapshots are now curated under explicit evidence paths.
6. **Dangerous exact paths:** deployed ROS package/unit paths, laptop user units,
   legacy `/home/abx/Lite-robot` services, external codec root, and vendor ABI
   paths.
7. **Absolute home paths:** catalogued above; replace gradually with environment,
   package-share lookup, systemd `EnvironmentFile`, and install-prefix discovery.
8. **Obsolete candidates:** Group 2 removed only verified local metadata and exact-content duplicates, while archiving unique snapshots; all uncertain candidates remain untouched.
9. **ROS workspace:** keep it intact now. Split packages only after compatibility
   wrappers and installed-unit tests exist.
10. **Clean separation feasibility:** yes. The runtime boundary is already
    conceptually clean: Product uses vendor gait through the persistent
    HIGH-LEVEL adapter; R&D owns joint-level MotionSDK/ONNX/MuJoCo. Physical tree
    cleanup can proceed without changing behavior if migration is incremental.
