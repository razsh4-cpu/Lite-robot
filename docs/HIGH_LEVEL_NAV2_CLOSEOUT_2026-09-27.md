# Lite3 HIGH-LEVEL / Nav2 engineering closeout — 2026-09-27

## Scope and evidence rules

This handoff records the product/navigation path as it existed at end of day. It
separates hardware evidence from live software observations and offline tests.
It does not promote replay, static inspection, or a systemd `active` state to a
physical result.

Evidence labels used below:

- **PHYSICALLY PROVEN** — observed on the real Lite3 during an approved run.
- **LIVE SOFTWARE VALIDATED** — verified against the live Mini-PC/ROS graph with
  no inference of physical safety beyond what was observed.
- **OFFLINE TESTED** — unit/static/build checks only.
- **IMPLEMENTED BUT NOT PHYSICALLY TESTED** — present in source but needs a
  specific approved hardware test.
- **OPEN ISSUE** — known limitation or result not yet proven stable.

No new physical motion was performed for this closeout.

## End-of-day outcome

- **DAY 1 — COMPLETE.** HIGH-LEVEL telemetry, startup-relative odometry, LiDAR,
  TF, `Home_Map`, AMCL/localization, RViz, map/mapping workflow, and laptop C2
  were integrated and used on hardware. Localization acceptance remains gated
  at three consecutive samples `>=80%`.
- **DAY 2 — COMPLETE: AUTONOMOUS NAVIGATION + OBSTACLE AVOIDANCE WORKING.** A
  real end-to-end chair-avoidance mission completed through Nav2 and the guarded
  HIGH-LEVEL product path, reached the goal, stopped, and released ownership.

## Product architecture

```text
Sensors
  -> ROS 2
  -> Localization (Map Server + AMCL + confidence guard)
  -> Nav2
  -> /cmd_vel
  -> AUTONOMY command source
  -> exclusive Command Arbiter / lease
  -> persistent HIGH-LEVEL runtime
  -> DeepRobotics vendor gait
  -> Lite3
```

The persistent HIGH-LEVEL runtime is the only owner of Motion Host telemetry UDP
`43897`; it maintains heartbeat, telemetry, `/odom`, and `odom -> base_link`
independently of Xbox availability. Sources `NONE`, `LOCAL_XBOX`,
`LAPTOP_XBOX`, and `AUTONOMY` are mutually exclusive. `NONE` is the safe boot
source. Source transitions pass through neutral/zero and do not restore old
velocity or authorization.

The separate research path remains:

```text
Low-Level / MotionSDK / IK-FK / MuJoCo / ONNX / FR leg lift
```

Vendor Gait + ROS 2/Nav2 is the current patrol/product architecture. The
low-level branch is advanced-locomotion/Physical-AI R&D and must not be merged
into the product command path merely for convenience.

## Responsibility split

### Mini-PC (headless, robot critical)

- persistent HIGH-LEVEL runtime and the sole UDP `43897` receiver;
- heartbeat, telemetry, `/odom`, TF, LiDAR;
- Map Server, AMCL, localization guard/supervisor;
- Nav2, costmaps, safety monitor, AUTONOMY adapter, command arbiter;
- robot-side C2 and health/reliability monitoring.

The default boot target is `multi-user.target`. The robot must remain safe and
capable of executing an already authorized autonomous mission if the laptop is
absent.

### Laptop / C2

- RViz and all GUI visualization;
- Xbox device and operator/C2 relay;
- map, localization, posture, diagnostics, and mission operator CLIs;
- development, monitoring, and diagnostic snapshots.

RealSense D455 remains installed but is on-demand. The current Day-2 LiDAR Nav2
stack does not consume its RGB/depth/point-cloud streams.

## Timeline and evidence

### Runtime, DDS, odometry, and startup

1. **LIVE SOFTWARE VALIDATED:** a persistent HIGH-LEVEL runtime was separated
   from optional Xbox command sources. Xbox disconnect can revoke manual
   authorization and zero/release its source without terminating robot
   heartbeat, telemetry, `/odom`, or TF.
2. **LIVE SOFTWARE VALIDATED:** systemd `active` was found insufficient when a
   ROS node or DDS participant was absent. A HIGH-LEVEL ROS watchdog and
   readiness-based startup were added.
3. **OFFLINE TESTED / LIVE SOFTWARE VALIDATED:** localization startup now waits
   for network/DDS, fresh `/odom`, fresh `/scan`, Map Server lifecycle active,
   AMCL lifecycle active, required TF, then confidence. Lifecycle transitions
   use bounded retries; stuck localization is restarted as a stack after DDS
   cleanup. Status stages are `STARTING`, `WAITING_FOR_SCAN`,
   `WAITING_FOR_ODOM`, `WAITING_FOR_MAP_SERVER`, `WAITING_FOR_AMCL`,
   `UNLOCALIZED`, `LOCALIZED`, `NAVIGATION_READY`, and `STARTUP_FAILED`.
