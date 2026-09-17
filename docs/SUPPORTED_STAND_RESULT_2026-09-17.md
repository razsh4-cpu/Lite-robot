# Supported stand attempt result — 2026-09-17

## Outcome

The explicitly authorized supported stand attempt **did not execute and did not
move the robot**. The five-second authorization expired before the separate
`stand` input was accepted. The state machine failed closed, requested SDK
release, and rejected the stand request. There was no retry.

Final console status:

```text
state=0
stand_test=RELEASE_REQUESTED
abort_reason=[stand authorization expired]
preflight=[OK]
acquisition=NOT_REQUESTED
ownership=NOT_REQUESTED
telemetry=FRESH
joint_send_enabled=0
forward=0 lateral=0 yaw=0
```

## Observed sequence

1. Passive `status` reported fresh telemetry, `preflight=[OK]`, ownership not
   requested, and the joint-send gate closed.
2. `acquire` submitted one ownership request. The SDK exposes no positive
   ownership acknowledgement. Joint positions and posture remained unchanged.
3. A second `status` reported fresh telemetry, `preflight=[OK]`,
   `OWNERSHIP_UNCONFIRMED`, and the joint-send gate still closed.
4. `authorize_stand SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED` armed one attempt for
   five seconds.
5. Before the following `stand` command was accepted, the worker detected the
   expired deadline, entered `ABORTING`, and then `RELEASE_REQUESTED`.
6. The subsequent `stand` input was blocked. Final `status` showed ownership and
   acquisition reset to `NOT_REQUESTED` with `joint_send_enabled=0`.
7. The console was quit cleanly.

The passively measured joint positions stayed at the folded/resting values. No
`STANDING_UP` or `TARGET_REACHED` state was entered, and the guarded joint-send
gate never opened. Therefore no stand trajectory or joint command was issued.

## Cause and correction

The separate authorization API deliberately expires after five seconds. Remote
tool and console-output latency can exceed that interval even when the next
action is requested immediately from the operator's perspective.

The existing console already provides
`stand_once SUPPORTED_ESTOP_HEALTH_LIMITS_CONFIRMED`. Its state-machine method
holds the lifecycle lock while it both arms and queues the request, eliminating
the inter-command timing gap. Existing `stand_once_test` coverage verifies that
the combined action remains one-use, leaves the send gate closed while pending,
and fails closed on invalid preconditions.

The documented real-test procedure now uses `stand_once`. No control algorithm,
gain, joint target, or send gate was changed.

## Current stop point

The approved attempt is consumed. Another physical stand test requires new
explicit approval and the same mechanical support, clear area, emergency-stop,
battery/health, and supervision checks. Do not retry automatically. Body shift,
leg lift, RL, velocity control, and raw torque remain prohibited.

A later, separately approved atomic attempt reached the standing target. Its
result and the safety issue it exposed are recorded in
`docs/SUPPORTED_STAND_SUCCESS_2026-09-17.md`.
