# Independent Lite3 autonomous backend — prepared, not activated

This backend has no frontend dependency. It reuses the existing localization,
Nav2, obstacle test and single `AUTONOMY → arbiter → HIGH-LEVEL` path. No service
is installed by this directory. No robot commands are sent by its tests.

## External site contract

Supply an existing validated map YAML/image and its named-location registry.
`SavedGoals.for_site(registry, map_yaml)` hashes the exact YAML and image bytes;
goals are bound to that identity, not a universal `Home_Map`. Changing either
invalidates old goals. Missing map assets/coordinates fail closed. Registry
coordinates must be measured on that map; the loader cannot prove their physical
validity. Never generate production coordinates from the test fixtures.

The live integration must compute this same identity from the **active** map
assets and confirm Map Server actually serves them. A caller-supplied identity
alone is not proof of an active map. Saved poses remain initial hypotheses only.

## Partner-facing Python contract

`AutonomyBackend` exposes `goto`, `start_patrol`, `pause_patrol`, `resume_patrol`,
`cancel_patrol`, `stop_patrol`, `handle_alert`, `navigation_result`,
`check_readiness`, `prepare_manual_takeover` and read-only `status`.

`Readiness` requires three distinct consecutive fresh localization measurements
>=80%, verified prerequisites, matching map identity and correct source. Values
are fractions. The live collector must supply distinct measurements, not repeat
one score; this pure orchestration layer does not collect ROS data. Snapshot
age limit is 2.5 seconds. Prerequisites include standing posture, fresh telemetry,
HIGH-LEVEL health, scan, odometry, TF, Map Server/AMCL lifecycle, Nav2/costmaps,
and no competing mission. During execution the collector must continuously call
`check_readiness`; absence of this loop must prevent live activation.

`NavigationPort.start(request_id, standard_map_pose)` is the sole navigation
boundary. The only supplied implementation is `RecordingNavigation`, an offline
fixture. A concrete live port is **not provided or activated**: bind to existing
Nav2/AUTONOMY, never add a controller, mux, arbiter or UDP receiver. Existing
300 ms command watchdog and runtime interlocks remain authoritative.

`NavigationPort.stop` must cancel Nav2, confirm zero, release AUTONOMY and confirm
`COMMAND_SOURCE=NONE`. A timeout/error leaves `STOPPING` and blocks new goals.
Callbacks carry request IDs; obsolete results are ignored. Patrol validates the
whole route before starting, stops/releases between waypoints, and never loops
implicitly. Alerts use configured saved-goal routing, pause a running patrol,
and require an explicit resume decision after arrival. Manual takeover confirms
cancel/zero/release, then permits a **request** through the existing manual
arbiter; it never authorizes Xbox or restores previous commands.

## Reused authoritative files

- Localization/TF: `onboard_ros2_ws/src/lite3_state_estimation/`.
- Odometry/HIGH-LEVEL: existing `xbox_lite3_motion_host_bridge.py` (single receiver).
- Nav2: `sensor_visualization/config/nav2_day2.yaml`, existing Day-2 launch/BT.
- Obstacle workflow: `operator/lite3_nav.py` and existing obstacle planning helpers.
- RViz: `laptop_visualization/lite3_remote_lidar.rviz` (costmaps internally active).
- Registry: existing `sensor_visualization/config/named_locations.yaml`.

No footprint/inflation/controller/AMCL/TF tuning changed. NavFn/DWB limits remain
0.10 m/s forward, 0.05 m/s lateral, 0.20 rad/s yaw; lateral use still needs its
own applicable physical evidence. Footprint is 0.710 × 0.470 m, padding 0,
inflation 0.30 m. Do not claim these values guarantee safe clearance everywhere.

Workspace relocation uses `LITE3_WORKSPACE` (legacy default preserved),
`LITE3_ROS_SETUP` and `LITE3_RVIZ_CONFIG`. RViz launch paths resolve sibling files.
Deployment units must be inspected/bound to the selected workspace before live
use; no unit changes or deployments are performed by this preparation.

## Shortest supervised validation after Xbox PASS

1. Confirm installed workspace/profile and controller CPU compatibility; select
   any valid site map and measured map-specific goals (Home_Map optional).
2. No-motion: verify telemetry/scan/odom/TF, AMCL >=80% ×3, lifecycle/costmaps,
   one command authority, map hash and RViz alignment. Compute a dry path only.
3. Bind and no-motion-test the live NavigationPort against the existing path;
   verify cancel/zero/release and manual takeover without authorization transfer.
4. Explicit approval: 10 cm goal/STOP, then short turn goal, then visible obstacle
   avoidance or safe refusal. PASS requires arrival, zero and source NONE; abort
   on stale data, localization loss, unsafe clearance or unexpected motion.
5. Explicit approval: two measured saved goals/patrol; pause/resume/cancel;
   alert interrupt followed by explicit resume; manual takeover at zero.

All new orchestration evidence is offline-only. Existing historical navigation
proof does not prove this new orchestration/live binding. No physical validation
is claimed. The ROS-dependent autonomy test requires installed `rclpy` and robot
message packages, unavailable in this development test environment.
