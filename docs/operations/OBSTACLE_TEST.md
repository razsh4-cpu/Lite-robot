# Built-in obstacle avoidance test

The laptop command `nav test obstacle` wraps the already proven product path:

`Nav2 -> /cmd_vel -> AUTONOMY -> Command Arbiter -> HIGH-LEVEL -> Lite3`

It does not create another controller, arbiter, Nav2 stack, odometry publisher,
or UDP receiver.

## Commands

- `nav test obstacle status` is read-only. It never starts Nav2, acquires a
  lease, or sends motion.
- `nav test obstacle` performs preflight, starts only the existing
  `lite3-nav2.service` when the navigation layer is the sole missing item,
  records a bounded diagnostic snapshot, computes candidate paths, and stops
  at an explicit `[y/N]` physical-motion approval prompt.
- `nav test obstacle cancel` is idempotent. It cancels NavigateToPose, stops the
  existing AUTONOMY adapter, releases its lease, and removes any test override.

## Localization policy

Normal navigation always requires `>=80%` for three consecutive samples.

If and only if localization is stable at `>=70%` for three samples and every
other preflight check passes, the obstacle command may offer a separate,
explicit 70% test override. The operator must approve the override before it is
created and must separately approve physical motion after seeing the path.

The override is a validated JSON token in `/run/lite3-control`, applies only to
the obstacle test, expires after at most 180 seconds, and is removed on PASS,
FAIL, cancel, exception, AUTONOMY stop, or reboot. A missing, stale, malformed,
or modified token restores the normal 80% gate. Falling below 70% during the
test aborts the mission.

## Preflight

The test requires standing posture, healthy HIGH-LEVEL and telemetry, fresh
scan and odometry, complete TF, active Map Server and AMCL, correct localization
gate, active planner/controller/BT Navigator, fresh global and local costmaps,
one UDP 43897 receiver, no active mission, `COMMAND_SOURCE=NONE`, and an
available AUTONOMY lease.

Always verify the `MAP` line in `nav test obstacle status`. A high-quality scan
cannot localize against the wrong saved map. Selecting a map and remapping are
different operations; a wrong active map must be corrected by loading the
already-created map, not by changing AMCL, the map origin, or LiDAR extrinsics.

## Diagnostics

Each explicit planning session is stored under
`~/lite3_diagnostics/obstacle/<session-id>/`. It contains the scan, odometry,
static map, local/global costmaps, TF snapshot, AMCL covariance, localization,
all returned candidate paths, selected goal/path, raw and padded footprint,
inflation settings, per-pose clearance and limiting obstacle. During execution
it additionally records bounded `/cmd_vel` evidence, result, ownership
transitions, and final robot state.

Footprint clearance uses the path tangent for NavFn paths whose pose yaw is not
meaningful. The raw body is `0.610 x 0.370 m`; the configured footprint is
`0.710 x 0.470 m`, with `footprint_padding=0.0` and
`inflation_radius=0.30 m`. These values are never reduced to force a path.

## Recovery messages

- `OBSTACLE TEST BLOCKED` means at least one required gate failed.
- `NO TEST OBSTACLE DETECTED` means no relevant live LiDAR return was confirmed
  in a costmap.
- `NO SAFE PATH` means the saved footprint/clearance policy rejected all
  candidates.
- `OBSTACLE TEST READY` means the normal 80% gate passed and the command is
  waiting for physical-motion approval.
- `READY FOR CONTROLLED 70% CHAIR AVOIDANCE TEST` means the temporary test gate
  is active and the command is waiting for the separate motion approval.

RViz remains manual/on-demand. The obstacle CLI does not enable or start the
RViz watcher.

## Deployment after an offline update

With the Mini-PC online and `COMMAND_SOURCE=NONE`, run:

```bash
/home/raz/ros-robot-cc/Lite-robot/operator/deploy_nav_obstacle_test.sh
```

The script verifies hostname `abx-fit-001`, copies only the obstacle-test and
localization-policy files, builds the two existing ROS packages, clears any
stale `/run` override, and restarts localization plus the Nav2 safety monitor.
It does not start Nav2, AUTONOMY, posture, or motion. Restarting localization
may require normal AMCL convergence again.

After deployment, first select/verify the correct map, then run:

```bash
nav test obstacle status
```

Only when the status identifies the intended map should the operator run
`nav test obstacle`.
