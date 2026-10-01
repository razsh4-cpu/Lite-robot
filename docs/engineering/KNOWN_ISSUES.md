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
