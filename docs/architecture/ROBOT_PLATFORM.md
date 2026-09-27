# Lite3 current robot platform

This inventory records the real implementation at Architecture Phase 1. It is
not a proposed rewrite. Paths are repository paths; deployed Mini-PC paths are
under `/home/abx/ros2_ws` or `/home/abx/Desktop/robotdog_ws` as encoded by the
units.

## Current command and telemetry boundary

```text
GENERIC ROBOTICS
  Nav2 / operator C2 / optional local Xbox
        │  /cmd_vel or namespaced C2 Joy
        ▼
  source-specific validation + exclusive command-source lease
        │  /lite3/autonomy/cmd_vel or /lite3/laptop_xbox/joy
        ▼
LITE3-SPECIFIC
  persistent HIGH-LEVEL runtime
        │  freshness + standing + authorization + safe-zero gates
        ▼
  DeepRobotics Motion Host codec and HIGH-LEVEL UDP
        │  command 192.168.1.120:43893; sole telemetry receiver :43897
        ▼
  Lite3 vendor gait/controller and hardware
```

The persistent HIGH-LEVEL runtime is the single integration boundary today.
The generic Phase-1 interface must delegate to its protected ROS inputs; it is
not a second runtime.

## Real component inventory

| Function | Machine | Package / node | ROS/API boundary | systemd | Executable/script | Current configuration |
|---|---|---|---|---|---|---|
| HIGH-LEVEL transport, heartbeat, telemetry | Mini-PC `abx-fit-001` | `sensor_visualization` / `/lite3_high_level_runtime` | protected command subscriptions; vendor UDP | `lite3-high-level-runtime.service` | `lite3_high_level_runtime` → `lite3_high_level_runtime.launch.py` → `xbox_lite3_motion_host_bridge.py` | unit, `.default`, launch parameters |
| Robot telemetry/state decode | Mini-PC, inside the same process | vendor Motion Host codecs plus `lite3_state_estimation.core` helpers | decoded basic/gait state, RPY, velocity, position, battery | same HIGH-LEVEL service | `xbox_lite3_motion_host_bridge.py` | robot `192.168.1.120`, telemetry port `43897` |
| Odometry and base TF | Mini-PC, same process | `/lite3_high_level_runtime` | publishes `/odom` and `odom → base_link` at bounded 50 Hz | same HIGH-LEVEL service | same bridge | startup-origin logic in `lite3_state_estimation.core` |
| Battery / ultrasonic telemetry | Mini-PC, same process | `/lite3_high_level_runtime` | `/lite3/battery_percent`, `/lite3/ultrasound` | same HIGH-LEVEL service | same bridge | no second receiver |
| Vendor command output | Mini-PC, same process | `/lite3_high_level_runtime` | UDP to `192.168.1.120:43893` | same HIGH-LEVEL service | same bridge and loaded vendor codecs | `transmit`, `zero_only`, limits and gates in launch/runtime |
| Posture state | Mini-PC + laptop query | HIGH-LEVEL telemetry/log state; `lite3_posture_guard` | read-only guarded state/preflight | invoked by operator flow | `lite3_posture_guard.py` | `/run/lite3-control` state and HIGH-LEVEL journal |
| Stand / Down request | Laptop C2 into Mini-PC relay | operator CLI + robot-side `/lite3_laptop_xbox_source` | `/c2/robot_01/laptop_xbox/{request,heartbeat,joy,robot_status}` → `/lite3/laptop_xbox/joy` | `lite3-laptop-xbox-source.service` robot-side | `operator/lite3_robot_cli.py`, `lite3_laptop_xbox_source.py` | existing state-aware preflight; vendor posture toggle remains below boundary |
| AUTONOMY adapter | Mini-PC | `sensor_visualization` / `/lite3_autonomy_command_source` | `/cmd_vel` → `/lite3/autonomy/cmd_vel` | `lite3-autonomy-command-source.service` (explicit activation) | `lite3_autonomy_command_source.py` | 0.10 m/s forward/back, 0.05 m/s lateral, 0.20 rad/s yaw, 300 ms timeout |
| Nav2 | Mini-PC | Nav2 controller/planner/BT/lifecycle nodes | `NavigateToPose`, controller output `/cmd_vel` | `lite3-nav2.service` | `nav2_day2.launch.py` | `config/nav2_day2.yaml`; footprint 0.710 × 0.470 m |
| Command ownership / arbiter state | Mini-PC | source-specific lease implementations | `/run/lite3-control/COMMAND_SOURCE`, flock on `owner.lock` | used by HIGH-LEVEL and source units | `CommandSourceLease`, `LaptopXboxLease`, runtime source checks | valid `NONE`, `LOCAL_XBOX`, `LAPTOP_XBOX`, `AUTONOMY`; boot default `NONE` |
| Manual laptop Xbox source | Laptop C2 + Mini-PC relay | laptop `lite3_c2_xbox`; robot `/lite3_laptop_xbox_source` | laptop `/joy`, namespaced C2 topics, protected Joy topic | laptop user service(s); robot `lite3-laptop-xbox-source.service` | `c2/lite3_c2_xbox.py`, `lite3_laptop_xbox_source.py` | `c2/robots.json`; 300 ms request/heartbeat/Joy freshness |
| Optional local Xbox | Mini-PC | reconnect/input components and HIGH-LEVEL protected Joy path | `/joy` / optional local source | Xbox service units | Xbox startup/reconnect scripts | optional; not a robot-runtime prerequisite |
| LiDAR | Mini-PC | `rplidar_ros` launch | publishes `/scan`, TF through sensor model/static chain | `lite3-lidar.service` | `lite3_lidar_bringup.launch.py` | RPLIDAR S2 launch and URDF/extrinsics |
| Saved-map localization | Mini-PC | Map Server, AMCL, `localization_guard` | `/map`, `/amcl_pose`, `/localization/status`, `/localization/pose`, `map → odom` | `lite3-localization.service` | `lite3_localization_supervisor`, `localization_guard.py` | saved-map metadata, `amcl_stationary.yaml`; 0.80 ×3 gate |
| Health/readiness | Mini-PC | shell/Python monitors | freshness/lifecycle/state files in `/run/lite3-control` | `lite3-system-health.service`; HIGH-LEVEL watchdog where installed | `lite3_system_health.sh`, `lite3_high_level_ros_watchdog.py`, Nav2 safety monitor | actual ROS health checks, battery minimum 25% for navigation |
| Operator GUI / RViz | Laptop | RViz and operator wrappers | ROS2 DDS read/goal interfaces | laptop user watcher/autostart | laptop visualization/operator scripts | canonical RViz configuration; no GUI required onboard |

