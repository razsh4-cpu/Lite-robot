# BIPOLIX ROBOTICS PLATFORM — Architecture Baseline

This document is the architecture source of truth. Future architecture work must
read it and the linked inventory before changing production boundaries. It
organizes the hardware-proven Lite3 system; it does not replace it.

Core migration rule:

```text
wrap → define contracts → test → migrate gradually
```

## Top-level architecture

```text
                OPERATOR / C2
                     │
                MISSION LAYER
                     │
        ┌────────────┴────────────┐
        │                         │
     AUTONOMY                 PERCEPTION
   Nav2 / Goals              Sensors / AI
        │                         │
        └────────────┬────────────┘
                     │
             SAFETY / ARBITRATION
                     │
               ROBOT INTERFACE
                     │
               ROBOT ADAPTER
                     │
              VENDOR / HARDWARE
                     │
               PHYSICAL ROBOT
```

Supporting platform architecture:

```text
State Estimation       Sensor Management       Configuration
Calibration            Robot Identity          Health / Diagnostics
Logging / Black Box    Networking              Deployment
Updates / Rollback     Backup / Restore        Testing / Acceptance
```

Detailed evidence and policies:

- [Real component inventory](COMPONENT_INVENTORY.md)
- [Current Lite3 platform boundary](ROBOT_PLATFORM.md)
- [Safety and arbitration](SAFETY_AND_ARBITRATION.md)
- [Configuration, calibration and data](CONFIGURATION_CALIBRATION_DATA.md)
- [Platform operations, perception and deployment](PLATFORM_OPERATIONS.md)
- [Gradual migration plan](MIGRATION_PLAN.md)

## Major layer contracts

| Layer | Responsibility | Allowed inputs | Allowed outputs | Dependencies | Must not | Failure behavior |
|---|---|---|---|---|---|---|
| Operator / C2 | Commands, status, visualization, manual-control and mission requests | Human input, registry, read-only robot/system state | Explicit requests to Mission, Autonomy or approved manual source | Networking, generic contracts, status APIs | Control motors, publish below protected source boundary, bypass arbiter/HIGH-LEVEL | Report unavailable; owned manual source sends neutral and releases on loss |
| Mission Layer | Decide *what* outcome to pursue and track mission lifecycle | Operator/alert requests, named/ad-hoc target, capabilities, autonomy result | Goals/cancel to Autonomy; mission state/events | Generic Robot Interface, site data, Autonomy API | Plan paths, publish velocity, encode vendor commands | Cancel/stop requested action, enter FAILED/CANCELLED/RECOVERING and preserve result |
| Autonomy | Decide *how* to navigate: localization integration, planning, control, obstacle avoidance | Mission goal, map/pose, sensors, capabilities | Standard bounded velocity intent through approved AUTONOMY source | Nav2, State Estimation, Sensor Management, Safety | Assume unsupported axes, own vendor transport, bypass lease | Stop/cancel and release on invalid localization, stale prerequisites or action failure |
| Perception | Interpret sensor information into observations/events | Timestamped calibrated sensor streams and sensor health | Detections, tracks, alerts with frame/confidence/provenance | Sensor Management, calibration, TF | Directly command motion, rewrite map/calibration, replace deterministic safety | Mark output stale/degraded; downstream rejects unusable observations |
| Safety / Arbitration | Exclusive ownership, authorization, watchdogs, stale-data response, safe zero and fault response | Source requests, health, permits, state freshness | One valid lease and approved protected command stream | Onboard clock/state, Robot Interface health, existing guards | Grant competing sources, restore stale velocity/authorization, weaken gates | Zero, revoke, release to NONE, expose exact fault |
| Robot Interface | Vendor-neutral identity, capability, state, posture, health, odometry and planar intent | Generic validated requests; normalized adapter state | Generic contract to/from one adapter | Contract/config schemas only | Contain vendor IDs, packets, addresses or direct hardware access | Reject invalid/unsupported request; report DEGRADED/FAULT/OFFLINE |
| Robot Adapter | Translate generic contracts to the existing approved platform path | Generic intent and vendor-derived state | Protected ROS interface; normalized generic state | One Robot Interface, platform configuration, existing safety path | Create duplicate receiver/runtime/arbiter/controller | Preserve safe-zero/release; surface translation/transport health |
| Vendor / Hardware | Balance, gait, joint-level locomotion and physical telemetry | Approved adapter command | Hardware action and vendor telemetry | Vendor controller, electrical/mechanical platform | Define missions or higher-level policy | Native watchdog/fault handling; upstream observes and stops safely |
| Physical Robot | Mechanical/electrical execution | Vendor controller actuation | Physical state and sensor signals | Power, compute, buses, sensors, mechanics | Be treated as software-only | Hardware protection plus software fault reporting where measurable |

