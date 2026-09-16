# Lite3 security-patrol roadmap

## Intended architecture

```text
Lite3VelocityController (explicit SDK ownership)
  → ROS 2 /cmd_vel bridge (calibrated conversion)
  → Nav2 controller
  → map → odom → base_link → {lidar_link,camera_link}
  → patrol manager → mission manager
  ← person detector / health watchdog / navigation results
  → local event log / alert backend
```

The policy may internally produce joint commands. Application, ROS, Nav2, and
mission code must never create joint commands directly.

## Status

| Component | Status | Notes |
|---|---|---|
| Ethernet reachability | PROVEN | Direct robot network previously verified. |
| Lite3 RL policy path | IMPLEMENTED_OFFLINE | Exact reference commit is prepared for x86 with explicit ownership. |
| Software velocity source | IMPLEMENTED_OFFLINE | Normalized values only; no physical unit calibration. |
| ROS `/cmd_vel` normalization | IMPLEMENTED_OFFLINE | ROS-only output `/lite3/normalized_cmd_vel`; not connected to SDK yet. |
| RPLIDAR S2 driver | READY_FOR_TEST | Existing `sllidar_ros2`; live health must be revalidated after mounting. |
| D455 driver | READY_FOR_TEST | Existing RealSense setup; mounting and frame IDs need validation. |
| TF extrinsics | BLOCKED_BY_HARDWARE | `base_link→lidar_link` and `base_link→camera_link` are MEASURE_ON_ROBOT. |
| LiDAR ICP odometry | READY_FOR_TEST | Existing launch/config; prior physical tracking was insufficient. |
| Visual/depth odometry | NOT_STARTED | Candidate only. |
| AMCL/map/Nav2 | IMPLEMENTED_OFFLINE | Existing map/localization/planner scaffolds; waits for trustworthy odometry/TF. |
| Patrol/mission/event models | IMPLEMENTED_OFFLINE | Pure mock-tested decisions; no direct locomotion calls. |
| Person detection | NOT_STARTED | Interface only; select model after camera validation. |
| Alert backend | IMPLEMENTED_OFFLINE | Local JSONL mock sink; no cloud dependency. |

## Hardware prerequisites

1. Verify power/battery/telemetry and an original controller or E-stop.
2. Validate fresh MotionSDK feedback before SDK ownership is explicitly requested.
3. Measure sensor extrinsics; do not publish guessed static transforms.
4. Establish reliable odom before AMCL/Nav2.
5. Calibrate velocity conversion from normalized policy input to physical response.

## Sensor and TF validation checklist

### RPLIDAR S2

- Verify `/scan` frequency, timestamp monotonicity, `frame_id`, ranges, and dropped scans.
- Confirm scan orientation and visualize in RViz.
- Record USB/serial device identity and a 10-minute stability sample.

### RealSense D455

- Verify RGB, depth, both camera-info streams, and optional IMU streams.
- Check image/depth alignment, timestamp behavior, frame IDs, USB bandwidth, and 10-minute stability.

### Required physical measurements

For each sensor, record from `base_link` origin:

- x/y/z translation in metres;
- roll/pitch/yaw in radians or degrees with a stated convention;
- axis directions and the point used as the sensor frame origin;
- mounting rigidity and whether vibration isolation is present.

Publish transforms only after these values are measured and reviewed.

## Odometry experiment plan

Compare LiDAR scan matching, D455 visual/depth odometry, and optional IMU fusion.
For each candidate record 60-second static drift, measured straight-line error,
measured rotation error, return-to-start error, output rate, latency, tracking
losses, and recovery behavior. The candidate can feed `odom→base_link` only
after those measurements meet the project’s chosen acceptance threshold.

## Nav2 readiness criteria

- Measured footprint and inflation parameters.
- Valid `map→odom→base_link` TF tree with no competing publishers.
- Stable `/odom`, scan obstacle layer, and localization for the full test run.
- `/cmd_vel` bridge calibrated, timeout-safe, and independently stop-tested.
- Test progression: rotation/short translation → 1–2 m goal → obstacle → multi-waypoint.

## Patrol and security readiness criteria

- Patrol manager owns waypoint order/retry/timeout only.
- Mission manager owns decisions; perception never publishes locomotion commands.
- Person event includes confidence, timestamp, image reference, depth if available,
  and robot pose if localization is valid.
- Alert backend persists a local structured event before any remote integration.

## Recovery boundaries

Localization loss, navigation failure, sensor loss, network loss, command timeout,
low battery, and emergency stop are represented as mission/health events. Exact
robot recovery actions remain BLOCKED_BY_HARDWARE until their effects are tested.

## Pilot KPIs and endurance sequence

Measure command/stop reliability, odometry/localization error, waypoint success,
obstacle avoidance, detection precision/recall, alert latency, recovery success,
network uptime, battery/runtime, and crash-free operation. Run staged tests at
5 min, 15 min, 30 min, 1 h, 2 h, and 4 h; advance only after the previous stage
has a reviewed result.

## Exact next hardware test

With the robot secured and E-stop available: validate passive MotionSDK telemetry
only. Do not acquire control, stand, or move until timestamps and joint/IMU data
are fresh and consistent.

## Sensor architecture review

See [SENSOR_SECURITY_ARCHITECTURE.md](SENSOR_SECURITY_ARCHITECTURE.md) for the
evidence-labelled sensor audit, TF/odometry plan, perception boundary, recovery
contract, mounting checklist, pilot scope and FMEA. See
[LEARNING_NOTES.md](LEARNING_NOTES.md) for Raz’s teaching notes and active recall.

The next autonomy prerequisite remains: validate S2/D455 topics, measured static
extrinsics, and a trustworthy `odom -> base_link` source before enabling Nav2
motion.
