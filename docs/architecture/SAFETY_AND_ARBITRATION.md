# Safety, arbitration and system-state baseline

This document formalizes existing behavior without replacing its runtime state
machines. The deployed guards remain authoritative.

## Command sources and authority

Current accepted values are:

```text
NONE
LOCAL_XBOX
LAPTOP_XBOX
AUTONOMY
```

`/run/lite3-control/owner.lock` is the exclusive kernel lock and
`/run/lite3-control/COMMAND_SOURCE` is the observable source marker. A source
may publish motion only while it holds the lease and the marker agrees. Boot,
shutdown and failure return to `NONE`.

| Source | Acquisition | Liveness | Release/failure cleanup |
|---|---|---|---|
| LOCAL_XBOX | Optional Xbox supervisor validates device and free ownership; fresh operator authorization remains required | Joystick freshness and HIGH-LEVEL gates | Neutral/zero, revoke authorization, stop optional input, release; persistent robot runtime continues |
| LAPTOP_XBOX | Explicit C2 request after joystick/robot selection and free lease | request + heartbeat + Joy all fresh within 300 ms | publish neutral, clear authorization/request, release on disconnect/stale/stop |
| AUTONOMY | Explicit service start; localization gate and free lease | fresh finite `/cmd_vel` within 300 ms plus HIGH-LEVEL and safety monitor prerequisites | publish zero, stop source and release on invalid/stale/abort/shutdown |
| NONE | Default/no acquisition | no source may command motion | HIGH-LEVEL stays connected and maintains heartbeat/telemetry without requesting motion |

The existing implementation distributes lease helpers between command-source
modules. A future common library may remove duplication only after parity tests;
the authority model must not change accidentally.

## Layered safety chain

```text
Intent producer
  → source-specific input validation
  → exclusive command-source lease
  → protected ROS topic
  → HIGH-LEVEL ownership/freshness/standing/authorization gates
  → bounded vendor command
  → Lite3 vendor controller
```

No mission, AI, operator or adapter may publish below this chain.

## Conceptual system states

These aggregate existing facts; they are not a new runtime enum:

```text
BOOTING
  → SYSTEM_READY
  → STANDING
  → LOCALIZED
  → NAVIGATION_READY
  → MISSION_ACTIVE
```

| Concept | Current evidence |
|---|---|
| BOOTING | network/DDS and required services are not yet proven healthy |
| SYSTEM_READY | persistent runtime, heartbeat, fresh telemetry/odom and core TF are healthy |
| STANDING | fresh vendor telemetry reports the explicit standing basic state |
| LOCALIZED | guard reports scan-to-map score at or above 0.80 |
| NAVIGATION_READY | three consecutive valid scores ≥0.80 plus ready Nav2 inputs/lifecycle |
| MISSION_ACTIVE | AUTONOMY lease is held and a Nav2 goal/command stream is active |

Fault transition:

```text
MISSION_ACTIVE → FAULT → STOPPING → SAFE
```

`SAFE` means motion intent is zero, temporary authorization is revoked and the
motion-source lease is released. It does not require shutting down persistent
heartbeat, telemetry, odometry or sensor services.

## Fault-response ownership

| Fault | Detection owner | Required response owner | Current response |
|---|---|---|---|
| `/scan` stale | Nav2 safety monitor / readiness probes | AUTONOMY source + Nav2 | stop source, zero/release; navigation blocked |
| `/odom` stale | Nav2 safety monitor / health probes | AUTONOMY source + Nav2 | stop source, zero/release; navigation blocked |
| TF unavailable/stale | localization/Nav2 readiness | localization/Nav2 | do not declare ready; abort/block navigation |
| Localization invalid | localization guard + safety monitor | AUTONOMY/Nav2 | block acquisition or abort active navigation |
| `/cmd_vel` invalid/stale | AUTONOMY source | AUTONOMY source | zero and release after 300 ms watchdog |
| Xbox/C2 stale | source relay | owning Xbox source | neutral, revoke and release; robot runtime stays alive |
| HIGH-LEVEL unhealthy | health/readiness and runtime | all command sources | motion blocked; source cleanup; preserve evidence |
| Telemetry stale | HIGH-LEVEL runtime and safety monitors | HIGH-LEVEL + source | non-zero command suppressed; zero/release upstream |
| Mini-PC restart | systemd/runtime initialization | platform startup | source initialized to `NONE`; no restored velocity/authorization |
| Nav2 action failure | Nav2 / future Mission Manager | Nav2 then Mission Layer | stop command stream; action reports failure; future mission recovery policy decides next action |
| Battery below 25% during navigation | Nav2 safety monitor | AUTONOMY source | abort/stop and release; future return/stand/down policy not yet defined |
| Laptop/network loss | C2 source freshness | LAPTOP_XBOX source | release manual source; onboard autonomous/safety services remain independent |

## Health model

Each subsystem reports one of:

```text
READY  DEGRADED  FAULT  OFFLINE
```

Subsystems are evaluated independently: Robot/HIGH-LEVEL, LiDAR, Odometry, TF,
Localization, Nav2, Network, Battery, CPU and Storage. System health is an
aggregation for a requested operation, not one universal boolean. For example,
an offline laptop or D455 can degrade remote visualization/perception without
invalidating onboard LiDAR navigation.

## Mission safety contract (future)

Mission states are `PENDING`, `RUNNING`, `ARRIVED`, `FAILED`, `CANCELLED` and
`RECOVERING`. The future Mission Manager selects *what* to do and observes Nav2
results. It must not plan paths, publish `/cmd_vel`, own vendor transport or
alter safety gates. Cancel must propagate to Nav2, cause zero/release through
the current command path and finish with an observable terminal result.

Potential mission types are `GoTo`, `Patrol`, `Inspect`, `RespondToAlert`,
`ReturnHome` and `Cancel`. They are contracts only in this baseline; Day 3 is
not activated.

## Alerts and observation poses (future)

```text
Alert + location/region
  → Mission policy
  → safe observation/approach pose
  → NavigateToPose
  → Inspect / Report
```

An alert coordinate is evidence, not necessarily a safe destination. Mission
policy must consider map validity, restricted areas, footprint, sensor field of
view and standoff distance before proposing an observation pose. The proposal
still passes through normal localization, Nav2 and arbitration gates.
