# Architecture component inventory

Evidence date: 2026-09-28. This inventory is derived from repository source,
launch files and systemd units. It describes the intended deployed topology; it
does not claim that a service is currently installed or active on a machine.

## Robot-critical runtime and control

| Responsibility | Machine | Package / executable / node | Interfaces | Service / configuration | Dependencies and consumers | Safety relevance |
|---|---|---|---|---|---|---|
| Stable ROS network gate | Mini-PC | `sensor_visualization/lite3_ros_network_ready` | NetworkManager and ROS/DDS readiness | `lite3-ros-network-ready.service`; ROS domain 0, SUBNET discovery | Precedes runtime, LiDAR and localization | Prevents half-started DDS graph after boot |
| Persistent HIGH-LEVEL transport, heartbeat, telemetry and odometry | Mini-PC | `lite3_high_level_runtime` launch; `xbox_lite3_motion_host_bridge.py`; node `/lite3_high_level_runtime` | subscribes `/lite3/autonomy/cmd_vel`, `/lite3/laptop_xbox/joy`, legacy/local `/joy`; publishes `/odom`, `/lite3/battery_percent`, `/lite3/ultrasound`, `odom→base_link`; UDP command `192.168.1.120:43893`, telemetry `:43897` | `lite3-high-level-runtime.service`; `lite3_high_level_runtime.launch.py`; optional `/etc/default/lite3-high-level-runtime` | Requires network gate; consumed by all state, posture, navigation and health paths | Sole production hardware transport and telemetry receiver; standing, freshness, authorization and zero gates |
| AUTONOMY command source | Mini-PC | `lite3_autonomy_command_source.py`; node `/lite3_autonomy_command_source` | `/cmd_vel` → `/lite3/autonomy/cmd_vel`; `/run/lite3-control` lease | `lite3-autonomy-command-source.service`; limits 0.10/0.05/0.20; 300 ms watchdog | Requires HIGH-LEVEL and localization gate; input from Nav2 | Exclusive AUTONOMY lease, finite/clamped commands, zero/release on stale or invalid input |
| Laptop Xbox command source relay | Mini-PC | `lite3_laptop_xbox_source.py`; node `/lite3_laptop_xbox_source` | `/c2/robot_01/laptop_xbox/{joy,heartbeat,request,robot_status}` → `/lite3/laptop_xbox/joy` | `lite3-laptop-xbox-source.service`; 300 ms freshness | Requires network gate and HIGH-LEVEL; input from laptop C2 | Exclusive LAPTOP_XBOX lease; neutral/release on disconnect or stale input |
| Optional local Xbox input | Mini-PC | Xbox startup/reconnect scripts and `lite3_high_level_xbox_runtime` | `/dev/input/js0`, local `/joy`, LOCAL_XBOX lease | `lite3-xbox.service`, `lite3-high-level-xbox.service`, Xbox defaults | Bluetooth and HIGH-LEVEL; optional | Never a system-readiness prerequisite; reconnect cannot restore old motion |
| Posture preflight/state | Mini-PC | `lite3_posture_guard.py` | read-only state files and HIGH-LEVEL journal | Invoked by laptop posture CLI | HIGH-LEVEL state freshness and `COMMAND_SOURCE` | Blocks posture when motion/ownership/state is unsafe |
| Posture operator | Laptop plus Mini-PC C2 relay | `operator/lite3_robot_cli.py` / temporary C2 Joy edge | C2 request/heartbeat/Joy/status | installed `robot` wrapper; robot relay service | Uses existing C2 lease and vendor posture implementation below HIGH-LEVEL | No direct socket; confirms telemetry and releases temporary ownership |

## Sensors, state estimation and localization