Dependencies point downward or sideways only through explicit contracts. Higher
layers never import Lite3/DeepRobotics code. Circular dependencies are forbidden.

## Supporting platform contracts

| Concern | Owns | Does not own | Failure behavior |
|---|---|---|---|
| State Estimation | authoritative pose/velocity chain and covariance | goals or motion ownership | invalidate pose/readiness; navigation blocks/stops |
| Sensor Management | drivers, device identity, frames, timestamps and stream health | mission logic or USB handling in missions | mark sensor unavailable/stale; dependent capability degrades |
| Configuration | reviewed operating policy and limits | measured per-robot calibration | schema failure blocks affected subsystem |
| Calibration | measured per-robot relationships with evidence/version | site maps or policy limits | invalid/missing record blocks dependent sensor fusion |
| Robot Identity | type, instance, adapter and hardware inventory | site identity | unknown/incompatible identity prevents activation |
| Health / Diagnostics | subsystem state and operation-specific aggregation | command ownership | report exact degraded/fault/offline subsystem |
| Logging / Black Box | bounded events, diagnostics, actions and result evidence | safety authority | logging fault is reported; it does not bypass stop behavior |
| Networking | onboard/private robot links, DDS readiness, C2 transport | mission semantics | local safety survives; remote-owned source times out/releases |
| Deployment | versioned artifacts, installation and service enablement | runtime command | failed validation retains/returns previous known version |
| Updates / Rollback | staged activation and version compatibility | volatile ownership restoration | rollback with motion source NONE |
| Backup / Restore | robot/config/calibration/site/version data | credentials or transient `/run` state | validate identity/schema before restore activation |
| Testing / Acceptance | offline, simulation and live evidence classes | permission to infer hardware safety from offline tests | failed gate blocks promotion; evidence class remains explicit |

## Robot Interface baseline

The generic contract is implemented as pure types in
`src/robot_interfaces/bipolix_robot_interfaces`. It exposes:

- planar `linear.x`, `linear.y`, `angular.z` intent and stop as the all-zero
  velocity command;
- posture `SITTING`, `STANDING`, `TRANSITIONING`, `UNKNOWN` and operations
  `stand`/`down`;
- connected, moving, telemetry freshness, reliable battery when available,
  fault and HIGH-LEVEL readiness;
- standard odometry topic `/odom`;
- health `READY`, `DEGRADED`, `FAULT`, `OFFLINE`;
- robot identity, motion limits and capability queries.

The interface validates values and support but is not a substitute for runtime
safety. Its implementation must still use leases, watchdogs and protected ROS
endpoints. It has no vendor imports, ports or packet IDs.

## Robot type and instance

```text
Robot Type:     manufacturer=DeepRobotics, model=Lite3 Venture, adapter=lite3
Robot Instance: robot_id=robot_01
```

The type selects capabilities and adapter behavior. The instance selects
identity, hardware inventory and calibration. Mission/Nav2/C2 architecture must
not be built around the literal `robot_01`; future instances may share or differ
in type.

## Capability baseline

Current Lite3 product capabilities are forward, backward, lateral and yaw
motion through vendor gait; stand/down posture path; odometry; battery; and
telemetry. Capabilities describe an approved route, not permission to move.
Runtime state and safety gates still decide whether a request is currently
allowed.

## Motion architecture

```text
Mission
  → Nav2 goal
  → planner/controller
  → /cmd_vel
  → AUTONOMY validation + exclusive lease + 300 ms watchdog
  → /lite3/autonomy/cmd_vel
  → persistent HIGH-LEVEL runtime safety gates
  → DeepRobotics vendor gait
  → joint-level vendor controller / 12 joints
```

Nav2 owns where/how to navigate; its controller requests velocity now. Vendor
HIGH-LEVEL gait owns balance, leg phasing and joint locomotion. Joint-level
control remains hardware-specific. Neither Mission nor Robot Interface
reimplements gait.