## Ownership and safety invariants

- `lite3-high-level-runtime.service` alone owns UDP telemetry port `43897` in
  production and alone publishes its derived `/odom` and `odom → base_link`.
- `lite3_state_estimation/high_level_state_bridge.py` is a receive-only
  alternative and must not run concurrently with the persistent runtime.
- Command sources are mutually exclusive through the lock and state marker.
- AUTONOMY validates localization readiness before ownership and applies a
  300 ms `/cmd_vel` watchdog. Invalid/stale input publishes zero and releases.
- Laptop Xbox relay requires fresh request, heartbeat and Joy; disconnect or
  stale input publishes neutral and releases.
- The HIGH-LEVEL runtime independently checks ownership, command freshness,
  telemetry freshness, standing state and operator authorization before motion.
- Nav2 never owns the vendor transport and does not acquire the command-source
  lease merely by starting.

## Generic versus Lite3-specific

Generic code may know planar velocity, posture intent, normalized health,
standard odometry, identity and capabilities. Lite3-specific code owns mapping
of basic-state values, vendor posture semantics, Motion Host packets, network
endpoints and hardware telemetry. Vendor details must not flow upward through
the Robot Interface.

## Known configuration debt

Some deployed unit paths mix `/home/abx/ros2_ws` and
`/home/abx/Desktop/robotdog_ws`. They are documented rather than changed in
Phase 1 because deployment-path consolidation needs a controlled rollout and
rollback. Command-source lease logic also exists in more than one source module;
it is behaviorally consistent but should eventually share one safety library
without altering the deployed boundary.
