# Project-wide Definition of Done

Code existing is not completion. Offline or simulation success does not prove hardware behavior. Every feature carries an evidence state:

```text
DESIGNED
→ IMPLEMENTED
→ OFFLINE TESTED
→ SIMULATION TESTED (when applicable)
→ PHYSICALLY VALIDATED (when required)
→ REGRESSION TESTED
→ DOCUMENTED
→ RELEASED
```

| Stage | Required evidence | Hardware required? |
|---|---|---|
| DESIGNED | Layer owner, interfaces, safety impact, dependencies, failure behavior, acceptance plan | No |
| IMPLEMENTED | Scoped code/config with no duplicate authority or bypass | No |
| OFFLINE TESTED | Focused deterministic tests; negative/failure paths; static ownership/config checks | No |
| SIMULATION TESTED | Scenario and model/version recorded; expected behavior and limits evaluated | Only when simulation is relevant; never hardware proof |
| PHYSICALLY VALIDATED | Explicitly approved experiment, preconditions, PASS/FAIL/ABORT, evidence and real result | Yes, for motion, sensors/calibration, hardware timing and physical safety claims |
| REGRESSION TESTED | Relevant catalog plus full applicable suite; known unrelated failures disclosed | Hardware only when the regression claim is physical |
| DOCUMENTED | Architecture/requirements/runbook/evidence updated; limitations and rollback recorded | No |
| RELEASED | Reviewed logical commit, version/release note, deployment and rollback artifact, clean repository | Deployment may require controlled target access; motion is separate |

## Completion rules

- A physical-motion capability cannot exceed `OFFLINE TESTED` without a live
  experiment approved for that exact run.
- Simulation and replay results are labeled as such and cannot establish
  loaded balance, collision clearance, real timing or hardware response.
- A live observation without preserved preconditions/result is useful evidence
  but not a repeatable acceptance test.
- A feature that changes a safety owner, TF owner, calibration, protected topic
  or command path requires architecture review and rollback.
- `RELEASED` requires all mandatory earlier stages for that feature. Optional
  simulation may be marked N/A with rationale.
- Known failures are never hidden to obtain a green label.

## Minimum evidence by feature class

| Feature class | Mandatory physical validation? |
|---|---|
| Documentation, schemas, pure state mapping | No; offline tests and review |
| Operator read-only status/diagnostics | Live read-only integration when claiming real-machine correctness |
| Posture or motion command | Yes |
| Navigation/controller/safety response | Yes for product operation and physical clearance claims |
| Sensor extrinsic/calibration | Yes, with measurement method and alignment evidence |
| Watchdog/lease cleanup | Offline fault tests plus live non-destructive validation before product claim |
| Deployment/startup recovery | Controlled reboot/live service validation; no motion required |
| Mission sequencing | Simulation/integration first, then controlled physical mission |

The current evidence status is cataloged in `TEST_CATALOG.md` and the
known-good product baseline in `KNOWN_GOOD_BASELINE.md`.
