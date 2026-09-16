# Control and sensor stack

Dry run:

```bash
source /opt/ros/jazzy/setup.bash
source /home/abx/ros2_ws/install/setup.bash
ros2 launch sensor_visualization lite3_cmd_vel_vendor_gait.launch.py transmit:=false
```

Passive LiDAR/SLAM:

```bash
ros2 launch sensor_visualization lite3_lidar_slam.launch.py
```

Current TF is `base_link -> lidar_link` at `(0,0,0.08 m)`, yaw `pi`. ICP uses
correspondence ratio 0.50 and reset countdown 3. SLAM uses `odom`/`base_link`.

Tests:

```bash
pytest -q src/sensor_visualization/test/test_lite3_control_safety.py \
  src/lite3_security_patrol/test
```

See `EVIDENCE_INDEX.md` and `EXPERIMENTS.md`.

