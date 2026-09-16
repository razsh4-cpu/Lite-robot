# Architecture

## Control

```text
operator/future autonomy -> /cmd_vel + deadman -> safety adapter
  -> normalized forward/yaw -> telemetry-gated vendor-axis node
  -> SimpleCMD UDP 43893 -> jy_exe vendor gait -> physical motion
```

ROS commands are bounded requests, not a calibrated SI-speed contract. Future
Nav2 commands must pass through this same arbitration/deadman/safety path.

## Monitoring

```text
Lite3 UDP 43897 -> passive decoder -> state/battery/freshness -> watchdog
                                                       -> Telegram (optional)
```

Raw packet health and valid RobotState freshness are separate. Battery is
current only with fresh RobotState; otherwise it is explicitly last-known. The
watchdog never sends robot packets.

## Mapping

```text
world -> RPLIDAR -> /scan [lidar_link] -> static TF
  -> ICP [odom->base_link, /odom] -> SLAM [map->odom, /map] -> RViz
```

A healthy `/scan` alone does not prove healthy odometry or localization.

