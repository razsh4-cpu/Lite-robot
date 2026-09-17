# Supported stand automatic-release result — 2026-09-17

## Evidence status

**Software acceptance: PASS. Physical observation: EVIDENCE INCOMPLETE.**

One explicitly authorized, mechanically supported `stand_once` was executed from
branch `handoff/low-level-leg-control-2026-09-17` at commit
`11b5ad45568950497db64d25c8d37eb9554fcf7d`. The executable SHA-256 was
`32d1a307def8eec63b185ae653947516cc32d186e395a9d6218e401ddb5b420a`.

No RL, velocity, body-shift, leg-lift, walking, Nav2, lidar or raw-torque command
was used. No operator `stop` was required and no retry occurred.

## Observed software sequence

```text
LOCKED
ARMED
PENDING
STANDING_UP
TARGET_REACHED
ABORTING
RELEASE_REQUESTED
```

Pre-action status showed fresh telemetry, `preflight=[OK]`, zero software
velocity, ownership/request `NOT_REQUESTED`, and `joint_send_enabled=0`.
After `acquire`, the gate remained closed and ownership was honestly reported as
`OWNERSHIP_UNCONFIRMED`.

Final status after automatic release was:

```text
state=0
stand_test=RELEASE_REQUESTED
abort_reason=[stand target hold complete]
preflight=[OK]
acquisition=NOT_REQUESTED
ownership=NOT_REQUESTED
telemetry=FRESH
joint_send_enabled=0
forward=0 lateral=0 yaw=0
```

The console then quit cleanly.

## Trace measurements

- Stand entry: trace wall time 26900.5157485 s
- First `TARGET_REACHED`: elapsed 3.501 s
- Automatic release event: elapsed 5.501 s
- Measured target hold: **2.0005399 s**
- Total entry-to-release interval: 5.5024791 s
- Trace records: 5,372; dropped: 0
- Sent records: 5,370
- Maximum tracking error during the complete trajectory: 0.0823028 rad
- Tracking error at first target reach: 0.0595558 rad
- Maximum absolute roll: 0.0065554 rad
- Maximum absolute pitch: 0.0326368 rad
- Trace end reason: `stand target hold complete`

The complete-trajectory error remained below the 0.35 rad active guard. The
target-reached error was below the 0.08 rad convergence limit. Automatic release
met the two-second design within one feedback interval.

## Evidence files

Generated evidence is stored outside Git to avoid committing machine runtime
logs:

- `/home/abx/Desktop/robotdog_ws/.evidence/auto-release-2026-09-17/console.log`
  - SHA-256 `bd6c027b1b07bab8ab8b85f8631be00bcbb41bf628bfb9a91cdb109a17cb008e`
- `/home/abx/Desktop/robotdog_ws/.evidence/auto-release-2026-09-17/stand-trace.jsonl`
  - SHA-256 `b03e65c1d3cefad0e5ca13ac53a380b756b80cb56b32443d0b138c53b79aa58e`

The original `/tmp` files have the same hashes. The transcript includes process
startup, all operator inputs, state transitions, trace path and final status.

## Missing physical evidence

The software cannot establish the robot's physical response, support behavior,
sound, or final posture after SDK release. Those facts remain **UNKNOWN** until
the supervising operator reports them. This document does not claim unsupported
balance or a safe return-to-rest.

No later physical milestone is authorized. The next safe action is to record the
operator's direct observation, review this result, and decide whether any further
work should remain offline.