| Responsibility | Machine | Package / executable / node | Interfaces | Service / configuration | Dependencies and consumers | Safety relevance |
|---|---|---|---|---|---|---|
| RPLIDAR S2 driver and static mount TF | Mini-PC | `sllidar_ros2`; `base_to_lidar_tf` | publishes `/scan` in `lidar_link`; static `base_link→lidar_link` | `lite3-lidar.service`; `lite3_lidar_bringup.launch.py`; serial by-id; current defaults z=0.08 m, yaw=π | Network gate; consumed by SLAM, AMCL, costmaps, health | Primary Day-2 obstacle sensor; stale scan aborts/blocks navigation |
| RealSense D455 | Mini-PC, on demand | `realsense2_camera` | color/depth/aligned depth/point cloud according to driver launch | `lite3-realsense.service`; `align_depth=true`, `pointcloud=true`; intentionally no boot install target | Optional RViz/perception experiments; not consumed by current Day-2 Nav2 | Not a navigation prerequisite; avoids consuming a CPU core when unused |
| Static map and AMCL | Mini-PC | `nav2_map_server/map_server`, `nav2_amcl/amcl` | `/map`, `/amcl_pose`, `map→odom`; services for global/no-motion localization | `lite3-localization.service`; supervisor; `day1_localization.launch.py`; `amcl_stationary.yaml` / `amcl.yaml` | Requires fresh `/scan`, `/odom`, TF; consumed by localization gate and Nav2 | Lifecycle readiness and bounded recovery; no motion command path |
| Localization confidence/state | Mini-PC | `lite3_state_estimation/localization_guard`; node `/lite3_localization_guard` | reads `/map`, `/scan`, `/odom`, `/amcl_pose`, TF; publishes `/localization/status`, `/localization/pose`, `/initialpose` | launched with localization; per-map `initial_pose.json`; threshold 0.80 ×3 | Consumed by Nav2/AUTONOMY gates, status and RViz | Saved pose is hypothesis only; global localization fallback; reports UNLOCALIZED until gate passes |
| Explicit mapping mode | Mini-PC, selected from laptop | `slam_toolbox` via `slam_mapping.launch.py`; `lite3_map_manager.py` | `/scan`, `/odom`, TF → live map; map saver | `lite3-mapping.service`, conflicts with localization; map manager state | Requires HIGH-LEVEL and LiDAR; consumed by operator mapping workflow | No command output; mapping and localization cannot run as competing modes |
| Alternative receive-only state bridge | Mini-PC development path | `lite3_state_estimation/high_level_state_bridge` | would bind UDP 43897 and publish `/odom`, telemetry and TF | `high_level_state.launch.py`; no production service | Alternative to, never alongside, persistent HIGH-LEVEL | Must remain off while production runtime owns `43897` |
| SDK telemetry bridge | Mini-PC R&D path | C++ `lite3_telemetry_bridge` | `/lite3/imu/data`, `/lite3/joint_states`, `/lite3/contact_force_z` | built by `sensor_visualization/CMakeLists.txt`; no production unit | MotionSDK-based R&D consumers | Not part of product state-estimation ownership |

## Navigation, safety and health

| Responsibility | Machine | Package / executable / node | Interfaces | Service / configuration | Dependencies and consumers | Safety relevance |
|---|---|---|---|---|---|---|
| Planner/controller/BT | Mini-PC | Nav2 `planner_server`, `controller_server`, `bt_navigator`, lifecycle manager | actions `/compute_path_to_pose`, `/navigate_to_pose`; output `/cmd_vel`; costmap topics | `lite3-nav2.service`; `nav2_day2.launch.py`, `nav2_day2.yaml`, BT XML | Requires network, fresh inputs and localization ≥0.80; controller output consumed only by AUTONOMY source | Starting Nav2 does not acquire command ownership |
| Global/local costmaps | Mini-PC, within Nav2 | Nav2 costmap nodes | `/map`, `/scan`, TF; global/local costmaps | `nav2_day2.yaml`; footprint 0.710×0.470 m, padding 0, inflation radius 0.30 m | Planner/controller consume; RViz may display but display is not control | Full robot footprint and LiDAR obstacles remain active even if hidden in RViz |
| Independent Nav2 health abort | Mini-PC | `lite3_nav2_safety_monitor.py` | reads `/odom`, `/scan`, `/cmd_vel`, battery, localization and ownership | `lite3-nav2-safety-monitor.service`, PartOf Nav2 | Watches live mission prerequisites | Stops AUTONOMY source on stale data, low battery or invalid localization |
| Localization startup recovery | Mini-PC | `lite3_localization_supervisor.sh`, input and lifecycle readiness gates | lifecycle states, TF and `/run/lite3-control` stage files | `lite3-localization.service`; three bounded attempts and DDS cleanup | Starts Map Server then AMCL only after required inputs | Reports exact stage/STARTUP_FAILED instead of half-ready state |
| System health aggregation | Mini-PC | `lite3_system_health.sh` | real topic/TF/lifecycle probes; writes `/run/lite3-control/*` | `lite3-system-health.service`, 10 s default interval | Consumed by status/C2/operator | Laptop absence and optional RealSense do not make robot core unhealthy |
| Relocalization recovery motion | Mini-PC, explicit laptop approval | `lite3_relocalization_motion.py` through `lite3_relocalization_run` | approved bounded `/cmd_vel` → AUTONOMY path | `lite3-relocalization-motion.service`; no install target; conflicts with normal AUTONOMY source | Requires HIGH-LEVEL, LiDAR, localization and explicit approval | Bounded motion, clearance/freshness checks, 300 ms watchdog, zero/release cleanup |

