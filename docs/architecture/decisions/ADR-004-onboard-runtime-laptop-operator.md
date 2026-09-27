# ADR-004: Keep robot-critical runtime onboard and operator tools on laptop

- Status: Accepted
- Date: 2026-09-28

## Context

The Mini-PC must preserve heartbeat, telemetry, odometry, sensing, localization,
Nav2 and safety when the laptop disconnects. RViz, Xbox input, operator menus
and development tools benefit from the laptop and are not robot-runtime
prerequisites. This split has already been used in the physical Day-2 system.

## Decision

Run robot-critical transport, sensors in use, localization, Nav2, arbitration
and safety on `abx-fit-001`. Run RViz, laptop Xbox/C2 UI, monitoring and
development tooling on the laptop.

## Consequences

- Loss of the laptop cannot terminate robot heartbeat or telemetry.
- An autonomous mission can remain safe without an RViz connection.
- GUI and unused development workloads do not consume onboard resources.
- C2 remains a request/observation boundary, not a hardware transport owner.
