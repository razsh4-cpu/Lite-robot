# BIPOLIX ROBOTICS PLATFORM

```text
Operator / C2
      ↓
Mission Layer
      ↓
Autonomy
      ↓
Safety / Arbitration
      ↓
Robot Interface
      ↓
Robot Adapter
      ↓
Hardware
```

This is the architectural source of truth. Read it together with
[`ROBOT_PLATFORM.md`](ROBOT_PLATFORM.md) before changing product architecture.
Phase 1 establishes the Robot Interface and Lite3 Adapter boundary around the
working system; it does not replace a production runtime.

## Layer contracts

| Layer | Responsibility | Allowed inputs | Allowed outputs | Must not | Failure behavior |
|---|---|---|---|---|---|
| Operator / C2 | Present state and accept explicit operator intent | Human input, read-only robot status | Action requests to Mission/Autonomy or approved manual source | Open vendor sockets, forge ownership, bypass safety | Report unavailable; send neutral/release when its owned input disappears |
| Mission Layer | Sequence named product goals | Mission request, capabilities, navigation result | Goals to Autonomy | Send raw velocity or vendor commands | Cancel current goal and report the failed step |
| Autonomy | Turn goals and sensor state into bounded motion intent | Goals, map/localization, sensors | Standard velocity intent through approved source | Assume every robot supports every motion axis; bypass ownership | Publish zero/stop and release on stale or invalid prerequisites |
| Safety / Arbitration | Grant one command source and enforce gates | Source requests, state freshness, permits | Exclusive lease and approved bounded command stream | Grant two owners or restore stale authorization/velocity | Fail closed to `NONE`, zero, revoke authorization |
| Robot Interface | Expose identity, capabilities, normalized state, posture and planar velocity intent | Generic requests and adapter state | Vendor-neutral contract to/from one adapter | Contain vendor command IDs, networking or defeat the safety chain | Reject invalid/unsupported requests; report normalized degraded/offline state |
| Robot Adapter | Translate generic contracts to one approved platform path | Validated generic intent, vendor-derived state | Existing approved ROS interface and normalized state | Create duplicate runtime/arbiter/telemetry receiver | Preserve zero/release behavior and report translation failure |
| Hardware | Execute the platform controller's accepted command | Existing vendor HIGH-LEVEL transport | Vendor telemetry | Define product policy | Native controller/watchdog behavior remains authoritative |

## Dependency rules

1. Dependencies point downward only; circular dependencies are forbidden.
2. Mission may depend on Autonomy and generic Robot Interface types, never a
   physical adapter.
3. Autonomy may emit `linear.x`, `linear.y`, and `angular.z` only through the
   approved command-source path.
4. Operator/C2 may request actions but cannot bypass Safety / Arbitration.
5. Robot Interface may be implemented by a Robot Adapter; it contains no robot
   vendor imports, command IDs, ports or network addresses.
6. The Lite3 Adapter may know Lite3/DeepRobotics state semantics and approved
   ROS endpoints, but it must reuse the persistent HIGH-LEVEL runtime.
7. Exactly one owner remains responsible for each hardware transport and state
   transform. No adapter may add another UDP telemetry receiver, `/odom`
   publisher, command arbiter, velocity controller or HIGH-LEVEL runtime.
8. Capability checks supplement—never replace—runtime safety gates, leases,
   freshness checks, the 300 ms command watchdog and safe-zero behavior.

## Phase-1 code boundary

```text
src/robot_interfaces/bipolix_robot_interfaces/
    contracts.py        # generic identity/state/capability/request vocabulary
    config.py           # validates the four-file robot configuration concept

src/robot_adapters/lite3/bipolix_lite3_adapter/
    state_mapping.py    # Lite3 decoded state -> generic state

config/robots/lite3/
    robot.yaml          # instance/type identity, dimensions, capabilities
    motion.yaml         # generic endpoints, conservative limits, vendor target
    safety.yaml         # existing ownership, watchdog and localization gates
    sensors.yaml        # existing topic/transport ownership
```

These are pure Python contracts and configuration. They start no ROS node,
service or socket and send no command. Existing production components remain
authoritative as inventoried in `ROBOT_PLATFORM.md`.

## Identity versus type

`robot_01` is a configured robot instance. `Lite3 Venture` is the robot type,
and `lite3` selects its adapter. Mission, Nav2 and C2 code should progressively
consume the instance configuration instead of embedding `robot_01`; they must
not confuse an instance ID with a hardware type.

## Target repository structure

This is a gradual target, not a move scheduled for Phase 1:

```text
src/
├── robot_core/
├── robot_interfaces/
├── robot_adapters/
│   └── lite3/
├── sensors/
├── localization/
├── navigation/
├── safety/
├── missions/
└── operator/
config/
├── robots/
├── sensors/
├── navigation/
└── safety/
docs/architecture/
tests/
```

## Gradual migration plan

1. Keep deployed nodes and systemd units in place; wrap and test them first.
2. Make read-only operator/status code consume normalized `RobotState` and
   `RobotIdentity` without changing command paths.
3. Make command producers consult `RobotCapabilities` and `MotionLimits`, while
   retaining their existing lease and watchdog enforcement.
4. Add one Lite3 adapter implementation that delegates to the existing ROS
   endpoints; do not embed UDP or vendor codecs in the generic interface.
5. Move configuration ownership only after a deployed consumer and rollback
   path exist. Until then the new files describe/validate the target contract;
   existing launch/systemd configuration is operationally authoritative.
6. Formalize Mission Layer only after the adapter wrapper has parity tests.

## Decisions

- [ADR-001: vendor gait for product locomotion](decisions/ADR-001-vendor-gait-product-locomotion.md)
- [ADR-002: generic Robot Interface and Lite3 adapter](decisions/ADR-002-generic-interface-lite3-adapter.md)
- [ADR-003: low-level work remains R&D](decisions/ADR-003-low-level-rnd-separation.md)
- [ADR-004: onboard runtime and laptop operator split](decisions/ADR-004-onboard-runtime-laptop-operator.md)
