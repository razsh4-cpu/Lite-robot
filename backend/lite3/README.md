# Independent Lite3 autonomous backend — live binding implemented, not deployed

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

The live observer queries the active Map Server YAML parameter, hashes its assets
and requires the same identity and matching actually loaded occupancy grid,
resolution and origin. The grid decoder requires PyYAML/Pillow and supports
grayscale trinary maps; unsupported modes fail closed. Its semantics follow
[Nav2 Jazzy Map Server](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_map_server/src/map_io.cpp).
Site versions must be immutable while loaded;
never overwrite an active map/image underneath Map Server. Supervised RViz
validation still confirms the loaded grid and physical alignment. Saved poses
remain initial hypotheses only.

## Partner-facing Python contract

`AutonomyBackend` exposes `goto`, `start_patrol`, `pause_patrol`, `resume_patrol`,
`cancel_patrol`, `stop_patrol`, `handle_alert`, `navigation_result`,
`check_readiness` and read-only `status`. `IndependentRuntime` binds these to ROS
and supplies live readiness/result handling. No web/MQTT/fleet runtime is used.

`Readiness` requires three distinct consecutive fresh localization measurements
>=80%, verified prerequisites, matching map identity and correct source. Values
are fractions. The observer reads the existing authoritative localization state
files, using score-file measurement timestamps and deduplicating raw revisions.
Repeated reads or unchanged ROS publications cannot count as new measurements.
Snapshot
age limit is 2.5 seconds. Prerequisites include standing posture, fresh telemetry,
HIGH-LEVEL health, scan, odometry, TF, Map Server/AMCL lifecycle, Nav2/costmaps,
and no competing mission. During execution the collector must continuously call
`check_readiness`; absence of this loop must prevent live activation.

`NavigationPort.start(request_id, standard_map_pose)` is the sole navigation
boundary. `LiveNavigationPort` uses `RosNav2Transport` for `/navigate_to_pose`.
`SystemdAutonomy` starts/stops only the existing optional AUTONOMY service, which
alone acquires/releases the shared arbiter lock. Default execution approval is
false. No controller, mux, arbiter or UDP receiver is added. Existing
300 ms command watchdog and runtime interlocks remain authoritative.

An orchestration-only mutex serializes backend starts of the existing adapter;
it does not replace or acquire the physical arbiter's `owner.lock`. It remains
held during uncertain cleanup until cancellation, zero and source NONE are
confirmed. Mission status is refreshed from the live action-status publisher;
stale cached state cannot authorize dispatch.

`NavigationPort.stop` suppresses AUTONOMY before waiting for Nav2 cancellation,
then requires a terminal action result, fresh post-stop HIGH-LEVEL zero evidence
and confirms
`COMMAND_SOURCE=NONE`. A timeout/error leaves `STOPPING` and blocks new goals.
Callbacks carry request IDs; obsolete results are ignored. Patrol validates the
whole route before starting, stops/releases between waypoints, and never loops
implicitly. Alerts use configured saved-goal routing, pause a running patrol,
and require an explicit resume decision after arrival.

Future integration requirement only: AUTONOMY and LAPTOP_XBOX must remain
mutually exclusive through the shared Command Arbiter. No manual integration
is implemented or tested in this continuation.

## Reused authoritative files

- Localization/TF: `onboard_ros2_ws/src/lite3_state_estimation/`.
- Odometry/HIGH-LEVEL: existing `xbox_lite3_motion_host_bridge.py` (single receiver).
- Nav2: `sensor_visualization/config/nav2_day2.yaml`, existing Day-2 launch/BT.
- Obstacle workflow: `operator/lite3_nav_cli.py` and existing obstacle planning helpers.
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

## Onboard no-motion verification and later execution

Copy `site.example.yaml` to external site storage; fill `map_yaml` and
`saved_goals` paths and measured route names. Template null values deliberately
refuse startup. Registry entries still require `configured: true` and finite
map-specific x/y/yaw; no coordinates are invented.

In the existing onboard Jazzy/workspace environment, from the repository root:

```bash
python3 -m backend.lite3.run --site /absolute/path/to/site.yaml
```

This is read-only verification, even if all readiness gates pass. The observer
requires fresh sensor headers, dynamic TF (including AMCL timestamp tolerance),
standing/fresh HIGH-LEVEL state, battery >=25%, active lifecycle nodes, matching
map assets, no conflicting NavigateToPose goal, and the existing safety-monitor
service plus exactly one safety-monitor ROS node. UNKNOWN/stale state blocks.

Only following separate approval, add one of `--goto <id>`,
`--patrol supervised_validation`, or `--alert observation_alert`.
The launcher shows readiness/proposal and requires explicit `y` at its
default-N prompt. It rechecks readiness before acquiring AUTONOMY. Default
execution timeout is 60 seconds, configurable up to 300. Ctrl+C/timeout/error
cancels/suppresses the existing path; unconfirmed cleanup is visibly blocked.
Pause/resume/cancel/alert interruption are exposed through `IndependentRuntime`
for local Python callers; they must keep calling `step()` while active.

No-motion path preview remains the existing private `/day2/preview_goal` RViz
workflow, **not** `/goal_pose` (which can execute navigation). Never use a goal
execution command as a dry planner.

## Shortest supervised validation

1. Confirm installed workspace/profile and controller CPU compatibility; select
   any valid site map and measured map-specific goals (Home_Map optional).
2. No-motion: verify telemetry/scan/odom/TF, AMCL >=80% ×3, lifecycle/costmaps,
   one command authority, map hash and RViz alignment. Compute a dry path only.
3. Use the implemented observer/binding for no-motion live verification. Confirm
   the existing optional AUTONOMY unit/workspace paths and sudo permissions; do
   not start AUTONOMY or send a NavigateToPose goal as part of this dry check.
4. Explicit approval: 10 cm goal/STOP, then short turn goal, then visible obstacle
   avoidance or safe refusal. PASS requires arrival, zero and source NONE; abort
   on stale data, localization loss, unsafe clearance or unexpected motion.
5. Explicit approval: two measured saved goals/patrol; pause/resume/cancel;
   alert interrupt followed by explicit resume. Manual convergence is out of scope.

All new orchestration evidence is offline-only. Existing historical navigation
proof does not prove this new orchestration/live binding. No physical validation
is claimed. Real rclpy/Nav2 message/DDS execution is pending on the onboard ROS
environment; fake action/service transports validate software behavior only.
