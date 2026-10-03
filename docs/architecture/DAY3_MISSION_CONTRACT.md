# Day-3 Mission Manager contract (dormant)

Status: **IMPLEMENTED BUT NOT PHYSICALLY VALIDATED / EXECUTION DISABLED**.

This phase provides pure contracts, the existing named-location registry and
offline orchestration in `backend/lite3/autonomy.py` (see its README).
The concrete live NavigationPort is not implemented or activated.
It installs no service, starts no node, sends no Nav2 goal and acquires no lease.

## Boundary

```text
operator or alert request
  -> Mission Manager (what, lifecycle and result)
  -> existing Nav2 NavigateToPose (how to navigate)
  -> /cmd_vel -> AUTONOMY -> arbiter -> HIGH-LEVEL -> Lite3
```

Mission Manager may resolve either a validated saved location or an ad-hoc
`map` pose. It must verify robot capability/readiness and delegate navigation to
Nav2. It must never plan velocity, publish `/cmd_vel`, import vendor APIs, acquire
low-level control, or bypass the Command Arbiter.

## Pure contract now available

`product/missions/bipolix_missions` defines:

- `SavedLocationTarget(name)`;
- `AdHocTarget(x, y, yaw, frame_id=map)`;
- states `IDLE`, `VALIDATING`, `NAVIGATING`, `ARRIVED`, `FAILED`, `CANCELLED`;
- explicit, immutable lifecycle transitions.

The existing dormant registry is
`sensor_visualization/config/named_locations.yaml`. `gate`, `entrance` and
`parking` deliberately contain no invented coordinates.

## Future operator contract

- `go <saved_location>` resolves a configured site location and requests one
  existing `NavigateToPose` action;
- an ad-hoc request supplies a finite `map` pose;
- `mission status` reports lifecycle/action/safety state without ownership;
- `mission cancel` cancels Nav2, verifies zero, releases AUTONOMY and ends in
  `CANCELLED`.

These commands are **not activated** in this phase. Implementation requires
mocked action/cleanup tests, then live no-motion integration, then an explicitly
approved physical mission experiment.