4. **LIVE SOFTWARE VALIDATED:** the saved per-map pose is an initial hypothesis,
   not a fixed physical start. A bounded AMCL global search follows failure to
   converge. Navigation is not ready until three consecutive match fractions
   are `>=0.80`.
5. **LIVE SOFTWARE VALIDATED:** the former `/odom` flood was approximately
   154 Hz. The sole Motion Host receiver now drains a bounded datagram burst and
   publishes only the newest valid RobotState once per 20 ms telemetry tick,
   capping `/odom` and TF at 50 Hz. This reduced executor/DDS pressure without
   adding another receiver.
6. **OFFLINE TESTED / LIVE SOFTWARE VALIDATED:** Nav2-to-AUTONOMY `/cmd_vel`
   uses sensor-data/BEST_EFFORT QoS where required. The AUTONOMY source applies
   an independent 300 ms stale-command watchdog and bounded velocity output.

### Localization operator workflow

- `relocalize status` is read-only.
- `relocalize` performs a read-only preflight and displays the exact bounded
  maneuver. It requires the literal approval prompt
  `Physical robot movement will occur. Continue? [y/N]`; default/Enter, `N`,
  invalid input, and Ctrl+C do not acquire ownership or send motion.
- `relocalize cancel` is intended to be idempotent: zero through the existing
  AUTONOMY path, stop the state machine, release ownership, and leave
  `COMMAND_SOURCE=NONE`. A stale/ghost AUTONOMY marker was encountered during a
  live run; the safe stop/release path recovered it. This cleanup remains an
  important regression target.
- Success requires the existing three consecutive `>=80%` gate. Saved map pose,
  map origin, LiDAR extrinsics, and odometry are not overwritten to manufacture
  confidence.

### Operator commands actually present

Run `commands` in a fresh laptop terminal for the maintained registry.
Implemented families at closeout:

- Robot: `robot status`, `robot stand`, `robot down`.
- Manual/C2: `connect joystick`, `disconnect joystick`,
  `c2 select robot robot_01`, `take control`, `release control`, `c2`.
- Map/localization: `status`, `maps`, `maps Home_Map`, `mapping`,
  `mapping --cancel`, `relocalize status`, `relocalize`,
  `relocalize cancel`.
- Navigation/validation: `day1-acceptance`, `day2-ready`, `prepare-day2`.
- System: `commands`.

The menu marks read-only, ownership, mode-changing, and physical-motion commands.
Wrappers source ROS 2 Jazzy and the required workspace automatically.

### Posture and C2

- **PHYSICALLY PROVEN:** `robot stand` acquired a temporary C2 lease while the
  source was `NONE`, used the existing HIGH-LEVEL `SIT_STAND` path, transitioned
  real telemetry from SITTING to STANDING, sent no translational/lateral/yaw
  velocity, stopped the posture command, and released back to
  `COMMAND_SOURCE=NONE` with zero remaining velocity.
- **IMPLEMENTED BUT NOT PHYSICALLY TESTED AS A DEDICATED CLI TEST:**
  `robot down` uses the supported HIGH-LEVEL posture path and the same guards.
- C2 fixes included boot-time `/run/lite3-control` permissions, robot-side
  service ordering after network/HIGH-LEVEL readiness, compatible ROS 2/DDS
  environment, real `robot_status`, temporary posture lease acquisition, and
  explicit recovery of stale/ghost command-source state.
- A disabled or disconnected source publishes a neutral/release boundary.
  Manual reconnect never restores old Stand authorization or velocity.

### HIGH-LEVEL reliability and neutral behavior

- **LIVE SOFTWARE VALIDATED:** the project observed cases where systemd remained
  `active` after the ROS node disappeared. Health now checks ROS graph/state and
  fresh telemetry, not only the unit state. The runtime has restart/watchdog
  behavior and startup ordering after network readiness.
- Heartbeat remains enabled at 4 Hz in the persistent runtime. Disabling it is
  guarded as an explicit heartbeat-loss experiment because Motion Host may
  lower the robot when heartbeat expires.
- A command source must own the lease and provide fresh input; otherwise the
  runtime remains connected and sends no motion request. Safe recovery leaves
  `COMMAND_SOURCE=NONE`.

### Headless Mini-PC optimization

**Measured before:**

- load average approximately `9.02 / 7.69 / 5.11`;
- RAM used approximately `1.7 GiB`;
- RealSense approximately `98%` of one CPU core.

**Measured after:**

- load average approximately `1.33 / 1.08 / 0.56`;
- RAM used approximately `1.0 GiB`;
- RealSense `0%` when unused;
- GUI not running.

