# Platform, perception and operations architecture

## Sensor Management boundary

Sensor Management owns driver lifecycle, device identity, frame assignment,
timestamps, diagnostics and the declaration of which streams are authoritative.
Mission code consumes interpreted observations or health; it does not open USB
devices, configure serial ports or start drivers.

| Sensor/source | Current responsibility | Current status | Future boundary |
|---|---|---|---|
| RPLIDAR S2 | mapping, AMCL and 2D Nav2 obstacle detection | Required for mapped Day-2 navigation; `/scan` | Deterministic navigation sensor managed onboard |
| Vendor odometry/telemetry | base motion, posture, battery, ultrasound and robot link evidence | Required HIGH-LEVEL source; sole UDP receiver | Lite3 Adapter normalizes robot state |
| IMU fields | orientation/motion information inside vendor telemetry; alternate SDK bridge can publish research topics | Not a separately fused production source | State Estimation may fuse after calibration and single-owner design |
| RealSense D455 | aligned depth/point cloud experiments and future perception | On-demand; not used by current LiDAR Nav2 | Perception pipeline with explicit stream/resource profile |

The offline RViz profile `sensor_visualization/rviz/d455_s2_map.rviz` combines
the map, red `/scan`, blue Lite3 body/heading, Nav2 path/goal and the existing
D455 point-cloud topic. It does not invent `base_link→camera` calibration. Live
Mini-PC/D455 work must verify the real camera frames and TF alignment before
that point cloud is treated as spatially registered. `lite3-realsense.service`
remains on-demand and is not a boot dependency because its previous workload
was approximately one CPU core.
| Ultrasonic | four values exposed on `/lite3/ultrasound` | Available telemetry, not in current navigation safety policy | Near-field safety input after validation, diagnostics and fault policy |

Deterministic obstacle and localization sensing remains separate from future AI
interpretation. A perception model may publish detections/events; it does not
replace scan freshness, TF, costmaps or the command arbiter.

## Perception and AI boundary

Traditional deterministic robotics owns localization, TF, Nav2, safety,
arbitration and motor control. AI/perception may implement person detection,
object recognition, anomaly detection, event understanding and natural-language
operator assistance.

AI output is a proposal or observation with confidence, timestamp, frame and
provenance. It may propose an alert or mission request. It may not acquire a
motion lease, publish protected commands, rewrite maps/calibration or directly
control motors.

## C2 and networking

```text
Laptop / C2  ↔  robot network / ROS 2 DDS  ↔  Mini-PC  ↔  Lite3 private link
```

Mini-PC owns robot-critical runtime, active sensors, state estimation,
localization, Nav2, safety and the robot adapter. Laptop owns RViz, Xbox input,
operator CLI, monitoring and development/debug tools. C2 namespaces commands by
robot instance; today `robot_01` is the only registered instance.

ROS 2 currently uses domain 0, SUBNET discovery and UDPv4 in the relevant
units/wrappers. Robot command/telemetry uses the separate Lite3 private network
target `192.168.1.120` and ports documented in `ROBOT_PLATFORM.md`. The network
readiness service gates DDS participant startup after boot.

Loss of laptop or internet must not terminate onboard heartbeat, telemetry,
odometry, LiDAR, localization or safety. Loss of a laptop-owned command stream
must release LAPTOP_XBOX. Future multi-robot C2 adds registry/discovery and
per-robot status/alerts without sharing a motion lease across robots.

## Offline-first behavior

Core safe operation and local navigation are onboard and do not depend on cloud
services. Remote supervision can disappear while local safety remains active.
Policy for a remote-link loss during a future mission must be explicit per
mission (continue locally, stop safely, or return), but the default for an
unclassified remote command stream is fail closed.

## Observability and black box

Current evidence is split across systemd journal, health state files,
purpose-specific diagnostics, optional rosbag and explicit control logs. The
target is a bounded session record:

```text
runs/<session_id>/
├── metadata.yaml
├── events.jsonl
├── diagnostics.jsonl
├── rosbag2/
└── result.yaml
```

Minimum metadata: session ID, UTC/local timestamps, robot ID, site/map,
software/config/calibration revisions, operator or initiating subsystem, mission
type, safety limits and evidence class (offline/simulation/live). Events include
ownership changes, operator approvals, lifecycle changes, mission transitions,
faults, stops and recovery outcomes.

The onboard logger owns time-critical fault evidence and uses bounded retention;
the laptop may copy or enrich it but is not required for capture. Sensitive
credentials are never recorded. Logs are observability—not command authority.

## Power and hardware boundary

The platform includes battery/power conversion, Mini-PC, sensors, USB, Ethernet
and Wi-Fi adapters, connectors, mounting and thermal behavior. Software may
consume measurable battery, temperature, throttling, storage, network and device
health. It cannot infer absent hardware telemetry as healthy.

Mechanical mounting and cabling affect calibration and reliability. A software
release does not certify power margins, connector retention or sensor mounting.
Hardware changes require an inventory/calibration review before navigation
acceptance.

## Simulation boundary

Future structure:

```text
Robot Interface
├── Lite3 Adapter
└── Simulation Adapter
```

Mission, navigation orchestration and non-hardware safety logic should run
against either adapter. Simulation supplies normalized state, odometry, sensors
and command acknowledgements under the same contracts. It must be unmistakably
identified as simulation and cannot be presented as live hardware evidence.
Existing MuJoCo/ONNX work is not moved or rewritten in this baseline.

## Advanced Locomotion / Physical AI R&D

MotionSDK, ONNX, MuJoCo, IK/FK, body shift, FR leg lift and foothold/stepping
experiments remain a separate evidence and safety domain:

```text
Vendor Gait + ROS2/Nav2 = product/patrol path
Low-Level/MotionSDK/ONNX = advanced locomotion R&D
```

R&D executables never become an implicit fallback for the product adapter. Any
future product promotion requires a dedicated ADR, ordered hardware milestones,
permits, ownership compatibility and regression evidence.

## Deployment target

```text
Fresh supported Linux
  → signed/versioned Bipolix release
  → dependencies and ROS 2 Jazzy
  → robot adapter package
  → robot type + instance configuration
  → per-robot calibration
  → site selection
  → offline/static validation
  → hardware validation checklist
  → READY FOR MAPPING
```

Future deployment artifacts include OS/dependency manifest, package artifacts,
systemd units and enablement policy, configuration/calibration schemas, robot
registry, site-data tooling, health/acceptance scripts, migration scripts,
release notes and rollback manifest. No USB installer or updater is built in
this phase.

## Update and rollback

Updates are staged and validated before switching the active version. Service
health must be checked at ROS/lifecycle/topic level rather than only systemd
`active`. Configuration and calibration migrations are explicit and reversible.
On failed validation, stop command sources, preserve zero/`NONE`, roll back the
artifact set, then rerun readiness. Never hide failures by weakening watchdogs
or freshness thresholds.