## Laptop / C2 / operator

| Responsibility | Machine | Implementation | Interfaces and consumers | Safety relevance |
|---|---|---|---|---|
| Robot registry and Xbox C2 | Laptop | `c2/robots.json`, `lite3_c2_xbox.py`, connect/disconnect and C2 CLIs, user services | local `/joy`; robot-namespaced C2 topics over ROS 2 DDS | Selection is instance-based; manual control requires explicit lease and fresh authorization |
| Operator command registry | Laptop | `operator/lite3_command_registry.py` | Installed `commands` menu for real wrappers only | Labels motion/ownership/read-only operations; no command emission itself |
| Map/localization CLI | Laptop → SSH Mini-PC | `lite3_map_cli.py` → `lite3_map_manager` | `status`, `maps`, `mapping`; RViz session service | Mapping never drives; map selection gates localization and may offer approved recovery |
| Relocalization CLI | Laptop → SSH Mini-PC | `lite3_relocalize_cli.py` | status/preflight/approval/start/cancel | Default answer is no; ownership is not acquired before explicit approval |
| RViz visualization | Laptop | `lite3-rviz-watcher.service`, session scripts, canonical RViz config, blue robot marker | DDS topics/actions; no Mini-PC GUI | Optional visualization; single-instance behavior; laptop loss does not stop robot runtime |
| Reliability evidence | Laptop and Mini-PC | `lite3_reliability_monitor.py`, collectors and systemd units | boot IDs, resource/kernel/network/service evidence | Read-only persistent evidence for reboot/freeze/network diagnosis |
| Day-2 dry-run tools | Laptop | plan/preview/snapshot analyzers and guarded executors | Nav2 actions, costmaps, scan, AMCL, `/cmd_vel` observation | Development tools; not boot services; physical execution requires explicit approval |

## Canonical laptop operator commands

The maintained registry is `operator/lite3_command_registry.py`. Availability is
checked against installed wrappers; this table records the implemented command
families, not permission to run motion.

| Commands | Role | Motion/ownership behavior |
|---|---|---|
| `robot status`, `status`, `relocalize status`, `commands`, `day2-ready`, `day1-acceptance` | Read-only state/health/menu/acceptance | No ownership or motion; `day1-acceptance` may open RViz |
| `robot stand`, `robot down` | State-aware posture | Temporary approved C2 ownership; existing HIGH-LEVEL posture path; zero and release afterward |
| `connect joystick`, `disconnect joystick`, `take control`, `release control`, `c2 ...` | Laptop Xbox/C2 selection and ownership | Explicit lease/release; fresh authorization required; disconnect first releases safely |
| `maps`, `maps Home_Map` | List/select saved map and localize | No automatic drive; may offer separately approved relocalization motion |
| `mapping`, `mapping --cancel` | Enter/cancel SLAM mapping mode | Mode change only; never drives robot |
| `relocalize`, `relocalize cancel` | Bounded recovery workflow | Explicit confirmation before ownership/motion; cancel zeros and releases idempotently |
| `prepare-day2` | Deployment maintenance | Installs prepared files; no motion |

Physical Day-2 plan/execute/obstacle tools under `operator/` are engineering
validation utilities, not general boot services or Mission Layer APIs.

## Logging and diagnostics currently present

- systemd journal is the primary runtime log for robot services.
- `lite3_bag_recorder.py` wraps rosbag2 for a fixed diagnostic topic set.
- `lite3_control_logger.py` and `lite3_log_analyzer.py` support bounded control
  evidence in explicit launch paths.
- readiness, Xbox, Nav2 preflight, map status and reliability tools provide
  purpose-specific diagnosis.
- A unified session/black-box manifest does not yet exist; its target contract
  is defined in `PLATFORM_OPERATIONS.md`.

## Dormant and R&D components

Installed executables are not automatically production owners. In particular,
the alternative telemetry bridge, keyboard/calibration/manual-axis tools,
offline world, packet inspector, low-level MotionSDK/ONNX controllers and the
saved-location mission registry are development/R&D or future scaffolds. They
must not be launched concurrently with an authoritative production owner.
