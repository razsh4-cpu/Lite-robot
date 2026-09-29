# Known-good Lite3 product baseline

Baseline name: `LITE3_HIGH_LEVEL_NAV2_DAY2_2026-09-27`

This is the regression reference for the current HIGH-LEVEL product path. It
does not include the separate low-level R&D path and does not expand the ODD.

## Recorded software state

| Artifact | Commit | Meaning |
|---|---|---|
| Product code import | `abf9900` | Lite3 HIGH-LEVEL ROS2, localization, Nav2, safety, C2 and operator stack captured in Git |
| Day-2 closeout | `1462847` | Evidence/status documentation for the accepted physical system |
| Robot Interface Phase 1 | `0c2a742` | Pure generic contracts/Lite3 mapping/config foundation; no runtime replacement |
| Architecture Baseline | `7d5bc92` | Architecture/source-of-truth expansion; no product runtime change |
| Platform foundation | `bf223eb` | Baseline, tests, experiments, safety/failure, requirements and workflow documentation |
| Built-in obstacle CLI | `7ae1688` | Reusable guarded operator test and bounded diagnostic snapshots; offline tested only as a new wrapper |
| Dormant Day-3/D455 preparation | `b6848f9` | Pure Mission contracts and on-demand D455 RViz profile; no runtime activation |

The exact installed Mini-PC package hashes at the instant of the physical run
were not captured as a release manifest. Therefore `abf9900` plus the closeout
evidence is the strongest repository baseline, not a cryptographic deployment
attestation. Creating versioned deployment manifests remains planned debt.

## Physically demonstrated baseline

Evidence classification: `PHYSICALLY PROVEN` unless a bullet states otherwise.

- supported Stand and telemetry-confirmed standing;
- laptop Xbox/C2 manual command path and safe release;
- RPLIDAR, mapping and `Home_Map` saved-map localization;
- AMCL/navigation gate with three consecutive confidence samples ≥80%;
- Nav2 planning/controller through `/cmd_vel → AUTONOMY → arbiter → HIGH-LEVEL`;
- forward, lateral and yaw motion through the vendor gait product path;
- real chair detection in LiDAR/costmaps and right-side avoidance;
- accepted Nav2 path approximately 1.47 m;
- `NavigateToPose` result `SUCCEEDED` (`error_code=0`);
- final localization approximately 95.4%;
- robot stopped standing, AUTONOMY stopped/released and final
  `COMMAND_SOURCE=NONE`.

Attempt 1 travelled approximately 1.64 m and avoided the chair but was
interrupted by Mini-PC power loss/reboot; it is useful evidence, not a completed
goal PASS. Attempt 2 above is the accepted baseline.

## Offline/software proven

- vendor-neutral Robot Interface contracts and Lite3 telemetry/state mapping;
- configuration loading, capability/limit validation and architecture ownership
  invariants;
- obstacle-test approval, status, cancel, override cleanup, packaging and
  diagnostic-snapshot behavior through mocks/static tests;
- dormant Mission target/lifecycle contracts and unconfigured registry;
- current complete offline regression: 243 tests passed on 2026-09-29 (the increase from 242 adds the independent 180-second override-consumer assertion).

These results prove deterministic software behavior only, not installation, DDS,
physical clearance, sensor alignment or hardware response.

## Implemented but not physically validated

- the reusable `nav test obstacle` operator wrapper as a new installed workflow
  (its underlying navigation/avoidance path is physically proven above);
- dedicated `robot down` CLI acceptance;
- explicit relocalization CLI physical maneuver and cleanup as one end-to-end run;
- clean Mini-PC installation/import of the latest obstacle-test package;
- D455 map/scan/robot/path/point-cloud RViz profile; camera-to-base TF remains unconfigured and requires live calibration;
- Mission contracts (execution deliberately disabled).

## Planned

- active Day-3 Mission Manager and `go`/status/cancel operator commands;
- validated named-location coordinates and ad-hoc Mission integration;
- unified bounded experiment recorder/black box;
- D455 perception or Nav2 costmap integration;
- simulation adapter, HIL/fault injection, CI/release installer, backup/restore,
  update/rollback, security hardening and fleet/multi-robot operation.

## Baseline operational parameters

- robot body approximately 0.610 × 0.370 m;
- Nav2 footprint 0.710 × 0.470 m;
- `footprint_padding=0.0 m`;
- `inflation_radius=0.30 m`, cost scaling 4.0;
- AUTONOMY limits: 0.10 m/s forward/back, 0.05 m/s lateral, 0.20 rad/s yaw;
- command freshness watchdog: 300 ms;
- localization acceptance: ≥0.80 for three consecutive samples;
- navigation battery gate: fresh and ≥25%;
- persistent HIGH-LEVEL is the sole UDP 43897 receiver and `/odom` owner.

## Required regression invariants

1. No duplicate UDP receiver, odometry/TF owner, arbiter or robot runtime.
2. Boot/source default is `NONE`; no restored motion or authorization.
3. Xbox/laptop loss cannot stop persistent heartbeat/telemetry.
4. Stale command/sensor/localization faults stop or block motion as documented.
5. Nav2 never bypasses AUTONOMY and the protected HIGH-LEVEL boundary.
6. Existing maps, TF extrinsics, localization tuning and limits are not changed
   merely to make a test pass.

Primary evidence: `docs/HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md` and
`onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md`.
