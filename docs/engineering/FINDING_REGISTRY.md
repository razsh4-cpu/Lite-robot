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
| [FINDING-20260913-001](findings/FINDING-20260913-001-motion-sdk-ownership-unconfirmed.md) | CURRENT | ROBOT_CONTROL | MotionSDK ownership request has no authoritative acknowledgement |
| [FINDING-20260913-002](findings/FINDING-20260913-002-posture-dependent-joint-readings.md) | HISTORICAL | ROBOT_CONTROL | Joint readings changed after normal lying preparation without mapping edits |
| [FINDING-20260914-001](findings/FINDING-20260914-001-vendor-manual-axis-protocol.md) | CURRENT | ROBOT_CONTROL | Vendor manual-axis locomotion requires full source-qualified SimpleCMD codes |
| [FINDING-20260914-002](findings/FINDING-20260914-002-direct-onnx-not-pilot.md) | DO_NOT_USE | ROBOT_CONTROL | Direct ONNX MotionSDK locomotion was not a reliable pilot path |
| [FINDING-20260917-001](findings/FINDING-20260917-001-atomic-stand-authorization.md) | RESOLVED | ROBOT_CONTROL | Time-bounded authorization and action must be atomic |
| [FINDING-20260917-002](findings/FINDING-20260917-002-absolute-stand-hold-deadline.md) | RESOLVED | ROBOT_CONTROL | Renewable health permits must not extend an absolute action deadline |
| [FINDING-20260918-001](findings/FINDING-20260918-001-low-level-foot-force-unavailable.md) | KNOWN_ISSUE | SENSORS | Low-level validation foot-force channels were zero |
| [FINDING-20260918-002](findings/FINDING-20260918-002-long-action-permit-lifecycle.md) | HISTORICAL | ROBOT_CONTROL | Longer low-level actions exposed permit-lifecycle ambiguity |
| [FINDING-20260921-001](findings/FINDING-20260921-001-simulation-contact-model-ambiguity.md) | DO_NOT_USE | ROBOT_CONTROL | MuJoCo contact geometry can create false unloading conclusions |
| [FINDING-20260927-004](findings/FINDING-20260927-004-odom-publication-rate.md) | RESOLVED | ODOMETRY | Unbounded HIGH-LEVEL odometry publication overloaded ROS executors |
| [FINDING-20261002-001](findings/FINDING-20261002-001-autonomy-velocity-qos-compatibility-preserves-independent-watchdog.md) | RESOLVED | ROS2 | AUTONOMY velocity QoS compatibility preserves independent watchdog |
| [FINDING-20261002-002](findings/FINDING-20261002-002-command-source-markers-do-not-establish-real-ownership.md) | KNOWN_ISSUE | SAFETY | Command-source markers do not establish real ownership |
| [FINDING-20261002-003](findings/FINDING-20261002-003-installed-executable-helpers-also-need-an-importable-module.md) | RESOLVED | DEPLOYMENT | Installed executable helpers also need an importable module |
| [FINDING-20261002-004](findings/FINDING-20261002-004-localization-confidence-is-a-custom-scan-to-map-match-score.md) | CURRENT | LOCALIZATION | Localization confidence is a custom scan-to-map match score |
| [FINDING-20261002-005](findings/FINDING-20261002-005-independent-body-frame-strafe-physical-proof-remains-incomplete.md) | KNOWN_ISSUE | ROBOT_CONTROL | Independent body-frame strafe physical proof remains incomplete |
| [FINDING-20261002-006](findings/FINDING-20261002-006-zero-yaw-navfn-poses-need-path-tangent-footprint-diagnostics.md) | RESOLVED | NAVIGATION | Zero-yaw NavFn poses need path-tangent footprint diagnostics |
| [FINDING-20261002-007](findings/FINDING-20261002-007-on-demand-unused-perception-reduced-recorded-mini-pc-load.md) | CURRENT | PERFORMANCE | On-demand unused perception reduced recorded Mini-PC load |
| [FINDING-20261002-008](findings/FINDING-20261002-008-temporary-high-level-posture-leases-need-neutral-continuity.md) | HISTORICAL | SAFETY | Temporary HIGH-LEVEL posture leases need neutral continuity |
| [FINDING-20261002-009](findings/FINDING-20261002-009-relocalization-requires-explicit-approval-before-ownership-or-motion.md) | RESOLVED | SAFETY | Relocalization requires explicit approval before ownership or motion |
| [FINDING-20261002-010](findings/FINDING-20261002-010-battery-connection-spark-and-suspected-dc-dc-damage-need-separate-closure.md) | KNOWN_ISSUE | HARDWARE | Battery connection spark and suspected DC-DC damage need separate closure |
| [FINDING-20261002-011](findings/FINDING-20261002-011-updated-gateway-source-must-become-the-running-deployed-process.md) | RESOLVED | DEPLOYMENT | Updated gateway source must become the running deployed process |
| [FINDING-20261002-012](findings/FINDING-20261002-012-mqtt-edge-namespace-translation-is-part-of-the-transport-contract.md) | RESOLVED | MQTT | MQTT edge namespace translation is part of the transport contract |
| [FINDING-20261002-013](findings/FINDING-20261002-013-configured-lidar-extrinsics-are-not-complete-calibration-metrology.md) | HISTORICAL | TF | Configured LiDAR extrinsics are not complete calibration metrology |
| [FINDING-20261002-014](findings/FINDING-20261002-014-reported-lithium-charging-fire-has-no-recorded-safety-closure.md) | KNOWN_ISSUE | HARDWARE | Reported lithium charging fire has no recorded safety closure |
| [FINDING-20261002-080](findings/FINDING-20261002-080-nav2-cpu-compatibility-fix-exists-deployed-but-not-on-integratio.md) | KNOWN_ISSUE | DEPLOYMENT | Nav2 CPU compatibility fix exists deployed but not on integration branch |
| [FINDING-20261002-081](findings/FINDING-20261002-081-idle-odometry-fix-exists-deployed-but-not-on-integration-branch.md) | KNOWN_ISSUE | DEPLOYMENT | Idle odometry fix exists deployed but not on integration branch |
| [FINDING-20261002-082](findings/FINDING-20261002-082-deployed-control-guards-and-site-configuration-differ-from-integ.md) | KNOWN_ISSUE | DEPLOYMENT | Deployed control guards and site configuration differ from integration |
| [FINDING-20261002-083](findings/FINDING-20261002-083-legacy-status-domain-and-advertised-capabilities-are-not-product.md) | KNOWN_ISSUE | DEPLOYMENT | Legacy status domain and advertised capabilities are not product readiness |
| [FINDING-20261002-084](findings/FINDING-20261002-084-retained-bags-and-clock-metadata-impose-evidence-limits.md) | CURRENT | DEPLOYMENT | Retained bags and clock metadata impose evidence limits |
| [FINDING-20261002-015](findings/FINDING-20261002-015-historical-normalized-vendor-axes-are-not-si-calibration.md) | CURRENT | ROBOT_CONTROL | Historical normalized vendor axes are not SI calibration |
| [FINDING-20261002-016](findings/FINDING-20261002-016-fresh-scan-and-odometry-do-not-prove-responsive-amcl.md) | HISTORICAL | ROS2 | Fresh scan and odometry do not prove responsive AMCL |
| [FINDING-20261002-017](findings/FINDING-20261002-017-active-localization-does-not-mean-nav2-servers-are-available.md) | RESOLVED | NAVIGATION | Active localization does not mean Nav2 servers are available |

