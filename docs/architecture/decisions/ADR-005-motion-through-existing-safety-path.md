# ADR-005: All physical motion uses the existing safety/arbitration path

- Status: Accepted
- Date: 2026-09-28

## Context

The physically proven Lite3 product path uses mutually exclusive command-source
leases, a 300 ms freshness watchdog, HIGH-LEVEL telemetry/standing/authorization
gates and safe-zero/release cleanup. The accepted chair-avoidance run completed
through `Nav2 → /cmd_vel → AUTONOMY → arbiter → HIGH-LEVEL → vendor gait` and
ended at `COMMAND_SOURCE=NONE`.

Adding a mission, AI, operator tool or adapter that can publish below this
boundary would invalidate the evidence and create competing motion authorities.

## Decision

Every product-path physical motion request must use the existing approved
command-source acquisition, protected ROS endpoint, HIGH-LEVEL safety and
release path. Generic interfaces express intent but grant no permission and
open no vendor transport.

No new module may create another arbiter, hardware command socket, UDP 43897
receiver, `/odom` publisher or direct vendor-motion bypass.

## Consequences

- Future Mission and AI layers can request outcomes but cannot command motors.
- Simulation adapters may emulate the contract but simulation evidence is not
  hardware authorization.
- Replacing any safety owner requires a separate ADR, parity tests, rollback
  plan and explicitly approved live validation.
- Failures converge to zero, revoked authorization, released lease and an
  observable terminal state rather than restoring an old command.
