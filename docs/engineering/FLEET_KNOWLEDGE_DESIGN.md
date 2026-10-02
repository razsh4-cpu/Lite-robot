# Future SABLE fleet engineering knowledge

This is a design note, not a fleet-learning service or deployment mechanism.
The existing Test Session/Finding split remains useful: an observation belongs
to a specific execution, while a candidate lesson needs applicability review.

Proposed lifecycle: robot evidence → Candidate Finding → linked evidence →
engineering/AI analysis → human approval → validated knowledge → applicability
rules → relevant robots. Agents may collect allowlisted evidence and draft
candidates; they may not silently promote them or teach other robots a behavior.
One successful robot run does not authorize cross-robot deployment.

## Applicability metadata proposal

| Field | Purpose / truth boundary |
|---|---|
| Robot model, robot ID | Separate platform-wide ideas from unit-specific evidence. |
| Hardware revision, firmware | Record relevant controller, actuator and CPU compatibility; UNKNOWN stays explicit. |
| Software version / SHA | Identify SABLE, adapter and driver revisions and dirty/deployed divergence. |
| Sensor configuration | Device model, calibration/extrinsic revision, mounting and relevant settings. |
| Environment / site | Surface, payload, workspace/map revision and operational limits. |
| Capability and control path | Match the affected behavior; keep local, historical laptop and current network paths separate. |
| Evidence level, result, validation status | Retain offline/live-static/physical distinction, failure and partial retests. |
| Applicability scope and exclusions | State measured prerequisites and robots/configurations to which evidence does not transfer. |
| Supersedes / superseded-by | Preserve earlier failure and configuration scope rather than deleting history. |
| Review / approval status | Candidate, reviewed, accepted or rejected, reviewer, date, basis and required retests. |
| Primary evidence / integrity | Stable references/hashes, collection bounds and missing payloads/access limits. |

These are proposed optional metadata additions, not retroactive requirements that
invalidate historical records. Schema evolution should first validate candidate
metadata offline, then define reviewed applicability rules and migration behavior.
UNKNOWN prerequisites prevent automatic transfer of an operational capability.

## Review boundary

Applicability review asks whether hardware/firmware/software/sensors/site and
control-path assumptions match and whether negative tests, faults, stop/release
and required physical retests exist. A software repair can transfer as a reviewed
candidate patch without transferring a physical PASS. Calibration, motion limits,
safety overrides, odometry signs and site maps never become fleet defaults from
one observed installation.

Validated knowledge is an engineering reference for relevant robots. Any future
execution or deployment still uses its product change-review, authorization,
safety and staged-validation process. This task implements no cross-robot
propagation, deployment, autonomous learning or product runtime dependency.
