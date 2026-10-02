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

## Additional do-not-repeat boundaries

- **Whole-tree deployment by branch age or host location.** Deployed SABLE
  fixes and integration guards differ; reconcile [actual consumers](MINIPC_DEPLOYED_STATE_AUDIT.md).
- **Treating online exporter or lateral capability constants as readiness.**
  [FINDING-20261002-083](findings/FINDING-20261002-083-legacy-status-domain-and-advertised-capabilities-are-not-product.md) preserves ROS-domain and fresh-state limitations.
- **Inferring direct strafe or SI calibration from a curve/detour.** Preserve
  [FINDING-20261002-005](findings/FINDING-20261002-005-independent-body-frame-strafe-physical-proof-remains-incomplete.md) and [FINDING-20261002-015](findings/FINDING-20261002-015-historical-normalized-vendor-axes-are-not-si-calibration.md).
- **Merging distinct hardware power incidents or calling continued operation
  safety closure.** Preserve spark, charging fire, and chair cable interruption
  separately, with UNKNOWN causes/retests where evidence is absent.
- **Treating old lifecycle pending-install text, a source fix, or missing raw
  capture as an accepted new run.** Retrospective capture dates are not test dates.

## Subsequent safe source closure — 2026-10-02

The read-only deployed snapshot remains unchanged. CPU-compatible controller selection and dispatch-bound idle odometry have subsequently been reconciled through existing SABLE owners, with offline tests only (TEST-20261002-106 / FINDING-20261002-095). Driver scaling diagnostics, bounded forwarding, UI evidence and passive validation preparation add observability without calibration changes. These are not deployed or physically proven. Direct strafe remains UNVALIDATED. See SAFE_AUTONOMOUS_CLOSURE.md for current counts, checks and blockers. Five additional supervised records TEST-20261002-107..111 are PLANNED ONLY, no new historical experiments; each physical matrix item is evaluated individually.
