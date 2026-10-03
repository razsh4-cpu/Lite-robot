# Lite3 navigation backend restoration baseline

Status: offline preparation only

Prepared from Git: `0bc597ab8b343e10620c19a2ef4e25a329d31f31`

Known-good product import: `abf99009ef4b48d66ca0ce8626d0f1c076eb051c`

Physical acceptance record: `1462847bb113ec5db0e4b9a8b38b538044fba9bd`

This plan restores the existing product chain; it does not introduce another
navigation stack, command arbiter, odometry owner, TF owner, or robot transport.
It is intentionally independent of NOMAD/SABLE and of the in-progress
independent-Xbox backend branch.

```text
RPLIDAR /scan + HIGH-LEVEL /odom + saved map
  -> Map Server + AMCL + localization guard
  -> map -> odom -> base_link -> lidar_link
  -> Nav2 planner/controller/BT Navigator + costmaps
  -> /cmd_vel -> AUTONOMY -> arbiter -> HIGH-LEVEL -> Lite3
```

No service was started, no deployment was performed, and no robot command was
sent while preparing this baseline.

## Evidence boundary

The strongest physical baseline is `LITE3_HIGH_LEVEL_NAV2_DAY2_2026-09-27`:

- `TEST-20260927-003`: `Home_Map`, scan alignment, AMCL and the complete TF
  chain passed the `>=80%` for three consecutive samples gate;
- `TEST-20260927-002`: a real chair was detected by LiDAR/costmaps, Nav2 chose
  a right-side path of about 1.47 m, `NavigateToPose` returned `SUCCEEDED`
  (`error_code=0`), localization ended near 95.4%, the robot stopped, AUTONOMY
  released, and `COMMAND_SOURCE=NONE`;
- the exact installed package hashes at the instant of that physical run were
  not captured. `abf9900` is therefore the strongest source baseline, not a
  cryptographic deployment attestation.

Later software commits extend this baseline without replacing it:

- `7ae1688`: guarded obstacle CLI, full candidate planning, bounded diagnostic
  snapshots, map identity, path-tangent footprint checks, and independent
  localization-policy consumption;
- `b98a1af`: reconciled localization guard source and the fail-closed 180-second
  test-override lifetime;
- `4a95852`: obstacle helper import/install regression protection;
- `0bc597a`: reconstructed evidence and current limitations.

## Known-good assets

| Concern | Authoritative source | Last functional commit | Reuse decision |
|---|---|---:|---|
| RViz operator view | `laptop_visualization/lite3_remote_lidar.rviz` plus `lite3_nav2_rviz*.sh`, marker and watcher | `abf9900` | Reuse visualization content; repair host-absolute launch paths before independent-backend installation |
| AMCL | `onboard_ros2_ws/src/lite3_state_estimation/config/amcl.yaml` | `abf9900` | Reuse unchanged initially |
| Map Server + AMCL launch | `onboard_ros2_ws/src/lite3_state_estimation/launch/day1_localization.launch.py` | `abf9900` | Reuse; selected map must be injected by map manager/start script |
| Localization gate | `lite3_state_estimation/localization_guard.py` | `b98a1af` | Reuse current source: saved pose is hypothesis, bounded global fallback, `>=80%` x3 |
| Deterministic lifecycle recovery | `lite3_localization_{start,supervisor}.sh`, `lite3_localization_lifecycle_ready.py` | `abf9900` | Reuse behavior; consolidate mixed deployed workspace paths before installation |
| Odometry | persistent `xbox_lite3_motion_host_bridge.py` within the HIGH-LEVEL runtime | `abf9900` | Preserve as sole UDP 43897, `/odom`, and `odom->base_link` owner |
| LiDAR + static TF | `lite3_lidar_bringup.launch.py`, `lite3-lidar.service` | `abf9900` | Reuse current serial-by-id and z=0.08/yaw=pi provenance; do not claim metrology completion |
| Nav2 | `nav2_day2.yaml`, `navigate_to_pose_day2.xml`, `nav2_day2.launch.py` | `abf9900` | Reuse planner/costmap/limits; validate installed controller binary on target CPU before motion |
| Nav2 safety/readiness | `lite3_nav2_preflight.py`, `lite3_nav2_safety_monitor.py`, `lite3_autonomy_command_source.py` | `7ae1688` | Reuse current fail-closed source |
| Obstacle workflow | `operator/lite3_nav_{cli,obstacle_core,obstacle_execute}.py`, chair snapshot/analyzer, plan publisher | `7ae1688` | Reuse algorithm and evidence capture; expose through backend API later, not through NOMAD/SABLE |

