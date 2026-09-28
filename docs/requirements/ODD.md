# Initial Operational Design Domain (ODD)

This ODD states only what current evidence supports. Anything not explicitly
included is outside the validated domain or **TO BE VALIDATED**.

## Supported domain

| Dimension | Current supported boundary |
|---|---|
| Environment | Known indoor site represented by a selected, validated static 2D map |
| Surface | Relatively flat, firm, traversable floor suitable for the Lite3 vendor gait |
| Localization | Live `/scan`, `/odom`, required TF and AMCL; three consecutive confidence samples ≥80% before navigation |
| Obstacles | Static or slowly changing obstacles that produce reliable RPLIDAR returns and leave sufficient footprint/inflation clearance |
| Motion | Conservative limits: 0.10 m/s forward/backward, 0.05 m/s lateral, 0.20 rad/s yaw |
| Footprint | Configured Nav2 polygon approximately 0.710 × 0.470 m for a measured body approximately 0.610 × 0.370 m; padding 0; inflation radius 0.30 m |
| Compute | Healthy onboard Mini-PC in headless mode with fresh HIGH-LEVEL telemetry, LiDAR, odometry and safety monitoring |
| Power | Robot and Mini-PC power sufficient for the test/mission; navigation battery telemetry fresh and at least the current 25% gate |
| Command state | Robot standing, `COMMAND_SOURCE=NONE` before AUTONOMY acquisition, no competing manual source |
| Supervision | Onsite operator and abort capability required for current physical engineering validation; laptop optional for onboard runtime |
| Connectivity | Internet/cloud not required; robot private link and onboard services required; laptop/C2 network required only for remote supervision/manual input |

## Outside the current validated ODD

- stairs, steps, ledges or deliberate drop-offs;
- rough, deformable, slippery or steep terrain;
- outdoor weather, rain, dust exposure or extreme lighting/temperature;
- dense crowds, people-contact operation or high-speed dynamic obstacles;
- glass/low-reflectivity objects not reliably detected by the RPLIDAR;
- autonomous charging/docking;
- unsupervised long-duration patrol;
- operation below required localization, sensor, telemetry or battery gates;
- cloud-dependent mission control;
- low-level learned gait/ONNX locomotion in the product path.

## TO BE VALIDATED

- maximum safe floor slope and floor discontinuity;
- minimum repeatable corridor/doorway clearance across tracking uncertainty;
- maximum mission duration and thermal/resource headroom under sustained Nav2;
- dynamic obstacle speed and detection/replanning envelope;
- LiDAR performance with glass, dark, narrow or low objects;
- Wi-Fi management-link reliability over repeated boots and mission-length soak;
- recovery behavior for each live fault-injection case;
- D455 and ultrasonic roles, ranges, failure modes and safety credit;
- multi-robot and remote-control-center operating constraints.

Expanding this ODD requires a defined experiment, evidence, regression impact
and updated acceptance criteria. Parameter changes alone do not expand it.
