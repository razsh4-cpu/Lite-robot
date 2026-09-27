# Lite3 C2 Xbox prototype

The laptop publishes Xbox input only to the one `selected_robot` namespace.
The robot-side relay owns the filesystem command-source lease and is the only
component that can select `LAPTOP_XBOX`. The persistent high-level runtime still
applies neutral-edge, A/RB authorization, standing, telemetry, timeout and
velocity gates.

The user service starts with `manual_enabled=false`; it cannot acquire a robot
at login. Selection and manual enable are explicit:

```bash
ros2 param set /lite3_c2_xbox selected_robot robot_01
ros2 param set /lite3_c2_xbox manual_enabled true
```

Before selecting a different robot, disable manual control. Changing
`selected_robot` also publishes neutral/release to the old robot and resets the
internal manual-enable state. Xbox loss, process loss, network loss or stale
messages cause the robot relay to publish neutral and release `LAPTOP_XBOX` to
`NONE` within 300 ms. Reconnect never restores authorization or motion.

## Fast diagnosis

The required robot status topic is:

`/c2/robot_01/laptop_xbox/robot_status`

If it is missing, check `192.168.2.32` with ping before diagnosing ROS. A
powered-off Mini-PC and a DDS discovery failure can produce the same topic
error. The complete decision tree is in
[`TROUBLESHOOTING.md`](../onboard_ros2_ws/src/sensor_visualization/docs/TROUBLESHOOTING.md).

When the robot is already standing, use a centered RB rising edge for fresh
manual authorization. A is the vendor SIT/STAND toggle and can make an already
standing robot lie down. Neither `connect joystick` nor lease acquisition sends
Stand or non-zero motion by itself.
