# Next mechanically supported front-right leg-lift test

## Status

**OFFLINE VALIDATION ONLY. NO HARDWARE RUN HAS BEEN AUTHORIZED OR EXECUTED.**

The new `leg_lift_once` action is a single bounded position-control sequence. It
does not use RL, velocity commands, raw torque, Nav2, lidar, or the vendor gait.
It is intended only for a mechanically supported robot with the operator holding
the emergency stop. It must not be run with the robot merely standing on the
ground.

## Exact requested motion

After the unchanged guarded stand reaches measured convergence, the action:

1. shifts the requested body position 5 mm rearward and 5 mm left over 2.0 s by
   moving all four foot targets 5 mm forward and 5 mm right relative to the body;
2. holds that shifted pose for 0.5 s;
3. raises only the front-right Cartesian foot target by 2 mm over 1.0 s;
4. holds the front-right target for 0.25 s;
5. lowers it over 1.0 s;
6. recenters the body over 2.0 s;
7. verifies the recentered stand for 0.5 s, closes the joint-send gate, and
   requests SDK ownership release.

The action uses IK-generated joint position targets. During the new sequence,
`kp` is at most 60, `kd` is at most 0.7, desired joint speed is at most
0.10 rad/s, each target stays within 0.03 rad of the standing pose, and
feed-forward torque is exactly zero. The largest sampled target displacement is
below 0.023 rad. The unchanged initial stand controller uses its existing gains.

Because live Lite3 foot-force channels have reported zero on all four legs, this
test does not claim contact detection or weight transfer. Mechanical support is
mandatory. This test validates only that the bounded target makes the supported
front-right leg move slightly upward and return.

## Independent aborts and limits

Both the state machine and the final hardware send boundary check the active
sequence. The gate closes and SDK release is requested on any of these conditions:

- stale or invalid feedback;
- roll or pitch greater than 3 degrees;
- measured joint speed greater than 0.50 rad/s;
- target tracking error greater than 0.15 rad;
- target displacement greater than 0.03 rad from the standing pose;
- target velocity greater than 0.10 rad/s;
- `kp` greater than 60, `kd` greater than 0.7, or nonzero feed-forward torque;
- invalid state, ownership request, send gate, or unforgeable permit;
- 7.5 s action deadline or 8 s permit expiry after leg-test entry;
- operator `stop`, SIGINT, SIGTERM, or shutdown.

Release removes commanded stiffness; the mechanical support must safely carry
the robot before, during, and after release.

## Preflight for the later supervised run

Immediately before a run, verify all of the following:

- the robot is mechanically supported so no leg is required to carry its weight;
- the area is clear and no person is under or beside a leg;
- the operator is holding the emergency stop;
- battery and robot health are acceptable;
- no handset, vendor gait, ROS node, Nav2 process, or other controller is active;
- telemetry is fresh, joints are stationary, IMU tilt is within limits, software
  velocity is exactly zero, and the send gate is closed;
- the executable hash and Git diff match the reviewed offline build.

Only after a fresh, exact approval for this plan may the console receive:

```text
acquire
leg_lift_once SUPPORTED_ESTOP_LEG_TEST_LIMITS_CONFIRMED
```

There is one attempt and no automatic retry. The console must then record the
full status progression and generated `/tmp/lite3-stand-trace-*.jsonl`, verify
automatic gate closure and release, and stop. Any unexpected movement, sound,
support loading, or posture is an immediate emergency-stop condition.

## Offline acceptance

The plan test samples the full trajectory at 1 kHz and checks IK, finite values,
joint displacement, target velocity, gains, zero feed-forward torque, the sole
front-right lift, return to stand, and completion. The inert state-machine test
uses an injected fake SDK transport and checks every phase, one-use behavior,
automatic release, and a tilt fault that aborts before another send.

Passing these tests proves command construction and software gating only. It does
not prove physical balance, unloading, clearance, contact, or hardware response.
