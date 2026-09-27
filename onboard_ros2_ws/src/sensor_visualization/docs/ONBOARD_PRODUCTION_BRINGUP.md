# Onboard production bringup

Production manual control uses the Lite3 vendor high-level Motion Host protocol.
It does not use the ONNX low-level controller.

## Headless Mini-PC boot

The onboard computer normally boots to `multi-user.target`; the Mint desktop is
kept installed but is not part of robot startup. Robot, network, SSH, LiDAR,
localization and health services are system services and do not require a
graphical login. The D455 remains installed but is on-demand because the
current LiDAR Nav2 stack has no subscribers to its image, depth or point-cloud
topics.

```bash
lite3-headless status
sudo lite3-headless start-gui          # temporary recovery desktop
sudo lite3-headless stop-gui           # return this boot to headless
sudo lite3-headless graphical-default  # GUI on subsequent boots
sudo lite3-headless headless-default   # headless on subsequent boots
sudo lite3-headless realsense-start    # optional D455 workload
sudo lite3-headless realsense-stop
```

Changing the default target never commands posture or motion. After any boot,
`COMMAND_SOURCE` must remain `NONE` until an operator explicitly selects a
command source.

For live failures, start with
[TROUBLESHOOTING.md](TROUBLESHOOTING.md). It records the proven power, C2,
localization, Fast DDS, telemetry, and Nav2 diagnostic paths.

## Readiness states

- `SYSTEM_READY`: Mini-PC completed non-motion startup.
- `LIDAR_READY`: a real `/scan` message was received.
- `MANUAL_CONTROL_AVAILABLE`: `/dev/input/js0` is the trusted Xbox controller.
- `AUTONOMY_READY`: currently `false`; reserved for the future autonomy source.
- `COMMAND_SOURCE`: `NONE`, `LOCAL_XBOX`, `LAPTOP_XBOX`, or `AUTONOMY`.

Only one source can hold `/run/lite3-control/owner.lock`. Xbox absence does not
fail startup. Restarting `lite3-xbox.service` opens a new finite 25–30 second
connection window.

## Xbox mapping

- `A`: edge-triggered vendor sit/stand toggle; sticks must be centered. This
  is not a state-aware Stand-only command, so do not press it when the robot is
  already standing.
- `RB`: one fresh authorization edge when the robot is already standing. It
  does not need to be held as a deadman switch.
- Left stick up/down: forward/backward.
- Left stick left/right: lateral left/right (corrected physical sign).
- Right stick left/right: yaw left/right; combine with left stick for arcs.
- Other buttons/triggers: unused.

After Stand or an already-standing RB authorization, fresh state 6, fresh
telemetry, and a centered-stick observation are required before velocity is
accepted. Joystick data older than 300 ms, malformed input, controller loss,
stale telemetry, or a non-standing robot all force zero velocity. Disconnect
revokes manual authorization and releases the source lease, but the persistent
HIGH-LEVEL runtime, heartbeat, telemetry, `/odom`, and TF remain active.

## Commissioning interlock

`/etc/default/lite3-high-level-xbox` initially sets `TRANSMIT=false` and
`ZERO_ONLY=true`. This permits a no-motion readiness test. Enabling real packets
is a separate supervised step after explicit approval.
