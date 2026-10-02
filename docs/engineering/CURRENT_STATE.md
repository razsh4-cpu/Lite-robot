# Current engineering state

Updated: 2026-10-02. This is an evidence index, not current robot readiness or
permission to command motion. Capture dates do not replace experiment dates.

## Recorded physical results and historical claims

- Supported low-level Stand and guarded cleanup are preserved with their
  earlier failures, authorization expiry, and partial automatic-release proof.
- The separate HIGH-LEVEL `robot stand` closeout reports SITTING→STANDING,
  zero planar velocity, and release to NONE: [TEST-20261002-004](tests/TEST-20261002-004-high-level-robot-stand-temporary-lease-acceptance.md).
- The chair sequence preserves reported safe refusal, power interruption, then
  accepted Nav2 goal/stop/release: [TEST-20261002-005](tests/TEST-20261002-005-earlier-chair-planning-safe-refusal.md), [TEST-20260927-001](tests/TEST-20260927-001-chair-avoidance-interrupted.md), [TEST-20260927-002](tests/TEST-20260927-002-chair-avoidance-pass.md). The accepted autonomous
  world-frame detour does not independently prove body-frame strafe.
- Earlier ROS backward, yaw, curve, and neutral/shutdown results are retained
  retrospective physical reports with raw evidence incomplete: [TEST-20261002-021](tests/TEST-20261002-021-historical-ros-vendor-backward-motion.md), [TEST-20261002-022](tests/TEST-20261002-022-historical-ros-vendor-yaw-in-both-directions.md), [TEST-20261002-023](tests/TEST-20261002-023-historical-ros-forward-and-yaw-curved-motion.md), [TEST-20261002-024](tests/TEST-20261002-024-historical-ros-deadman-release-neutral-and-shutdown.md). Their normalized units are not SI calibration.
- Home_Map mapping/save-load and product odometry displacement are historical
  claims with missing map hashes and measurements: [TEST-20261002-017](tests/TEST-20261002-017-home-map-mapping-and-save-load-historical-operation.md), [TEST-20261002-016](tests/TEST-20261002-016-historical-product-odometry-displacement-claim.md).

## Live-static and offline evidence

- Real ROS health, ordered DDS/lifecycle recovery, compatible AUTONOMY QoS,
  and headless resource snapshots are indexed in the test registry. Persistent
  installation and long/repeated-boot soak remain distinct proof obligations.
- Phase-3B live Mini-PC MQTT negative-path validation passed with unavailable
  robot telemetry, rejected intent, zero output, NONE, and no owner lock:
  [TEST-20261001-001](tests/TEST-20261001-001-nomad-phase3b-live-static.md). This did not prove healthy robot motion readiness.
- Phase-1 status, Phase-2 reservation, Phase-3A mock intent, relocalize approval,
  packaging/snapshot repairs, and Mission/Patrol mock behavior are software
  evidence. The committed Phase-3C adapter/Stand/connectivity history is
  [TEST-20261002-014](tests/TEST-20261002-014-committed-phase-3c-stand-and-connectivity-software.md); physical acceptance remains pending.

## Observed deployment differs from integration source

The read-only [Mini-PC audit](MINIPC_DEPLOYED_STATE_AUDIT.md) and
[TEST-20261002-080](tests/TEST-20261002-080-minipc-read-only-evidence-audit.md) record source/module hashes, service/config state,
CPU compatibility, ROS-domain mismatch, retained bag limits, and clock
uncertainty. Deployed SABLE has AVX-controller and idle-odometry fixes absent
from integration, while newer control guards are absent from deployed main.
Neither whole tree is safe to prefer without reconciliation. The observed
site caps/signs and legacy exporter fields are not physical calibration or
current readiness. No deployment or robot command was performed by the audit.

## Open or unvalidated

- Independent body-frame lateral motion; owner-reported direct NOMAD strafe
  failed with UNKNOWN cause: [TEST-20261002-013](tests/TEST-20261002-013-owner-reported-direct-nomad-strafe-failure.md).
- First real Phase-3C browser/Xbox forward/STOP, dedicated down CLI, dedicated
  full physical relocalize, NOMAD Mission/Patrol, and D455 perception integration.
- Network/boot/resource soak, all-source ghost-marker cleanup parity, missing
  raw physical captures/metrology, and separately reported spark/fire safety
  incidents without recorded engineering closure.

The existing bounded first Phase-3C motion session remains
[TEST-20261001-002](tests/TEST-20261001-002-phase3c-xbox-physical.md) (`PLANNED`, actual result `UNKNOWN`). It requires
separate approval and fresh preflight; this index authorizes nothing.

Primary navigation baseline: [closeout](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
Historical coverage and gaps: [master inventory](HISTORICAL_MASTER_INVENTORY.md).

## Subsequent safe source closure — 2026-10-02

The read-only deployed snapshot remains unchanged. CPU-compatible controller selection and dispatch-bound idle odometry have subsequently been reconciled through existing SABLE owners, with offline tests only (TEST-20261002-106 / FINDING-20261002-095). Driver scaling diagnostics, bounded forwarding, UI evidence and passive validation preparation add observability without calibration changes. These are not deployed or physically proven. Direct strafe remains UNVALIDATED. See SAFE_AUTONOMOUS_CLOSURE.md for current counts, checks and blockers. Five additional supervised records TEST-20261002-107..111 are PLANNED ONLY, no new historical experiments; each physical matrix item is evaluated individually.
