# Configuration, calibration and data architecture

## Three independent data domains

| Domain | Meaning | Examples | Must survive software reinstall? |
|---|---|---|---|
| Software | Versioned Bipolix code and dependency manifest | packages, launches, services, CLI, schema versions | Reproducible from release artifact |
| Robot | One physical unit and its measured properties | `robot_01`, adapter, capabilities, calibration, hardware inventory | Yes |
| Site | One operating environment | map, saved locations, routes, observation points, restricted zones | Yes; movable between compatible robots |

A robot can move to a new site by selecting site data; software is not
reinstalled and robot calibration is not copied into the site map.

## Configuration versus calibration

Configuration is an intentional policy or supported operating value: velocity
limit, watchdog timeout, feature selection, footprint, localization threshold
or Nav2 planner parameter. Calibration is a measured relationship for a
specific physical robot: sensor extrinsic, IMU alignment, timing offset or
motion correction.

Changing configuration follows review and tests. Changing calibration requires
a measurement method, robot identity and evidence. Neither is rewritten merely
to improve one localization score.

## Current configuration locations

| Concern | Current source(s) |
|---|---|
| Robot identity/capabilities/dimensions | Phase-1 `platform/config/robots/lite3/*.yaml`; C2 instance registry remains `c2/robots.json` |
| HIGH-LEVEL transport/gates | `lite3_high_level_runtime.launch.py`, bridge defaults, systemd environment/default file |
| AUTONOMY limits/watchdog | `lite3-autonomy-command-source.service` plus `lite3_autonomy_command_source.py` |
| Nav2 footprint/planner/controller/costmaps | `sensor_visualization/config/nav2_day2.yaml` and BT XML |
| AMCL/localization scoring | `amcl_stationary.yaml`, `lite3_state_estimation/config/amcl.yaml`, `localization_guard.py` parameters |
| LiDAR driver/extrinsic | `lite3_lidar_bringup.launch.py` launch defaults and stable serial by-id |
| Mapping | `slam_toolbox_lidar_only.yaml`, mapping launch/service and map manager |
| Saved-map metadata | per-map directory: `map.yaml`, image, `metadata.json`, `initial_pose.json` |
| Named locations scaffold | `sensor_visualization/config/named_locations.yaml` (future, not active missions) |
| DDS/network startup | systemd units and `lite3_ros_network_ready.sh`; ROS domain 0, SUBNET, UDPv4 |
| RViz | canonical laptop `laptop_visualization/lite3_remote_lidar.rviz` and session/watcher scripts |

The Phase-1 files under `platform/config/robots/lite3/` are contract/configuration
targets. Existing launch and unit files remain operationally authoritative
until a consumer, migration test and rollback exist.

## Concrete duplication debt

| Value | Current repeated locations | Migration authority target |
|---|---|---|
| AUTONOMY velocity 0.10/0.05/0.20 | autonomy service arguments, autonomy source defaults, HIGH-LEVEL autonomy bounds, Phase-1 motion config | one validated robot motion policy consumed by both source and final gate |
| Command timeout 0.30 s | autonomy source, HIGH-LEVEL autonomy timeout, laptop Xbox freshness and Phase-1 safety config | source-class safety policy with explicit per-source override only when justified |
| Localization threshold 0.80 ×3 | localization guard, gates/preflights/services and Phase-1 safety config | localization policy schema consumed by guard and readiness gates |
| Body 0.610×0.370 m and navigation footprint 0.710×0.470 m | robot config and Nav2 YAML | physical dimensions plus explicit navigation margin derivation |
| LiDAR mount z=0.08/yaw=π | LiDAR launch defaults | versioned `robot_01` calibration record after evidence capture |

The duplicates remain unchanged in this baseline. Removing them before deployed
consumers share validation and rollback would create two risks at once.

## Target layout

