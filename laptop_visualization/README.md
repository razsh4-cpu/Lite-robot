# Lite3 laptop visualization

This is visualization-only. RViz and the watcher run on the development laptop;
the Mini-PC owns the LiDAR and continues independently when the laptop is off.

The watcher polls every 10 seconds and requires a real `/scan` message before it
opens RViz. It never starts a LiDAR driver and never publishes robot commands.
Only one RViz process using `lite3_remote_lidar.rviz` is managed. If robot data
disappears after RViz opens, the existing window remains open and the event is
logged; no new window is spawned.

Commands:

```bash
systemctl --user status lite3-rviz-watcher.service
systemctl --user restart lite3-rviz-watcher.service
systemctl --user stop lite3-rviz-watcher.service
journalctl --user -u lite3-rviz-watcher.service -f
systemctl --user disable --now lite3-rviz-watcher.service

# Manual visualization (independent of the watcher)
source /opt/ros/jazzy/setup.bash
rviz2 -d /home/raz/ros-robot-cc/laptop_visualization/lite3_remote_lidar.rviz
```

The fixed frame is `base_link`, verified from the Mini-PC's static transform
`base_link -> lidar_link`. The configuration currently enables LaserScan and TF;
RobotModel, map, odometry, localization, Nav2 paths and costmaps can be added as
those topics become available.
