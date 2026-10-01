# Known bad / do not repeat

- **Experimental ICP as product odometry without closing loss behavior.** A rejected scan can enter a null-guess cascade. See [FINDING-20260915-001](findings/FINDING-20260915-001-icp-null-guess.md).
- **Readiness from `systemd active`.** Verify real ROS graph, lifecycle, freshness, and TF. See [FINDING-20260927-001](findings/FINDING-20260927-001-systemd-active-ros-dead.md).
- **Periodic subprocess probes without process-group cleanup.** This produced resource exhaustion resembling network failure. See [FINDING-20261001-001](findings/FINDING-20261001-001-exporter-process-leak.md).
- **Stale hard-coded broker/C&C IP.** Trace every MQTT hop and configure the destination. See [FINDING-20261001-002](findings/FINDING-20261001-002-mqtt-bridge-ip.md).
- **Wrong-map tuning.** Confirm active map before AMCL/extrinsic/origin changes or overrides. See [FINDING-20260928-001](findings/FINDING-20260928-001-active-map-identity.md).
- **Direct NOMAD→Lite3 UDP or duplicate producers.** Preserve the single arbiter, HIGH-LEVEL, lock, and vendor transport. See [FINDING-20260930-001](findings/FINDING-20260930-001-command-authority.md).
- **Legacy generic NOMAD Drive for Bipolix.** Use only the protected Phase-3C lease/reservation/epoch/deadman adapter.
- **Treating vendor state 98 as fault or standing proof.** It is valid non-fault telemetry; posture is separate. See [FINDING-20261001-004](findings/FINDING-20261001-004-vendor-state-98.md).
- **Precise path clearance without retained inputs.** Preserve the bounded reconstruction snapshot. See [FINDING-20260927-003](findings/FINDING-20260927-003-obstacle-snapshot.md).
- **Authority by timestamps/location alone.** Reconcile content and consumers; never import generated artifacts. See [FINDING-20260929-001](findings/FINDING-20260929-001-source-of-truth.md).
