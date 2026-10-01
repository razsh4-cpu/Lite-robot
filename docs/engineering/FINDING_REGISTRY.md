# Engineering-finding registry

| ID | Status | Area | Finding |
|---|---|---|---|
| [FINDING-20260915-001](findings/FINDING-20260915-001-icp-null-guess.md) | DO_NOT_USE | ODOMETRY | ICP rejection enters a null-guess cascade |
| [FINDING-20260927-001](findings/FINDING-20260927-001-systemd-active-ros-dead.md) | RESOLVED | ROS2 | systemd active is not ROS readiness |
| [FINDING-20260927-002](findings/FINDING-20260927-002-rtl8851bu.md) | KNOWN_ISSUE | NETWORKING | rtl8851bu evidence remains a separate open risk |
| [FINDING-20260927-003](findings/FINDING-20260927-003-obstacle-snapshot.md) | RESOLVED | NAVIGATION | Clearance analysis requires a reconstructable snapshot |
| [FINDING-20260928-001](findings/FINDING-20260928-001-active-map-identity.md) | RESOLVED | LOCALIZATION | Verify active map before interpreting confidence |
| [FINDING-20260929-001](findings/FINDING-20260929-001-source-of-truth.md) | RESOLVED | DEPLOYMENT | Deployment was hybrid, not one authoritative copied tree |
| [FINDING-20260930-001](findings/FINDING-20260930-001-command-authority.md) | CURRENT | SAFETY | One arbiter/UDP owner; NOMAD must not bypass it |
| [FINDING-20261001-001](findings/FINDING-20261001-001-exporter-process-leak.md) | RESOLVED | PERFORMANCE | Timed-out probes leaked ROS child processes |
| [FINDING-20261001-002](findings/FINDING-20261001-002-mqtt-bridge-ip.md) | RESOLVED | MQTT | Stale central-broker address stopped live status |
| [FINDING-20261001-003](findings/FINDING-20261001-003-firefox-gamepad.md) | CURRENT | XBOX | Linux joystick presence does not imply browser Gamepad visibility |
| [FINDING-20261001-004](findings/FINDING-20261001-004-vendor-state-98.md) | CURRENT | ROBOT_CONTROL | Vendor basic-state 98 is valid non-fault telemetry |
