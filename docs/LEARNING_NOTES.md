# Learning notes for Raz

These notes teach the causal chain, not just names. Evidence labels:
**PROVEN_FROM_CURRENT_PROJECT**, **SUPPORTED_BY_OFFICIAL_DOCUMENTATION**,
**ENGINEERING_INFERENCE**, and **REQUIRES_PHYSICAL_TEST**.

## LiDAR

**Simple:** A 2-D LiDAR is a spinning tape measure around one horizontal plane.
**Engineering:** `/scan` contains ranges, timestamps and a frame. TF places
each range in `base_link`/`map`; scan matching and costmaps consume it.
**Lite3:** **PROVEN_FROM_CURRENT_PROJECT:** S2 driver and ICP launch exist.
**REQUIRES_PHYSICAL_TEST:** rigid mount, measured `lidar_link`, scan quality and
odometry reliability. **Mistake:** a beautiful scan does not prove Nav2 works.
**Example:** wrong LiDAR yaw makes a straight wall appear rotated in the map.

## RealSense D455

**Simple:** RGB shows what; depth estimates distance; IMU feels movement.
**Engineering:** detections are image pixels; CameraInfo and aligned depth turn
them into rays/ranges. Lighting, glare, USB rate and timestamps matter.
**Lite3:** D455 topics were previously observed, but its mount and reliability
are unverified. Use it first for person evidence/range, not sole navigation.
**Mistake:** treating unaligned depth as the person’s distance.
**Example:** only attach a depth range to a box when RGB/depth timestamps and
alignment are valid.

## IMU

**Simple:** An IMU knows turning and acceleration, not a perfect travelled path.
**Engineering:** acceleration bias grows during integration. Fuse only after
checking axes, units, timestamps and covariance against an independent source.
**Lite3:** telemetry bridge publishes `/lite3/imu/data`; its frame quality needs
testing. **Mistake:** integrate raw acceleration to invent x/y odometry.
**Example:** IMU yaw-rate can support validated LiDAR odometry.

## TF

**Simple:** TF is a map of where every sensor is mounted on the robot.
**Engineering:** target tree is `map -> odom -> base_link -> sensor frames`.
Static mounts are measured; odom moves continuously; localization updates map.
**Lite3:** LiDAR/camera extrinsics are `MEASURE_ON_ROBOT`.
**Mistake:** guessed transforms or two publishers for `odom -> base_link`.
**Example:** a 5 cm transform error shifts every costmap obstacle.

## Odometry

**Simple:** Odom is smooth local motion, even if it slowly drifts.
**Engineering:** it publishes `/odom` and `odom -> base_link`; Nav2 uses its
velocity and local continuity. It may come from LiDAR, VIO, or fusion.
**Lite3:** current ICP is an experiment with earlier tracking loss.
**Mistake:** calling a stationary visualization transform real odometry.
**Example:** local control needs odom between AMCL corrections.

## Localization

**Simple:** Localization says where the robot is in the saved building map.
**Engineering:** AMCL/SLAM normally provide `map -> odom`; they correct global
drift but rely on a usable local motion estimate.
**Lite3:** saved-map AMCL scaffolding exists but has temporary base-frame setup.
**Mistake:** assuming AMCL alone makes a moving robot navigable.
**Example:** after drift, AMCL can correct “near Door A,” while odom stays smooth.

## SLAM

**Simple:** SLAM builds a map while estimating the route travelled.
**Engineering:** scan matching links scans; loop closure corrects accumulated
error. Dynamic humans, vibration and bad TF produce false constraints.
**Lite3:** SLAM Toolbox config exists, but rebuild maps after measured mounts.
**Mistake:** trusting a nice-looking map without repeatability testing.
**Example:** compare start/end pose after a closed indoor loop.

## Nav2

**Simple:** Nav2 chooses and follows a safe path; it is not a sensor driver.
**Engineering:** costmaps use map/odom, TF, footprint and observations; Nav2
outputs `/cmd_vel`, which requires a calibrated timeout-safe hardware adapter.
**Lite3:** configs are templates; `/cmd_vel` is not connected to the robot.
**Mistake:** enable autonomous output before testing independent stop behaviour.
**Example:** inspect costmaps in RViz before a 1–2 m autonomous goal.

## Sensor fusion

