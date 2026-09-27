# Gradual architecture migration plan

Rule: wrap → define contracts → test → migrate gradually. Every step keeps a
rollback and retains the hardware-proven path until parity is demonstrated.

## Target repository structure

```text
src/
├── robot_core/             # normalized state and platform orchestration
├── robot_interfaces/       # vendor-neutral contracts
├── robot_adapters/
│   ├── lite3/
│   └── simulation/         # future
├── sensors/                # management and health, not drivers duplicated
├── state_estimation/
├── localization/
├── navigation/
├── perception/
├── safety/
├── missions/               # future Day 3+
└── operator/
config/
├── robots/{types,instances}/
├── navigation/
├── localization/
├── sensors/
├── safety/
└── missions/
calibration/<robot_id>/
sites/<site_id>/
docs/architecture/
tests/{contracts,integration,acceptance}/
```

This is a target, not a request to move the current ROS workspace wholesale.

## Ordered migration

### Baseline — complete in this phase

- Inventory real nodes, services, topics, actions, owners and machines.
- Define generic Robot Interface, identity, capability and health vocabulary.
- Record safety, TF, data, sensor, deployment and machine boundaries.
- Preserve existing runtime code and configuration authority.

### 1. Read-only adapter integration

- Add a Lite3 adapter facade that reads existing topics/state and produces the
  generic `RobotState`/health model.
- It opens no UDP socket and publishes no command.
- Compare facade output with existing `robot status`, health and telemetry in
  offline fixtures, then live read-only acceptance.

### 2. Shared arbitration contract

- Extract common lease semantics behind a tested safety API while existing
  source services continue to enforce behavior.
- Prove acquisition, refusal, heartbeat, timeout, zero and cleanup parity for
  NONE/LOCAL_XBOX/LAPTOP_XBOX/AUTONOMY.
- Deploy one source at a time with rollback; never run old/new owners together.

### 3. Configuration consumers

- Add schema/version validation and remove duplicated magic numbers only when
  the current operational consumer is migrated.
- Split robot type from robot instance.
- Move Nav2/localization/sensor values by reference or generated deployment
  artifact, not by keeping two writable sources of truth.

### 4. Calibration registry

- Capture the current LiDAR extrinsic as a versioned robot-specific calibration
  record with method/evidence.
- Make the launch consume the record after static and live comparison.
- Add camera/IMU/motion records only after measurement; never invent values.

### 5. Sensor and health interfaces

- Normalize per-subsystem health while retaining real topic/lifecycle probes.
- Define optional RealSense profiles and ultrasonic validation separately from
  required LiDAR navigation.
- Add resource and storage diagnostics to the aggregate model.

### 6. Mission Layer (future Day 3)

- Implement mission contracts only after robot/safety interfaces are stable.
- Named and ad-hoc targets resolve to Nav2 goals; Mission Manager owns mission
  state, not path planning or velocity.
- Alert workflows generate safe observation-pose proposals.

### 7. Simulation adapter and acceptance parity

- Implement a clearly identified simulation adapter.
- Reuse mission/navigation orchestration and non-hardware safety tests.
- Keep simulation results distinct from live hardware acceptance.

### 8. Reproducible deployment and data lifecycle

- Package versioned software/config/calibration/site manifests.
- Add staged update, validation, rollback, backup and restore.
- Build an installer only after deployment artifacts and rollback are proven.

## Do not migrate yet

- `lite3-high-level-runtime.service` or UDP 43897 ownership;
- vendor packet codec/command IDs;
- `/odom` and `odom→base_link` production ownership;
- AMCL `map→odom` ownership;
- current LiDAR extrinsic or map origin;
- AUTONOMY 300 ms watchdog and source cleanup;
- C2/Xbox release behavior;
- Nav2 controller/planner/costmap behavior;
- low-level validation/MotionSDK/ONNX R&D;
- physically validated maps and per-map hypotheses.

## Acceptance per migration

Every migration records: old/new owner, dependency direction, config schema,
offline tests, relevant full regression suite, deployment steps, rollback,
hardware command evidence and explicit live acceptance when required. No
offline or simulation result is labeled hardware validation.
