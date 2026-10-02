# Known issues

| Issue | Status | Impact | Evidence | Workaround / next action |
|---|---|---|---|---|
| rtl8851bu instability evidence | OPEN / partial mitigation | intermittent Mini-PC network loss | [finding](findings/FINDING-20260927-002-rtl8851bu.md) | preserve station-only/power policy; run long soak; do not conflate with resource leaks |
| Phase-3C browser Xbox physical path | physical validation pending | NOMAD manual control cannot be called physically proven | [planned test](tests/TEST-20261001-002-phase3c-xbox-physical.md) | complete only the bounded approved Stand/readiness then forward/STOP workflow |
| Ghost command-source marker parity | partial | stale marker may block later ownership | [operations KB](../operations/ENGINEERING_KNOWLEDGE_BASE.md) | validate lock/process/marker together; retain idempotent safe cancel |
| Dedicated `robot down` CLI | implemented, not physically validated | operator command maturity incomplete | [test catalog T004](../testing/TEST_CATALOG.md) | separate explicitly approved physical test |
| Dedicated relocalize CLI motion | partial | approval/cancel proven offline, end-to-end physical maneuver not closed | [TEST-20260929-001](tests/TEST-20260929-001-relocalize-approval.md) | bounded separate approval when required |
| D455 transform/perception use | unvalidated | cannot claim navigation/perception contribution | [baseline](../testing/KNOWN_GOOD_BASELINE.md) | calibrate/validate live before enabling consumers |
| Mission/Patrol physical execution | pending | only non-motion/mock behavior proven | [NOMAD MVP](../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md) | Phase-3C manual safety first; later separate approvals |

Resolved incidents belong in the [finding registry](FINDING_REGISTRY.md), not
this open-issue list.

## Additional closure gaps from 2026-10-02

| Issue | Status | Evidence / required boundary |
|---|---|---|
| Independent body-frame strafe | UNVALIDATED; reported direct NOMAD failure | [FINDING-20261002-005](findings/FINDING-20261002-005-independent-body-frame-strafe-physical-proof-remains-incomplete.md) — preserve UNKNOWN cause; world-frame detour is separate |
| Deployment CPU-controller and idle-odom divergence | OPEN reconciliation | [FINDING-20261002-080](findings/FINDING-20261002-080-nav2-cpu-compatibility-fix-exists-deployed-but-not-on-integratio.md), [FINDING-20261002-081](findings/FINDING-20261002-081-idle-odometry-fix-exists-deployed-but-not-on-integration-branch.md) — preserve deployed fixes before any integration deployment |
| Deployed control guards, site caps/signs | OPEN; calibration intent UNKNOWN | [FINDING-20261002-082](findings/FINDING-20261002-082-deployed-control-guards-and-site-configuration-differ-from-integ.md) — source hash is not physical acceptance |
| Legacy exporter versus active SABLE ROS domain | OPEN; readiness unavailable | [FINDING-20261002-083](findings/FINDING-20261002-083-legacy-status-domain-and-advertised-capabilities-are-not-product.md) — domain 0 versus 23, sole cause UNKNOWN |
| Missing bags and clock provenance | EVIDENCE INCOMPLETE | [FINDING-20261002-084](findings/FINDING-20261002-084-retained-bags-and-clock-metadata-impose-evidence-limits.md) — retained payloads and capture-specific rates/times cannot fill absent experiments |
| Spark / suspected DC-DC damage | Historical incident, no recorded closure | [FINDING-20261002-010](findings/FINDING-20261002-010-battery-connection-spark-and-suspected-dc-dc-damage-need-separate-closure.md) — suspected damage, cause and retest UNKNOWN |
| Later lithium charging fire | Historical incident, no recorded closure | [FINDING-20261002-014](findings/FINDING-20261002-014-reported-lithium-charging-fire-has-no-recorded-safety-closure.md) — reported continued operation is not charging safety proof |
| Map-save / odometry / extrinsic metrology | EVIDENCE INCOMPLETE | [TEST-20261002-017](tests/TEST-20261002-017-home-map-mapping-and-save-load-historical-operation.md), [TEST-20261002-016](tests/TEST-20261002-016-historical-product-odometry-displacement-claim.md), [FINDING-20261002-013](findings/FINDING-20261002-013-configured-lidar-extrinsics-are-not-complete-calibration-metrology.md) |

The obstacle packaging and snapshot software fixes are recorded as offline
passes; installed clean-import/artifact acceptance remains a separate live
validation item. Repeated-boot lifecycle recovery and sustained exporter/network
soak are not closed by one snapshot or a regression test.

## Subsequent safe source closure — 2026-10-02

The read-only deployed snapshot remains unchanged. CPU-compatible controller selection and dispatch-bound idle odometry have subsequently been reconciled through existing SABLE owners, with offline tests only (TEST-20261002-106 / FINDING-20261002-095). Driver scaling diagnostics, bounded forwarding, UI evidence and passive validation preparation add observability without calibration changes. These are not deployed or physically proven. Direct strafe remains UNVALIDATED. See SAFE_AUTONOMOUS_CLOSURE.md for current counts, checks and blockers. Five additional supervised records TEST-20261002-107..111 are PLANNED ONLY, no new historical experiments; each physical matrix item is evaluated individually.
