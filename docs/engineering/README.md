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
