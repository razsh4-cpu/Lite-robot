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
