# Physical robotics experiment template

Copy this template into the experiment/session directory before requesting live
approval. Complete PASS/FAIL/ABORT and data requirements before motion.

```markdown
# <experiment_id> — <name>

## QUESTION
What single uncertainty will this experiment answer?

## HYPOTHESIS
What observable result is expected, including numeric bounds where possible?

## SETUP
- robot ID/type:
- software commit/release:
- configuration/calibration/site-map revisions:
- physical environment and clearances:
- operator/emergency-stop position:
- command path and limits:

## PRECONDITIONS
- posture:
- command source before test:
- HIGH-LEVEL/telemetry/battery:
- scan/odom/TF/localization:
- path/obstacle review:
- exact approval received:

## PASS
Objective observable conditions required for success.

## FAIL
Conditions that make the hypothesis false without necessarily requiring an
emergency stop.

## ABORT
Immediate stop conditions: unexpected motion, loss/staleness, unsafe clearance,
ownership fault, operator call, power/cable risk, or other test-specific limit.

## DATA TO RECORD
- timestamps and session metadata;
- command source/lease events and operator approvals;
- relevant topics/TF/actions/system health;
- configured limits and diagnostic snapshot;
- external physical measurement/video when required.

## PROCEDURE
Numbered minimal steps, including zero/release verification.

## RESULT
Raw measured outcome, terminal action/service state and final command source.

## CONCLUSION
What was proven, not proven, and the next safe action.
```

Rules:

1. One primary question per experiment.
2. Parameter tuning is not performed during an acceptance run unless the run is
   explicitly a tuning experiment.
3. An interrupted run is not PASS even if motion looked promising.
4. Offline, simulation and physical evidence remain distinct.
5. No repeat run inherits approval automatically.
