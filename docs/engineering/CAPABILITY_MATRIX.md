# Capability and evidence matrix

| Capability | Current implementation | Evidence | Last validated | Robot | Software SHA | Known issue / limitation | Primary evidence |
|---|---|---|---|---|---|---|---|
| HIGH-LEVEL runtime | Persistent sole vendor UDP/odom owner | LIVE_STATIC_PROVEN | 2026-09-27 | robot_01 | `abf9900` baseline | repeated-boot soak useful | [closeout](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md) |
| Local Xbox | Existing lease-gated source | HISTORICAL_CLAIM | 2026-09 | UNKNOWN | UNKNOWN | exact session evidence incomplete | [test catalog](../testing/TEST_CATALOG.md) |
| Laptop Xbox/C2 | Exclusive `LAPTOP_XBOX` path | PHYSICALLY_PROVEN | 2026-09-27 | robot_01 | `abf9900` baseline | not proof of NOMAD browser adapter | [TEST-20260927-004](tests/TEST-20260927-004-laptop-xbox-manual.md) |
| NOMAD remote Xbox | Protected Phase-3C adapter/UI prepared | OFFLINE_PROVEN | 2026-10-01 | robodog_01 | Lite `35c8173`; NOMAD `76928a7` | physical test pending | [planned test](tests/TEST-20261001-002-phase3c-xbox-physical.md) |
| Command arbiter | NONE/LOCAL_XBOX/LAPTOP_XBOX/AUTONOMY exclusive | LIVE_STATIC_PROVEN | 2026-09-27 | robot_01 | `abf9900` | ghost-marker parity remains regression target | [finding](findings/FINDING-20260930-001-command-authority.md) |
| Safety watchdog | 300 ms guarded source freshness | LIVE_STATIC_PROVEN | 2026-09-27 | robot_01 | `abf9900` | Phase-3C physical release pending | [baseline](../testing/KNOWN_GOOD_BASELINE.md) |
| Mapping/SLAM | Operator workflow and saved maps | PHYSICALLY_PROVEN | 2026-09-27 | robot_01 | `abf9900` | map identity must be explicit | [test catalog](../testing/TEST_CATALOG.md) |
| Localization/AMCL | saved hypothesis + global fallback; 80% ×3 gate | LIVE_STATIC_PROVEN | 2026-09-27 | robot_01 | `abf9900` | physical ambiguity can require short manual motion | [TEST-20260927-003](tests/TEST-20260927-003-home-map-localization.md) |
| Product odometry | HIGH-LEVEL telemetry `/odom`, bounded rate | PHYSICALLY_PROVEN | 2026-09-27 | robot_01 | `abf9900` | ICP R&D is not product authority | [baseline](../testing/KNOWN_GOOD_BASELINE.md) |
| TF | map→odom→base_link→lidar_link single ownership | LIVE_STATIC_PROVEN | 2026-09-27 | robot_01 | `abf9900` | D455 extrinsic remains separate | [configuration](../architecture/CONFIGURATION_CALIBRATION_DATA.md) |
| Nav2 single goal | planner/controller via AUTONOMY | PHYSICALLY_PROVEN | 2026-09-27 | robot_01 | `abf9900` | preserve limits/gates | [chair PASS](tests/TEST-20260927-002-chair-avoidance-pass.md) |
| Obstacle avoidance | LiDAR→costmaps→Nav2, right-side chair | PHYSICALLY_PROVEN | 2026-09-27 | robot_01 | `abf9900` | snapshot required for clearance claims | [chair PASS](tests/TEST-20260927-002-chair-avoidance-pass.md) |
| RPLIDAR | `/scan`, mapping/localization/2D obstacles | LIVE_STATIC_PROVEN | 2026-09-27 | robot_01 | `abf9900` | single driver required | [test catalog T008](../testing/TEST_CATALOG.md) |
| D455 | on-demand driver/RViz preparation | IMPLEMENTED BUT UNVALIDATED | UNKNOWN | robot_01 | `b6848f9` | camera extrinsic/perception integration pending | [known-good baseline](../testing/KNOWN_GOOD_BASELINE.md) |
| NOMAD status | vendor-neutral status via MQTT/FleetRegistry | LIVE_STATIC_PROVEN | 2026-10-01 | robodog_01 | NOMAD `a0cda36` | gateway online must not imply robot ready | [Phase-3B record](tests/TEST-20261001-001-nomad-phase3b-live-static.md) |
| NOMAD authority | operator lease + separate reservation | OFFLINE_PROVEN | 2026-09-30 | robodog_01 | NOMAD `fa6810e` | physical ownership intentionally separate | [Phase-2 record](tests/TEST-20260930-002-nomad-phase2-authority.md) |
| Mission / Patrol | motion-blocked mock/preview only | OFFLINE_PROVEN | 2026-10-01 | robodog_01 | NOMAD `c3c3e96` | physical execution pending | [NOMAD non-motion MVP](../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md) |
| Multi-robot isolation | status/lease/reservation/mock isolation | OFFLINE_PROVEN | 2026-09-30 | fixture fleet | NOMAD `4561e74` | live fleet not proven | [Phase-3A record](tests/TEST-20260930-003-nomad-phase3a-mock.md) |
| Mini-PC reliability | headless/on-demand workload; exporter leak fixed | PARTIAL | 2026-10-01 | robot_01 | `e396f55` | rtl8851bu soak open | [exporter finding](findings/FINDING-20261001-001-exporter-process-leak.md) |