**Simple:** Combining senses helps only when their timing and directions agree.
**Engineering:** EKF/UKF uses measurements and uncertainty; wrong frames or
delayed data can make it confidently wrong.
**Lite3:** LiDAR+IMU, D455 VIO+IMU and three-way fusion are candidates only.
**Mistake:** feed every available topic into a filter before validation.
**Example:** validate standalone LiDAR and VIO, then compare a fusion result.

## Person detection

**Simple:** Detection notices a person-shaped image; it does not decide action.
**Engineering:** a detector yields confidence/box; verification uses time,
quality and optional range; an event includes timestamp, evidence and fresh pose.
**Lite3:** only event scaffolding exists. Model selection waits for D455 compute
benchmarks. **Mistake:** send a detector result directly to motion control.
**Example:** two strong frames can create one event and trigger a capture.

## Mission Manager

**Simple:** It is the cautious supervisor that decides patrol, observe, wait or
stop.
**Engineering:** it owns state transitions and calls navigation/alerts through
interfaces; perception and sensor modules only report facts/events.
**Lite3:** pure `mission_core.py` has no locomotion calls.
**Mistake:** couple camera inference to robot command output.
**Example:** `PersonDetected -> cancel goal -> confirm stopped -> capture -> log`.

## Safety and recovery

**Simple:** Safe robots define what happens when information disappears.
**Engineering:** monitor rate, timestamp, TF, odom/localization quality,
battery freshness, process health and command timeout; faults become states.
**Lite3:** watchdog distinguishes raw UDP loss from stale RobotState/battery.
**Mistake:** show a last-known battery as if it were current.
**Example:** stale LiDAR -> cancel Nav2 -> stop -> fault -> one recovery attempt -> alert.

## Full chain

```text
physical world -> sensor -> ROS driver -> topic/frame -> TF
               -> odometry/localization -> Nav2 or perception
               -> Mission Manager -> reviewed control adapter -> Lite3 action
```

At each arrow ask: Is it fresh? Which frame? Who owns the decision? What happens
if it fails? That question sequence is the useful debugging habit.

## Active recall questions

1. Why can `/scan` be healthy while Nav2 fails?
2. What different jobs do `odom -> base_link` and `map -> odom` perform?
3. Why must `base_link -> lidar_link` be measured?
4. Why is raw IMU acceleration not position?
5. What must agree before depth gives a person’s range?
6. Why can an IMU worsen a bad estimator?
7. What is the first safe response to LiDAR loss during patrol?
8. Why is a good SLAM map not proof of repeatable localization?
9. Who should decide whether a person pauses navigation?
10. Distinguish detection, verification and decision.
11. Why is a command timeout essential?
12. What does “last-known battery” mean?
13. Why is an indoor corridor easier than an outdoor first pilot?
14. What should an event log retain?
15. Why only one `odom -> base_link` publisher?
16. What can a LiDAR scan plane miss?
17. Why is normalized velocity not automatically m/s?
18. Why validate sources before fusing them?
19. What must be checked after a D455 USB reconnect?
20. What proof is needed before Nav2 `/cmd_vel` reaches Lite3 hardware?

## Answers

1. It does not prove TF, odom, localization, footprint, costmaps or control.
2. Odom is smooth local motion; map-to-odom globally corrects its drift.
3. TF defines beam origin/orientation; errors shift every observation.
4. Integration accumulates bias rapidly.
5. RGB/depth alignment, CameraInfo, timestamp and optical TF.
6. Wrong axes/timing/covariance inject bad information.
7. Cancel navigation, stop through a tested path, fault, bounded recovery/alert.
8. Maps can hide drift and false constraints; measure repeated return accuracy.
9. Mission Manager after verification and health/context checks.
10. One observation; evidence over time; then a policy response.
11. It prevents stale commands/dead processes continuing motion.
12. It is historical because fresh RobotState stopped arriving.
13. It reduces weather, terrain, lighting, map-change and recovery variables.
14. Time, fresh pose, state/battery, waypoint/Nav2 result, evidence, health/actions.
15. Two parents make TF pose ambiguous and invalid.
16. Objects above/below its plane and difficult reflectance cases.
17. It is a policy scale and needs measured physical calibration.
18. Fusion cannot repair unknown frame, timing or quality errors.
19. Rate, timestamps, frame IDs, alignment, depth quality and device health.
20. Measured TF/footprint, trusted odom/localization, obstacle tests and calibrated stop-safe control.
