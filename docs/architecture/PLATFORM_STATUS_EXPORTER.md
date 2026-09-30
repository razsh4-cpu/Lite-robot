# Platform Status Exporter

The Lite3 platform-status exporter is a read-only adapter from existing
Bipolix authorities to the vendor-neutral `robot.platform_status/v1`
snapshot consumed by NOMAD.

It does not decide robot state and does not provide control. It reads the
authoritative `/run/lite3-control` state files, systemd/lifecycle observations,
and ROS status topics, validates freshness, and atomically replaces
`/run/lite3-control/platform_status.json`.

Unavailable or stale inputs remain explicit. In particular, service activity
alone is never treated as proof of fresh telemetry, localization, or sensor
data. The exporter contains no MQTT client, command publisher, action client,
robot UDP socket, ownership acquisition, posture path, or command-source
writer.

Current source ownership:

- command source and owner: `/run/lite3-control/COMMAND_SOURCE` and flock state;
- localization state/score/startup: localization guard files under
  `/run/lite3-control`;
- odometry, battery and robot-state freshness: the existing HIGH-LEVEL ROS
  topics;
- LiDAR/D455: their existing sensor topics plus service state;
- TF: the established `map -> odom -> base_link -> lidar_link` chain;
- Nav2: existing lifecycle/action/service observations;
- health/refusal: existing health and startup state files plus measured input
  freshness.

The output schema is fixed at version 1 and always reports
`motion_commands_supported: false` for this integration phase.