The key current file contents for AMCL, Nav2, LiDAR, RViz and the launch files
remain identical to their `abf9900` blobs. The localization guard and guarded
obstacle/preflight layers are deliberately newer as listed above.

## Configuration to preserve

- body: approximately 0.610 x 0.370 m;
- Nav2 polygon: 0.710 x 0.470 m (`+/-0.355`, `+/-0.235`);
- `footprint_padding=0.0`;
- `inflation_radius=0.30 m`, `cost_scaling_factor=4.0`;
- obstacle source: `/scan`, marking and clearing enabled;
- planner: NavFn with A* and unknown space rejected;
- controller in the recorded product YAML: DWB, with maximum
  `vx=0.10 m/s`, `|vy|=0.05 m/s`, `|wz|=0.20 rad/s`;
- AUTONOMY stale-command watchdog: 300 ms;
- normal localization acceptance: scan-to-map match fraction `>=0.80` for
  three consecutive measurements;
- TF ownership: AMCL owns `map->odom`, persistent HIGH-LEVEL owns
  `odom->base_link`, LiDAR bringup owns static `base_link->lidar_link`;
- RViz: grayscale `/map`, red `/scan`, blue body/heading/footprint, green
  preview path, orange active Nav2 path, costmap overlays hidden only in RViz.

The custom localization score is not an AMCL probability. Map identity, TF,
covariance and scan alignment remain separate readiness evidence.

## `Home_Map` artifact status

`Home_Map` is site data, not repository code. The retained read-only Mini-PC
audit records both of these historical locations:

- `/home/abx/ros2_ws/maps/Home_Map/map.yaml`
- `/home/abx/Desktop/robotdog_ws/src/maps/Home_Map/map.yaml`

Both metadata captures report `map.pgm`, resolution `0.05`, origin
`[-4.155, -3.19, 0]`, occupied threshold `0.65`, free threshold `0.196`, and
`negate=0`. The PGM bytes, their hash, `initial_pose.json`, and
`metadata.json` were not retained in Git/evidence. Therefore the map cannot be
reconstructed or declared identical offline. The next safe live preparation
must copy the complete selected map directory read-only, hash all four site
artifacts, and verify that the active-map pointer names that exact YAML. It must
not regenerate or overwrite the map.

## Differences and repair list

1. **Independent Xbox branch unavailable to this audit.** At preparation time
   no `backend/lite3-independent-xbox` ref/worktree was visible in this Git
   repository. This branch was neither created nor touched. Rebase/cherry-pick
   of this documentation should happen only after that branch has a committed
   checkpoint; re-run the ownership diff then.
2. **Mixed deployment roots.** Localization/Nav2 units and scripts mix
   `/home/abx/ros2_ws` with `/home/abx/Desktop/robotdog_ws`. Preserve behavior
   for now, but the independent backend needs one versioned install root and
   environment file before deployment.
3. **RViz host paths.** The canonical scripts point at
   `/home/raz/ros-robot-cc/laptop_visualization`, while the Git checkout is
   `Lite-robot/laptop_visualization`. Replace these with an installed/package
   path or explicit backend configuration; do not maintain a second RViz copy.
4. **Map/site data absent from Git.** Restore and hash `Home_Map` as site data;
   never substitute the similarly shaped `site_full_20260925` by name or
   metadata alone.
