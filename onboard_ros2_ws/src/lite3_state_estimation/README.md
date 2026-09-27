# Lite3 high-level state bridge

Receive-only bridge for the vendor Motion Host telemetry stream. It publishes
`/odom`, `/imu/data`, `/joint_states`, `odom -> base_link`, robot basic state,
battery, and freshness. It creates no command socket and sends no robot packet.

The Motion Host stream is unicast UDP to port 43897. Therefore this bridge is
the sole receiver while running and deliberately refuses socket reuse. Stop it
before starting another runtime that owns the same telemetry socket.

High-level telemetry contains no contact-force field and no source timestamp.
Contact force is therefore not published; ROS receipt time is used and the
limitation is explicit. Joint velocity and effort are also absent and remain
empty in `JointState`.

`day1_localization.launch.py` consumes `/odom` and `odom -> base_link` from the persistent `lite3-high-level-runtime.service`; it must not start another high-level telemetry receiver
with the existing saved map and AMCL (`map -> odom`). It does not start Nav2,
publish an initial pose, or command the robot. The map cannot be considered
localized until an initial pose and a supervised motion validation are done.
