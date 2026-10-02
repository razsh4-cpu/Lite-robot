# Bipolix engineering knowledge

This directory is the canonical **entry point** for durable engineering
knowledge. It does not replace or move primary evidence. Architecture remains
under [`docs/architecture`](../architecture/ARCHITECTURE.md), the maintained
test catalog remains [`docs/testing/TEST_CATALOG.md`](../testing/TEST_CATALOG.md),
and retained logs/artifacts remain where their producers placed them.

## Start here

- [Current state](CURRENT_STATE.md)
- [Capability matrix](CAPABILITY_MATRIX.md)
- [Known issues](KNOWN_ISSUES.md)
- [Known-good configurations](KNOWN_GOOD_CONFIGURATIONS.md)
- [Lessons learned](LESSONS_LEARNED.md)
- [Known bad / do not repeat](KNOWN_BAD.md)
- [Test-session registry](TEST_REGISTRY.md)
- [Engineering-finding registry](FINDING_REGISTRY.md)

## Evidence model

Two record types are deliberately separate:

- `bipolix.test_session/v1`: an experiment or validation with an explicit
  result and evidence classification;
- `bipolix.engineering_finding/v1`: reusable knowledge from debugging,
  integration, deployment, architecture, or reliability work.

Test classifications are `PHYSICALLY_PROVEN`, `LIVE_STATIC_PROVEN`,
`OFFLINE_PROVEN`, `FAILED`, `PARTIAL`, `INCONCLUSIVE`, `PLANNED`,
`HISTORICAL_CLAIM`, and `SUPERSEDED`. Finding statuses are `CURRENT`,
`KNOWN_ISSUE`, `HISTORICAL`, `SUPERSEDED`, `DO_NOT_USE`, and `RESOLVED`.

`UNKNOWN`, `HISTORICAL_CLAIM`, `INCONCLUSIVE`, and `EVIDENCE MISSING` are
intentional truth-preserving values. Unit/mock results never become physical
proof. A later pass never erases an earlier failure.

## Workflow

Before meaningful subsystem work:

1. read the relevant capability row, findings, and prior sessions;
2. for an experiment, initialize a record and define PASS/FAIL/ABORT before
   execution;
3. preserve only useful logs/bags/images/videos and link to them;
4. close the record with actual behavior and classification;
5. add/update a finding when reusable knowledge was learned;
6. update the capability matrix only when the evidence warrants it;
7. run the validator.

Trivial commands do not need records. Physical tests still require the normal
explicit authorization and safety workflow; creating a record authorizes
nothing.

## Tooling

```bash
python3 tools/engineering_knowledge.py new-test \
  --title "Short descriptive title" --robot-id robot_01
python3 tools/engineering_knowledge.py new-finding \
  --title "Reusable engineering finding"
python3 tools/engineering_knowledge.py validate
```

The initializer collects only local timestamp/host/Git metadata. It performs
no ROS, network, ownership, configuration, or hardware operation. Add the new
record to its registry after completing its metadata.

Taxonomy: `ROBOT_CONTROL`, `SAFETY`, `ROS2`, `TF`, `ODOMETRY`,
`LOCALIZATION`, `NAVIGATION`, `SENSORS`, `XBOX`, `NOMAD`, `MQTT`,
`NETWORKING`, `MINI_PC`, `DEPLOYMENT`, `RELIABILITY`, `PERFORMANCE`,
`HARDWARE`, `R_AND_D`.

## Historical closure and deployed-state evidence

- [Historical master inventory](HISTORICAL_MASTER_INVENTORY.md) maps retained
  experiments, failures, fixes, retests, and remaining gaps to canonical IDs.
- [Mini-PC deployed-state audit](MINIPC_DEPLOYED_STATE_AUDIT.md) separates
  inspected source/configuration/services from historical motion acceptance.

The 2026-10-02 retrospective records use their capture date in frontmatter and
state the actual experiment date separately, including `UNKNOWN`. Restored
records retain original IDs and an explicit recovery note. Written physical
reports, source tests, live-static captures, and raw artifacts remain distinct.
The historical chair PASS does not establish independent body-frame strafe,
and older normalized ROS caps do not calibrate current SI-scaled NOMAD control.

- [Final knowledge-gap audit](FINAL_KNOWLEDGE_GAP_AUDIT.md) summarizes closure
  and exact remaining evidence/retest requirements.

## Subsequent safe source closure — 2026-10-02

The read-only deployed snapshot remains unchanged. CPU-compatible controller selection and dispatch-bound idle odometry have subsequently been reconciled through existing SABLE owners, with offline tests only (TEST-20261002-106 / FINDING-20261002-095). Driver scaling diagnostics, bounded forwarding, UI evidence and passive validation preparation add observability without calibration changes. These are not deployed or physically proven. Direct strafe remains UNVALIDATED. See SAFE_AUTONOMOUS_CLOSURE.md for current counts, checks and blockers. Five additional supervised records TEST-20261002-107..111 are PLANNED ONLY, no new historical experiments; each physical matrix item is evaluated individually.