The Mini-PC now boots to `multi-user.target`. Robot-critical services remain
onboard; RViz stays on the laptop. RealSense is preserved as an on-demand
service, and Nav2 remains available on demand.

### Network reliability

**Diagnosis: primarily `NETWORK LOSS`, not a proven full Mini-PC crash.** Boot
history contains controlled/real reboots, but the repeated “Mini-PC unavailable”
episodes did not provide evidence of kernel panic, OOM, thermal shutdown, or
filesystem failure. The strongest concrete evidence is the out-of-tree
`rtl8851bu` driver producing kernel UBSAN array-index-out-of-bounds errors and
creating concurrent station/AP-style interfaces (`wlxc03a55d2991a` and
`wlxc23a55d2991a`). A prepared fix pins NetworkManager to the station interface,
marks the AP interface unmanaged, disables Wi-Fi power saving, preserves the
existing `RobotDawg5.0` profile, and keeps static `192.168.2.32`.

**OPEN ISSUE:** the network fix is not yet proven over a long soak. Do not claim
closure until the management link survives repeated boots and mission load.
The lightweight persistent sampler records boot ID, load, memory/pressure,
temperatures, interfaces, disk, and top processes at:

```text
~/.local/state/lite3-reliability/health.jsonl
```

A root/system installation can additionally log under `/var/log/lite3-reliability`.

### RViz operator view

The canonical laptop configuration intentionally shows:

- static map in grayscale;
- live `/scan` in red;
- Lite3 body and live heading in blue;
- configured footprint in blue;
- preview goal and Nav2 path in distinct non-blue colors.

TF labels, odometry arrows, and colored global/local Costmap overlays are hidden
from the normal view. Costmaps, obstacle layers, and inflation remain active
internally. The body marker is centered on `base_link`, approximately
`0.610 x 0.370 m`, and its heading follows live `map -> base_link`.

### Nav2 footprint and safety

- measured physical body: approximately `0.610 x 0.370 m`;
- configured polygon: `0.710 x 0.470 m`, approximately 5 cm geometric margin
  on each side;
- `footprint_padding = 0.0 m`;
- `inflation_radius = 0.30 m`;
- `cost_scaling_factor = 4.0`;
- initial velocity limits: forward `0.10 m/s`, lateral `0.05 m/s`, yaw
  `0.20 rad/s`.

There is no double-counted footprint padding. Inflation is a graded obstacle
cost field for planning; it is not a second direct geometric enlargement of the
robot polygon.

### Path-clearance diagnostics

NavFn candidate poses frequently carry `yaw = 0` even while the path curves.
The first independent checker treated that value as physical body orientation,
rotated the rectangular footprint incorrectly, and produced false
collision/clearance results. The checker now derives orientation from the local
path tangent after the start pose, with a regression test for zero-yaw NavFn
paths.

The earlier insufficient snapshot could not reconstruct every limiting return.
The current dry-run snapshot tool preserves path candidates, scan, local/global
Costmaps, static map, TF, velocity limits, and metadata. Future obstacle
analysis must also retain per-pose clearance and the limiting obstacle/source so
results remain reproducible offline.

### Physical autonomous chair avoidance

#### Attempt 1 — physically useful, mission interrupted

**PHYSICALLY PROVEN:** the Lite3 detected and avoided the chair, travelled
approximately `1.64 m`, and exercised forward, lateral, and yaw motion through
the current AUTONOMY/HIGH-LEVEL product path. Localization remained about 92%.
Mission completion evidence was interrupted by Mini-PC power loss/reboot. This
was not evidence of a Nav2 planning/controller failure, but the action cannot be
recorded as a completed goal.

#### Attempt 2 — final accepted run

**PHYSICALLY PROVEN — `CHAIR AVOIDANCE TEST: PASS`:**

- avoidance side: RIGHT;
- Nav2 path length: approximately `1.47 m`;
- real NavigateToPose result: `SUCCEEDED` (`error_code=0`);
- Nav2 reached the short goal and the robot stopped;
- final localization: approximately `95.4%`;
- robot was STANDING at the recorded end of the accepted run;
- HIGH-LEVEL remained HEALTHY;
- AUTONOMY service stopped/released;
- final `COMMAND_SOURCE=NONE`.

The final path included lateral displacement; therefore lateral movement through
`Nav2 -> /cmd_vel -> AUTONOMY -> arbiter -> HIGH-LEVEL -> vendor gait` is now
physically demonstrated. This does not eliminate the need to preserve existing
limits and obstacle clearance for future environments.

## Validation matrix

