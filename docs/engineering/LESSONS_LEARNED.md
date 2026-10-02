# Lessons learned

| What happened | Why | Fix / current status | Do not repeat |
|---|---|---|---|
| AMCL/Map Server looked active but were unusable | process state was mistaken for ROS readiness | ordered readiness and bounded lifecycle recovery; [finding](findings/FINDING-20260927-001-systemd-active-ros-dead.md) | gate on real topics/lifecycle/TF/freshness |
| ICP lost one scan then never recovered | threshold rejection fed a null guess to later registrations | retained as R&D, not product authority; [finding](findings/FINDING-20260915-001-icp-null-guess.md) | lower thresholds or change ownership without replay/live proof |
| An autonomous run avoided the chair but was not a PASS | power loss prevented terminal-result/release evidence | preserve both [partial](tests/TEST-20260927-001-chair-avoidance-interrupted.md) and [PASS](tests/TEST-20260927-002-chair-avoidance-pass.md) | erase failed/partial runs after success |
| 8 mm clearance could not be audited later | live inputs and limiting pose/cell were not retained together | bounded snapshots; [finding](findings/FINDING-20260927-003-obstacle-snapshot.md) | publish precision without evidence |
| Localization stayed below gate in a new site | old `Home_Map` was selected | display/record active map; [finding](findings/FINDING-20260928-001-active-map-identity.md) | tune before checking map identity |
| Mini-PC seemed like a network failure while ping survived | exporter child processes accumulated | terminate/reap groups; [finding](findings/FINDING-20261001-001-exporter-process-leak.md) | blame Wi-Fi before resource evidence |
| NOMAD showed `never_seen` | edge bridge used stale C&C IP | trace/configure all MQTT hops; [finding](findings/FINDING-20261001-002-mqtt-bridge-ip.md) | infer robot failure from registry state alone |
| Firefox showed disconnected while Linux had js0 | Gamepad API activation/event/mapping differs from kernel visibility | focused interaction + connection polling; [finding](findings/FINDING-20261001-003-firefox-gamepad.md) | weaken deadman to hide browser bugs |
| Deployment copies disagreed | runtime was a hybrid of installed units and source trees | hash/consumer reconciliation; [finding](findings/FINDING-20260929-001-source-of-truth.md) | bulk-copy deployed/generated trees |
| Permission layers risked conflation | operator lease, reservation, and robot owner answer different questions | keep them separate; [finding](findings/FINDING-20260930-001-command-authority.md) | let UI authority bypass arbiter |

## Retrospective and deployment lessons

| Event | Durable lesson | Canonical record |
|---|---|---|
| Active services, absent new DDS inputs | Check actual graph, lifecycle, freshness, and TF; preserve pending unit installation | [TEST-20261002-001](tests/TEST-20261002-001-dds-recovery-with-incomplete-persistent-deployment.md) |
| Nav2 intent stalled at AUTONOMY | Verify compatible QoS and preserve independent watchdog | [FINDING-20261002-001](findings/FINDING-20261002-001-autonomy-velocity-qos-compatibility-preserves-independent-watchdog.md) |
| Ghost marker survived owner exit | Marker, kernel lock, and live process are different facts | [FINDING-20261002-002](findings/FINDING-20261002-002-command-source-markers-do-not-establish-real-ownership.md) |
| Executable helper failed Python import | Build and executable presence do not prove installed module availability | [FINDING-20261002-003](findings/FINDING-20261002-003-installed-executable-helpers-also-need-an-importable-module.md) |
| Curve/detour interpreted as strafe | Record command path, units, body yaw, and per-axis evidence | [FINDING-20261002-005](findings/FINDING-20261002-005-independent-body-frame-strafe-physical-proof-remains-incomplete.md), [FINDING-20261002-015](findings/FINDING-20261002-015-historical-normalized-vendor-axes-are-not-si-calibration.md) |
| Custom score exceeded gate despite pose offset | Match fraction is not official AMCL probability or metrology | [FINDING-20261002-004](findings/FINDING-20261002-004-localization-confidence-is-a-custom-scan-to-map-match-score.md) |
| Current source differed from deployed fixes/guards | Reconcile consumers, hashes, policy, and safe rollback file by file | [Mini-PC audit](MINIPC_DEPLOYED_STATE_AUDIT.md) |
| Spark and later fire | Preserve separate incidents, UNKNOWN causes, and missing safety acceptance | [FINDING-20261002-010](findings/FINDING-20261002-010-battery-connection-spark-and-suspected-dc-dc-damage-need-separate-closure.md), [FINDING-20261002-014](findings/FINDING-20261002-014-reported-lithium-charging-fire-has-no-recorded-safety-closure.md) |

## Subsequent safe source closure — 2026-10-02

The read-only deployed snapshot remains unchanged. CPU-compatible controller selection and dispatch-bound idle odometry have subsequently been reconciled through existing SABLE owners, with offline tests only (TEST-20261002-106 / FINDING-20261002-095). Driver scaling diagnostics, bounded forwarding, UI evidence and passive validation preparation add observability without calibration changes. These are not deployed or physically proven. Direct strafe remains UNVALIDATED. See SAFE_AUTONOMOUS_CLOSURE.md for current counts, checks and blockers. Five additional supervised records TEST-20261002-107..111 are PLANNED ONLY, no new historical experiments; each physical matrix item is evaluated individually.
