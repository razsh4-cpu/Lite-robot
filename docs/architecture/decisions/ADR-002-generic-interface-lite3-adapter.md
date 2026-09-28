# ADR-002: Separate Robot Interface from the Lite3 implementation

- Status: Accepted
- Date: 2026-09-28

## Context

Higher layers currently encounter instance names and Lite3-specific runtime
details. Future simulation and other robot platforms require a stable contract,
but rewriting the hardware-proven stack would create unnecessary risk.

## Decision

Define a minimal vendor-neutral Robot Interface for identity, capabilities,
planar velocity intent, posture intent, normalized state, odometry and health.
Place Lite3 state semantics and delegation to approved Lite3 ROS endpoints in a
separate adapter owned by the reusable Platform layer under
`platform/robot_adapters/lite3/`. Product code depends on the generic Robot
Interface and does not own or directly depend on DeepRobotics implementation
details where that generic boundary is sufficient. The adapter wraps the existing
runtime; it does not replace it or open another hardware transport.

## Consequences

- Higher layers can depend on capabilities rather than Lite3 assumptions.
- Future robot-specific adapters share the `platform/robot_adapters/<robot>/`
  ownership convention.
- Robot instances and robot types are distinct.
- Phase 1 adds pure contracts and mapping only; runtime integration is gradual.