5. **CPU/controller evidence split.** The physically accepted product YAML is
   DWB. Separate SABLE evidence reports an MPPI SIGILL and an RPP fallback on
   the AVX-less J6413, but that is a different stack and has no product
   physical acceptance. Do not copy SABLE code. Before starting Nav2, verify
   that the configured product controller plugin is installed and executable
   on the Mini-PC; change controller only through a focused no-motion plan and
   later physical acceptance.
6. **Calibration evidence limit.** z=0.08/yaw=pi is the current LiDAR source of
   truth and supported the recorded run, but its metrology record is incomplete.
   Preserve it; do not retune it to improve confidence.
7. **Current root copies.** The unversioned laptop ROS copies match Git for the
   core Nav2, AMCL, LiDAR and RViz assets. Their older preflight/safety-monitor
   copies lack the `7ae1688` map/lifecycle/override protections and must not
   replace the Git versions.

## Shortest restoration sequence

1. Finish and commit the independent Xbox backend, then compare only its
   HIGH-LEVEL/odom/TF/ownership seams with this baseline. Preserve one UDP 43897
   receiver and one `odom->base_link` publisher.
2. Retrieve the complete `Home_Map` directory read-only, hash it, and register
   it as versioned site data with its existing pose/metadata unchanged.
3. Make package/install paths configurable without changing node/topic/frame
   semantics. Install the existing ROS packages into one clean Jazzy workspace.
4. Run offline/static tests, then a live **no-motion** readiness sequence:
   `/scan`, `/odom`, TF owners, map identity, lifecycle-active Map Server and
   AMCL, `>=80%` x3, and one RViz instance.
5. In RViz verify grayscale map, red scan alignment, blue body/heading and
   footprint. Keep AUTONOMY stopped and `COMMAND_SOURCE=NONE`.
6. Start Nav2 without AUTONOMY and request only a preview path. Confirm planner,
   controller, BT Navigator, both costmaps, real LiDAR obstacles, full padded
   footprint and a collision-free short path.
7. Only after a separately approved physical plan, restore the proven
   `/cmd_vel -> AUTONOMY -> arbiter -> HIGH-LEVEL` path and repeat the smallest
   bounded navigation acceptance. Physical motion is outside this preparation.

## Offline verification at preparation time

The focused navigation/localization/map workflow suite passed 73 tests from
the isolated worktree. This proves source/static behavior only. It does not
prove the map artifact, installed ROS plugins, DDS graph, calibration, physical
clearance, or current robot readiness.

# Current preparation checkpoint — 2026-10-03

The independent offline backend is prepared in `backend/lite3/`; its README
defines the external site/map identity, saved goals, patrol/alert lifecycle and
manual-takeover contracts. Historical Home_Map recovery is optional, not a
backend prerequisite. No concrete live navigation transport is activated.

Localization scripts accept `LITE3_WORKSPACE`; RViz launch/session/watcher use
sibling paths and optional `LITE3_RVIZ_CONFIG`. Legacy workspace defaults and
localization threshold remain unchanged. No deployment units were modified.

Focused validation: 78 tests passed (new orchestration, external-site binding,
relocated environment, mission registry/contracts, localization supervisor/guard,
obstacle CLI and map workflow). The larger targeted collection yielded 97 passes
and 7 import failures, all missing `rclpy`; the separate existing AUTONOMY test
also cannot collect without `rclpy`. These are NOT reported as tested safety
runtime behavior. Shell syntax and `git diff --check` passed.
An additional static-only Nav2 run passed 20 tests with 8 ROS-dependent tests
explicitly deselected; these exclusions are not runtime safety validation.
Engineering knowledge validation in this isolated worktree encounters existing
external/sibling evidence links that do not resolve under `.worktrees`; no
historical evidence or link ownership was changed.

No SSH inspection completed, no deployment, no goals, no velocity, no ownership
and no robot motion. Concrete live NavigationPort binding and supervised runtime
validation remain required; historical physical success is not proof of this
new mission orchestration.
