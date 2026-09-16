# Lite3 ROS 2 autonomy workspace

Engineering workspace for a DeepRobotics Lite3 security/patrol robot on ROS 2
Jazzy. It contains a proven vendor-gait control path, passive telemetry and
watchdog, RPLIDAR S2 bringup, ICP odometry, and LiDAR SLAM scaffolding.

Start with [ROBOT_HANDOFF.md](ROBOT_HANDOFF.md), then read:

- [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)
- [docs/SAFETY.md](docs/SAFETY.md)
- [docs/EVIDENCE_INDEX.md](docs/EVIDENCE_INDEX.md)
- [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md)

## Build

```bash
source /opt/ros/jazzy/setup.bash
cd /home/abx/ros2_ws
colcon build --packages-select sensor_visualization lite3_security_patrol --symlink-install
source install/setup.bash
```

Passive LiDAR + odometry + mapping (no robot-control node):

```bash
ros2 launch sensor_visualization lite3_lidar_slam.launch.py
```

Vendor-gait control with transmission safely disabled:

```bash
ros2 launch sensor_visualization lite3_cmd_vel_vendor_gait.launch.py transmit:=false
```

Only set `transmit:=true` during a supervised session under `docs/SAFETY.md`.
Large bags and raw JSONL are excluded; their hashes are in the evidence index.
No Telegram token or other secret belongs in Git.

