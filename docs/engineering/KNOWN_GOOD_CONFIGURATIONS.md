# Known-good configuration references

Do not copy values from this index blindly; the linked source remains
authoritative.

| Area | Known-good reference | Important values / boundary |
|---|---|---|
| Product navigation | [known-good baseline](../testing/KNOWN_GOOD_BASELINE.md) | body 0.610×0.370 m; footprint 0.710×0.470 m; padding 0; inflation 0.30 m; limits 0.10/0.05/0.20; watchdog 300 ms |
| Localization | [configuration ownership](../architecture/CONFIGURATION_CALIBRATION_DATA.md) | normal acceptance `>=80%` ×3; saved pose is hypothesis; do not alter origin/extrinsics to raise score |
| Command authority | [safety architecture](../architecture/SAFETY_AND_ARBITRATION.md) | one arbiter/lock/marker; safe boot `NONE`; sources mutually exclusive |
| MQTT/NOMAD non-motion | [NOMAD Phase-3B record](../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md) | robot-scoped topics; edge broker 1885 in recorded deployment; status fails closed |
| Phase-3C adapter | [Phase-3C design](../../../NOMAD/docs/superpowers/specs/2026-10-01-bipolix-phase3c-physical-teleop-design.md) | v2 physical-manual contract; default output disabled; neutral/new-RB/continuous-deadman/watchdog |
| Mini-PC workload | [performance baseline](../operations/PERFORMANCE_BASELINE.md) | headless; RViz laptop-side; D455 on demand when unused by Day-2 Nav2 |
| Source deployment | [reconciliation record](../architecture/SOURCE_OF_TRUTH_RECONCILIATION_2026-09-29.md) | compare content/consumers; exclude build/install/log/runtime state |
