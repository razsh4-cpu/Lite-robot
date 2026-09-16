#!/usr/bin/env bash
set -euo pipefail

cd /home/abx/ros2_ws
set +u
source /opt/ros/jazzy/setup.bash
set -u

python3 -m py_compile \
  src/sensor_visualization/scripts/*.py \
  src/sensor_visualization/launch/*.py

colcon build --packages-select sensor_visualization --symlink-install
set +u
source install/setup.bash
set -u
colcon test --packages-select sensor_visualization --event-handlers console_cohesion+
colcon test-result --verbose

# Isolate the synthetic ROS graph from normal desktop/robot ROS nodes.
export ROS_DOMAIN_ID=88
python3 src/sensor_visualization/tools/lite3_ros_chain_test.py
python3 src/sensor_visualization/scripts/lite3_telemetry_watchdog.py --self-test
python3 src/sensor_visualization/scripts/lite3_offline_preflight.py

echo "OFFLINE_VALIDATION=PASS"
echo "ROBOT_COMMANDS_SENT=0"
