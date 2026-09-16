# lite3_security_patrol

Offline-safe scaffolding for the Lite3 security-patrol project.

`cmd_vel_normalizer` is deliberately **not** a Lite3 hardware bridge. It maps
`/cmd_vel` to `/lite3/normalized_cmd_vel` and publishes zero whenever physical
limits are uncalibrated (the default) or commands become stale. A separately
reviewed adapter must connect this normalized topic to the explicit-control
Lite3 RL process after hardware validation.

The `mission_core` and `health` modules are pure Python decision/data models.
They do not publish velocity, Nav2 goals, or network alerts.
