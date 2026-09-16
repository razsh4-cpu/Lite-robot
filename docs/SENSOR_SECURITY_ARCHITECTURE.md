# Lite3 sensing and security-patrol architecture

This is an offline architecture review. The robot was off; no sensor or robot
process was started.

## Evidence labels

- **PROVEN_FROM_CURRENT_PROJECT**: code/configuration or prior recorded result.
- **SUPPORTED_BY_OFFICIAL_DOCUMENTATION**: primary vendor/ROS documentation.
- **ENGINEERING_INFERENCE**: sensible design choice that needs validation.
- **REQUIRES_PHYSICAL_TEST**: must be measured on this Lite3.

## Current audit

| Area | Status | Evidence |
|---|---|---|
| RPLIDAR S2 driver | EXISTS_AND_TESTED | `sllidar_ros2` is present; S2 launch publishes `scan`, default frame `laser`, 1 Mbaud and 10 Hz. Revalidate after mounting. |
| LiDAR scan matching | PARTIAL | `lidar_odometry.launch.py` runs RTAB-Map ICP with conservative parameters. Prior real tracking loss means it is not accepted Nav2 odometry. |
| Mapping/AMCL/Nav2 | PARTIAL | SLAM Toolbox, saved-map AMCL and planner-only scaffolds exist. They contain temporary `laser`/`camera_link` choices and are not a mobile TF design yet. |
| D455 | EXISTS_BUT_UNVERIFIED | Previous project work observed RGB/depth topics, but this workspace has no validated D455 launch, extrinsics, rate, or USB stability record. |
| Lite3 IMU/joints/contact telemetry | EXISTS_BUT_UNVERIFIED | `lite3_telemetry_bridge.cpp` maps receive-only MotionSDK data to `/lite3/imu/data`, `/lite3/joint_states`, contacts. Axes, covariance, timing need testing. |
| Battery/status | EXISTS_AND_TESTED | Watchdog receives port 43897 and separates raw UDP loss from RobotState freshness. |
| Mission/health/events | EXISTS_BUT_UNVERIFIED | `lite3_security_patrol` has pure mission/health classes and JSONL event sink; no direct locomotion. |
| Person detector | MISSING | `PersonDetected` is an interface only. |
| `/cmd_vel` to hardware | MISSING | Existing normalizer is deliberately ROS-only and zero by default. |

## Causal data flow

```text
world -> S2 / D455 / Lite3 IMU -> timestamped ROS topics + frames
      -> measured TF -> odometry + localization -> Nav2/perception
      -> Mission Manager decision -> reviewed control adapter -> Lite3 action
```

Sensor drivers measure. TF explains *where* a measurement was made. Odometry
estimates smooth short-range motion. Localization corrects the global map pose.
Nav2 plans. Perception observes. The Mission Manager decides. Only the reviewed
control adapter may command the robot.

## RPLIDAR S2 role

**SUPPORTED_BY_OFFICIAL_DOCUMENTATION:** SLAMTEC specifies a 360-degree 2-D
scanner, typical 10 Hz scan rate, 32 kHz sample rate, 0.05 m blind range and
model/reflectance-dependent range. Those are sensor limits, not guaranteed
patrol performance.

Recommended target interface:

```text
/scan : sensor_msgs/LaserScan, frame_id=lidar_link
base_link -> lidar_link : measured static transform
```

**ENGINEERING_INFERENCE:** use it first for indoor obstacle observations,
2-D mapping, map localization and a Nav2 obstacle layer. It cannot see objects
above/below its scan plane; glass, mirrors, glossy black material, moving people,
dust, rain and body vibration can degrade it. Dynamic people must not become
permanent map walls.

Mount close to body centre, rigidly, with leg/cable self-occlusion measured in
sitting and standing poses. Record sensor-origin x/y/z and roll/pitch/yaw from
`base_link`; verify scan direction, timestamp age, rate and 10-minute stability.

## D455 role

| Stream | First use | Key limit |
|---|---|---|
| RGB | person/no-person, bounding box, evidence image | darkness, glare, blur, occlusion |
| depth | optional range and near-field geometry | invalid pixels, sunlight/reflectance/texture |
| IMU | angular/orientation cue for validated fusion | acceleration is not position |