```text
config/
├── robots/
│   ├── types/lite3/
│   │   ├── robot.yaml
│   │   ├── motion.yaml
│   │   ├── safety.yaml
│   │   └── sensors.yaml
│   └── instances/robot_01.yaml
├── navigation/
├── localization/
├── sensors/
├── safety/
└── missions/

calibration/
└── robot_01/
    ├── lidar_extrinsics.yaml
    ├── camera_extrinsics.yaml
    ├── imu.yaml
    └── motion.yaml

sites/
└── Home/
    ├── site.yaml
    ├── maps/Home_Map/
    ├── locations.yaml
    ├── routes.yaml
    ├── observation_points.yaml
    └── restricted_zones.yaml
```

The current `platform/config/robots/lite3/robot.yaml` contains both type and the first
instance for compatibility. A future schema migration should split it only
after all consumers accept the split.

## Calibration record contract

Each calibration file should eventually record:

```yaml
schema_version: 1
robot_id: robot_01
kind: lidar_extrinsics
value: {x: 0.0, y: 0.0, z: 0.08, roll: 0.0, pitch: 0.0, yaw: 3.141592653589793}
method: documented_measurement_or_validation_method
measured_at: ISO-8601 timestamp
software_version: git/release identifier
config_version: identifier
evidence: optional relative evidence reference
notes: operator notes
```

This is a target schema, not a claim that the example values have complete
metrology evidence.

## Current calibration status

- The production LiDAR transform is currently published from launch defaults:
  `base_link→lidar_link`, z=0.08 m and yaw=π. It is the current source of truth
  and must not be changed or duplicated during this phase.
- `lite3_sensor_mounts.urdf.xacro` is a parameterized sensor-mount template and
  explicitly contains no guessed Lite3 extrinsics.
- RealSense driver optical frames exist when its optional service runs, but a
  production `base_link→camera_link` calibration is not established by the
  Day-2 navigation stack.
- Vendor telemetry supplies orientation/motion fields used inside the current
  HIGH-LEVEL path; a standalone production IMU-fusion calibration is not yet
  owned by the product state-estimation stack.
- Motion calibration experiments exist, but product Nav2 uses conservative
  configured velocity limits and vendor gait rather than an exported
  per-instance motion-calibration record.

## TF and state-estimation ownership

| Transform | Owner | Type | Meaning / source of truth |
|---|---|---|---|
| `map→odom` | AMCL (`/amcl`) | Dynamic | Global correction locating the odometry frame in the selected static map |
| `odom→base_link` | persistent `/lite3_high_level_runtime` | Dynamic, 50 Hz bounded | Startup-relative planar pose derived from vendor `pos_world`/yaw by `PlanarStartupOrigin` |
| `base_link→lidar_link` | `base_to_lidar_tf` from LiDAR bringup | Static | Current measured/validated LiDAR mount parameters in the launch defaults |

No other production component may publish these transforms. The alternative
state bridge and offline/test worlds must never run against the live production
graph. Future IMU fusion, visual odometry and GNSS/RTK must define a single
replacement/extension owner before activation; they cannot add a competing TF.

Current pose chain:

```text
startup-relative vendor odometry
  + RPLIDAR scan
  + selected static map
  → AMCL
  → map→odom→base_link→lidar_link
```

## Backup ownership

Future backup must include robot identity, per-instance calibration, approved
configuration, site maps/metadata, named locations/routes/restricted zones and
a version manifest. Runtime caches, build trees, credentials and transient
`/run` ownership state are not backup data.

Backup/restore must validate schemas and identity before activation. Restoring
site data must not overwrite robot calibration; restoring robot data must not
silently change software binaries.

## Version and rollback model

Track independently:

- software release/version;
- configuration schema and revision;
- per-robot calibration revision;
- site/map revision.

An update stages artifacts, validates compatibility and health, then activates
them atomically where practical. Failure returns to the previous known set.
Rollback must never restore old command ownership, velocity, operator
authorization or volatile runtime state.