The separate MotionSDK/ONNX/MuJoCo/IK/FK/body-shift/leg-lift path is
**Advanced Locomotion / Physical AI R&D**, not a patrol fallback. See ADR-003.

## State-estimation and TF architecture

Current product chain:

```text
startup-relative Lite3 odometry + RPLIDAR + static map → AMCL → robot pose
```

Authoritative TF ownership:

- `map→odom`: dynamic, AMCL;
- `odom→base_link`: dynamic, persistent HIGH-LEVEL runtime;
- `base_link→lidar_link`: static, LiDAR bringup using current launch parameters.

No competing publisher is permitted. Future IMU fusion, visual odometry or
GNSS/RTK must designate a replacement/extension owner and migration gate first.

## Sensor and perception architecture

RPLIDAR is the deterministic mapping/localization/2D obstacle source. Vendor
telemetry is the robot-state source. D455 is optional/on-demand for future depth
and perception; current Nav2 does not depend on it. Ultrasound is exposed but
not yet a validated navigation safety input. Mission code never manages sensor
processes or devices directly.

AI is restricted to perception/event/operator assistance unless a future ADR
proves otherwise. AI can propose an alert or mission; it cannot publish
protected motion, acquire ownership or bypass deterministic localization,
Nav2, arbitration or HIGH-LEVEL safety.

## Mission architecture (defined, not implemented)

Future mission types: `GoTo`, `Patrol`, `Inspect`, `RespondToAlert`,
`ReturnHome`, `Cancel`. States: `PENDING`, `RUNNING`, `ARRIVED`, `FAILED`,
`CANCELLED`, `RECOVERING`.

Targets may be a named site location or an ad-hoc map pose. Alert coordinates
are not automatically destinations; policy derives a safe observation pose.
Mission Manager decides *what* and tracks results; Nav2 performs navigation.
This baseline does not activate the existing saved-location scaffold or start
Day 3.

## Safety, health and offline-first operation

The future aggregate progression is
`BOOTING→SYSTEM_READY→STANDING→LOCALIZED→NAVIGATION_READY→MISSION_ACTIVE`, mapped
from existing real probes and states rather than replacing them. Faults take
`MISSION_ACTIVE→FAULT→STOPPING→SAFE`, where SAFE is zero, revoked authorization
and released ownership while persistent telemetry may remain active.

Health is per subsystem and per requested operation. Laptop or internet loss is
not a core robot fault; laptop-owned manual control times out, while onboard
runtime and local safety remain. See `SAFETY_AND_ARBITRATION.md` for exact fault
ownership.

## Data, deployment and evidence

Software, robot and site are separate versioned domains. Calibration is measured
per robot and is not ordinary configuration. Site data owns maps, locations,
routes, observation points and restricted zones. Backup/restore and rollback do
not restore transient ownership or velocity.

Runtime evidence evolves toward bounded per-session metadata, events,
diagnostics, rosbag and result while retaining journal and focused tools.
Simulation uses the same contracts where practical but is always labeled as
simulation evidence.

## Current Phase-1/Architecture-Baseline code boundary

```text
src/robot_interfaces/bipolix_robot_interfaces/   # generic pure contracts
src/robot_adapters/lite3/bipolix_lite3_adapter/ # Lite3 state normalization
config/robots/lite3/                             # target contract configuration
tests/architecture/                              # offline contract/baseline checks
docs/architecture/                               # source of truth and decisions
```

These files start no ROS node, service or socket. Existing production units and
launch files remain authoritative until a controlled migration.

## Architectural decisions

- [ADR-001: vendor gait for product locomotion](decisions/ADR-001-vendor-gait-product-locomotion.md)
- [ADR-002: generic interface and Lite3 adapter](decisions/ADR-002-generic-interface-lite3-adapter.md)
- [ADR-003: low-level work remains R&D](decisions/ADR-003-low-level-rnd-separation.md)
- [ADR-004: onboard runtime and laptop operator split](decisions/ADR-004-onboard-runtime-laptop-operator.md)

## Change rule

Any change to an authoritative owner, protected topic, transform, lease,
watchdog, calibration, machine split or data-domain boundary requires an ADR or
an update to this baseline, focused offline tests, relevant regression tests and
an explicit deployment/rollback plan. Live hardware validation is separate and
requires approval for the exact run.