## Additional source-bound historical captures

- [FINDING-20261002-085](findings/FINDING-20261002-085-wi-fi-name-configuration-baseline.md) — `HIST-024`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-086](findings/FINDING-20261002-086-inert-first-stand-failure-recovery.md) — `HIST-026`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-087](findings/FINDING-20261002-087-original-vendor-controller-transport-investigation.md) — `HIST-032`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-088](findings/FINDING-20261002-088-real-body-shift-measured-speed-guard-abort.md) — `HIST-037`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-089](findings/FINDING-20261002-089-body-only-30-60-90-percent-safe-scale-calibration-plan.md) — `HIST-044`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-090](findings/FINDING-20261002-090-nav2-package-dns-install-failure.md) — `HIST-048`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-091](findings/FINDING-20261002-091-supported-stand-rms-only-velocity-loss-persistence-correct.md) — `HIST-066`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-092](findings/FINDING-20261002-092-duplicate-rviz-config-launcher-disagreement.md) — `HIST-083`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-093](findings/FINDING-20261002-093-distro-paho-compatibility-defect-shim.md) — `HIST-084`, retrospective; raw evidence limitations retained.
- [FINDING-20261002-094](findings/FINDING-20261002-094-operator-python-helper-lacked-sourced-ros-environment.md) — `HIST-089`, retrospective; raw evidence limitations retained.

- [FINDING-20261002-095](findings/FINDING-20261002-095-field-fix-concepts-reconciled-through-product-owners.md) — current safe offline continuation; no physical acceptance.