**SUPPORTED_BY_OFFICIAL_DOCUMENTATION:** Intel’s D400 documentation describes
D455 depth from about 0.3 m to beyond 4 m depending on lighting, plus a 6-DoF
IMU. **ENGINEERING_INFERENCE:** use RGB+depth for evidence and range, not as the
sole navigation/emergency-obstacle sensor on this moving quadruped.

Use the RealSense driver’s actual frames, not invented rotations:

```text
base_link -> camera_link                     MEASURE_ON_ROBOT
camera_link -> camera_color_optical_frame    driver-provided
camera_link -> camera_depth_optical_frame    driver-provided
```

Before perception: validate RGB/depth/CameraInfo, alignment, timestamp
monotonicity, known-distance depth, USB topology, CPU/GPU load, thermal margin,
and 10-minute stationary/vibration operation.

## TF, odometry, localization and Nav2

```text
map -> odom -> base_link -> lidar_link
                       `-> camera_link -> optical frames
```

**SUPPORTED_BY_OFFICIAL_DOCUMENTATION:** Nav2 requires `map -> odom`,
`odom -> base_link`, and transforms to sensor frames. Localization/SLAM provides
`map -> odom`; a locally continuous estimator provides `odom -> base_link`.
ROS uses x-forward, y-left, z-up SI coordinates.

Never publish competing `odom -> base_link` transforms. Never use a static
`map -> odom` for a moving robot. **REQUIRES_PHYSICAL_TEST:** Lite3 IMU axes,
sensor extrinsics, real odometry quality and robot footprint.

## Odometry candidates

| Candidate | Benefits | Failure modes/cost | Physical test |
|---|---|---|---|
| LiDAR scan matching + IMU | lighting-independent indoor geometry, medium cost | vibration, repeated corridors, people/glass, ICP loss | 60 s static, measured straight/yaw/return, recovery |
| D455 VIO/depth odom + IMU | rich 3-D cues | low light/sun, blur, textureless scenes, USB/compute | known path under lighting and motion variations |
| LiDAR + VIO + IMU | complementary sensing | highest complexity; bad TF/timing poisons fusion | validate each source before fusion |
| saved-map AMCL + local odom + LiDAR obstacles | required shape for repeatable indoor patrol | still needs local odom; map changes | relocalization and blocked-path tests |

No winner is selected. **PROVEN_FROM_CURRENT_PROJECT:** LiDAR ICP is an
experiment only; it previously lost tracking.

## Security perception and event flow

```text
RGB -> detector -> candidate confidence/box
depth + CameraInfo -> optional range
candidate + fresh pose -> PersonDetected -> verification window
Mission Manager -> cancel Nav2 / confirm stopped / capture / log / alert
```

Detection is one model output. Verification checks repeated observations,
confidence, image quality and optional depth plausibility. Decision selects the
response. Perception must never directly command motion.

The first `PersonDetected` contract should contain timestamp, confidence,
bounding box, source frame, image reference, optional depth/range, and pose only
when pose freshness is valid. Existing project code has all except box/source
frame/freshness metadata.

First MVP: `PATROL -> VERIFYING -> OBSERVING (cancel goal + stop confirmation)
-> CAPTURING -> EVENT_RECORDED -> local alert -> WAITING/resume decision`.
Benchmark a small person-capable detector only after D455 CPU/GPU measurements;
model selection is **REQUIRES_PHYSICAL_TEST**.

## Sensor fault contract

| Detect | Safe response | Recovery | Escalate |
|---|---|---|---|
| LiDAR stale/bad TF | cancel goal, zero, `SENSOR_FAULT` | one diagnosed restart | alert/operator |
| D455 disconnect/frozen frames | pause camera-dependent patrol | device recovery + rate/frame checks | alert |
| invalid depth | omit range; retain RGB only | next synchronized frame | sustained issue alert |
| IMU/odom/localization stale | stop autonomous navigation | tested relocalization/restart | operator |
| battery/state stale | never present old value as current | restore telemetry | alert/no long patrol |
| network/control loss | timeout-safe zero/fail-safe behaviour | manual recovery | alert |

**PROVEN_FROM_CURRENT_PROJECT:** watchdog already labels stale battery as
last-known. Exact stop/recovery actions require physical control testing.

## Future environment sensors

Keep hardware independent through:

```text
SensorEvent {type, value, unit, threshold, timestamp, location/frame,
             severity, source_id, freshness, evidence_reference}