| Capability | Status | Evidence / limitation |
|---|---|---|
| Persistent HIGH-LEVEL + sole UDP 43897 owner | LIVE SOFTWARE VALIDATED | Runtime, heartbeat, telemetry and odom remained independent of optional sources |
| Map Server/AMCL bounded lifecycle recovery | LIVE SOFTWARE VALIDATED + OFFLINE TESTED | Real startup/recovery exercised; long reboot soak still useful |
| Three consecutive localization samples >=80% | LIVE SOFTWARE VALIDATED + OFFLINE TESTED | Gated Nav2 runs; accepted chair run ended at 95.4% |
| Saved-pose hypothesis + global fallback | LIVE SOFTWARE VALIDATED | Manual motion was sometimes still needed to disambiguate |
| `relocalize` approval default-N | OFFLINE TESTED | Dedicated physical relocalize validation remains separate |
| `robot stand` | PHYSICALLY PROVEN | Temporary lease, telemetry confirmation, release to NONE |
| `robot down` CLI | IMPLEMENTED BUT NOT PHYSICALLY TESTED | Requires an approved dedicated run |
| Laptop Xbox/C2 | PHYSICALLY PROVEN | Stand and manual localization motion used; stale lease recovery observed |
| Nav2 goal/turn/lateral command path | PHYSICALLY PROVEN | Chair missions exercised forward/lateral/yaw |
| Chair avoidance | PHYSICALLY PROVEN | Final run succeeded and released to NONE |
| Headless boot/resource reduction | LIVE SOFTWARE VALIDATED | Measured before/after figures above |
| RTL8851BU reliability fix | OPEN ISSUE | Strong driver evidence; long soak not yet proven |
| Day-3 named goals | IMPLEMENTED BUT NOT PHYSICALLY TESTED | Registry skeleton contains gate/entrance/parking placeholders |

## Current safety invariants

1. Physical motion requires explicit operator approval for the exact run.
2. Only one command source owns the lease.
3. Nav2 never bypasses AUTONOMY or the command arbiter.
4. The 300 ms AUTONOMY watchdog zeros stale commands.
5. Stale scan, odom, telemetry, TF, unsafe localization, source changes, or
   abnormal command behavior trigger safe abort/release.
6. Startup and reconnection do not restore prior motion or authorization.
7. No second UDP `43897` receiver is permitted.
8. Map origin, LiDAR extrinsics, and footprint are not weakened to force a test.

## Open issues and next work

1. **HIGH value, offline:** implement Day-3 Mission Manager behavior around the
   existing named-location registry: named and ad-hoc goals, explicit approval,
   mission state, cancellation, safe observation points, and recorded result.
2. **HIGH value, offline:** strengthen reproducible diagnostic bundles for every
   mission (goal/action result, path, scan, costmaps, TF, localization and
   command-source transitions), keeping large captures outside Git.
3. **HIGH value, online:** validate one named 1–2 m goal and cancellation, then a
   short multi-goal mission, without repeating chair avoidance absent a new
   engineering question.
4. **MEDIUM value:** long network/boot soak using the persistent reliability
   sampler; correlate any disappearance with boot ID and driver counters.
5. **MEDIUM value:** a dedicated approved `robot down` CLI physical test.

Do not spend time now on broad refactoring, unconstrained Nav2 retuning after a
successful run, repeated chair tests for repetition, premature RealSense/AI
integration, or merging low-level/RL control into the patrol product path.

## Focused closeout validation

- `pytest`: **169 passed** across operator, C2, localization, startup, safety,
  arbitration, Nav2 static configuration, reconnect, posture, and mission tests.
- Python compilation and shell syntax: **PASS**.
- ROS 2 build: `lite3_state_estimation` **PASS**.
- `sensor_visualization` full laptop build: **environment-limited**, because the
  vendor MotionSDK `receiver.h` and
  `libdeeprobotics_legged_sdk_x86_64.so` are intentionally not present in this
  tracked/laptop tree. Static/unit tests passed; this is not a newly observed
  source regression.
- Fresh-shell command lookup and `commands`: **PASS**. Read-only `robot status`
  and `relocalize status` ran without manual ROS sourcing.
- Hardware motion commands sent during closeout: **NONE**.

## Repository contents introduced with this milestone

- `c2/`: laptop C2/Xbox relay and tests;
- `operator/`: map, posture, localization, Nav2, reliability and diagnostic CLIs;
- `laptop_visualization/`: canonical RViz config and single-instance watcher;
- `onboard_ros2_ws/src/lite3_state_estimation/`: HIGH-LEVEL odometry/localization;
- `onboard_ros2_ws/src/sensor_visualization/`: LiDAR, runtime, Nav2, safety,
  services, systemd units, tests and engineering notes.

Generated `build/`, `install/`, `log/`, Python caches, `.orig` files, private
configuration, and large host diagnostic captures are intentionally excluded.