```

Temperature, smoke, leak and gas modules create events; Mission Manager decides
whether to observe/alert. They never command velocity.

## Compute, network, logging

| Area | Known | Measure/verify |
|---|---|---|
| S2 | vendor lists model-dependent 5/12 V, >2 W | installed model, supply, cable stability |
| D455 | RGB/depth/IMU consumes USB and compute | USB bus, resolution/FPS, CPU/GPU/RAM/thermals |
| Ethernet | proven robot reachability | packet loss under full stack |
| storage | JSONL local sink exists | image size/retention/free-space/write latency |

Log timestamp, fresh pose, robot/battery state, waypoint/Nav2 result,
detections/confidence, sensor health, recovery action, alert result, and
image/depth references. Do not default to continuous video.

## Mounting checklist

For LiDAR and camera physically record: base reference and sensor origin;
x/y/z; roll/pitch/yaw and convention; axis direction in RViz; rigidity;
self-occlusion; cable routing/strain relief; connector/service access;
environmental protection/cooling; final photos. Do not publish transforms from
a drawing without an observed-wall/known-target check.

## First pilot and practical FMEA

**ENGINEERING_INFERENCE:** choose a flat, dry indoor warehouse aisle or covered
corridor with stable geometry, known Wi-Fi, moderate light, no stairs, short
10–30 m route and low foot traffic. Do not start with outdoor perimeter or open
parking: weather, sunlight, changing geometry and recovery distance compound
unvalidated dependencies.

**Must-have:** measured TF, stable odom/localization, obstacle layer, tested
stop-safe control, 2–3 waypoint patrol, verified person event, evidence capture,
local event log, health monitoring, manual override and stop-on-critical-sensor
loss. Later: identity, continuous video, outdoor patrol, autonomous charging.

| Failure | Severity | Mitigation | Test |
|---|---|---|---|
| robot does not stop | critical | timeout, E-stop, exclusion zone | controlled stop test |
| localization lost | high | cancel/stop/relocalize | kidnapped-robot test |
| person miss/false alarm | high/medium | verification, recorded evaluation | labelled replay |
| obstacle missed | critical | coverage review, conservative speed | obstacle matrix |
| Wi-Fi/alert loss | medium | persist local event before retry | outage test |
| LiDAR/camera/process failure | high | health transition and bounded restart | unplug/kill rehearsal |

## Exact next physical sensor tasks

1. Verify S2 scan rate, orientation, timestamp and 10-minute stability.
2. Measure and validate `base_link -> lidar_link`.
3. Verify D455 RGB/depth/CameraInfo/IMU and USB load for 10 minutes.
4. Measure and validate `base_link -> camera_link`; use driver optical frames.
5. Generate TF tree; remove placeholders/competing publishers.
6. Repeat static/straight/yaw/return/loss tests for LiDAR odometry.
7. Select/no-go an odometry source with recorded acceptance metrics.
8. Validate AMCL and costmaps without autonomous motion.
9. Validate calibrated stop-safe control before connecting Nav2.
10. Add mock, then benchmarked, person detection and event logging.

## Sources

- Nav2 transforms: https://docs.nav2.org/rolling/configuration_and_development/first_time_robot_setup_guide/transformation/setup_transforms/
- Nav2 odometry: https://docs.nav2.org/lyrical/configuration_and_development/first_time_robot_setup_guide/odom/setup_odom/
- SLAMTEC S2: https://www.slamtec.com/en/s2/spec
- Intel D400 datasheet: https://www.intelrealsense.com/wp-content/uploads/2024/10/Intel-RealSense-D400-Series-Datasheet-October-2024.pdf
