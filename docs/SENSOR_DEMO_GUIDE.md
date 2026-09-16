# Lite3 sensor capability demo — D455 and RPLIDAR S2

This is a **sensor-only** demonstration. It does not command the Lite3, run Nav2,
run SLAM, or acquire MotionSDK control.

## What is running

| Sensor | ROS 2 topic | Frame | Meaning |
|---|---|---|---|
| RPLIDAR S2 | `/scan` | `laser` | A horizontal, 2D 360-degree range scan |
| D455 RGB | `/camera/camera/color/image_raw` | `camera_color_optical_frame` | Normal colour video |
| D455 depth | `/camera/camera/depth/image_rect_raw` | `camera_depth_optical_frame` | Distance at each depth-camera pixel |
| D455 aligned depth | `/camera/camera/aligned_depth_to_color/image_raw` | `camera_color_optical_frame` | Depth resampled into RGB pixel coordinates |
| D455 point cloud | `/camera/camera/depth/color/points` | `camera_depth_optical_frame` | Reconstructed 3D XYZ points, with RGB fields when supplied by the driver |

## RPLIDAR S2 — simple explanation

The LiDAR sends out laser light in one flat horizontal plane. `/scan` is a list of
angles and distances. It is excellent for walls, chair legs, and obstacle clearance
at the height where it is mounted.

It is **not** 3D: it cannot see a table top above its plane, and it can miss a low
or high obstacle entirely. A displayed 2D LiDAR scan converted into dots is still
a single flat plane, not a 3D cloud.

## D455 — simple explanation

* **RGB** answers: “what does the scene look like?”
* **Depth** answers: “how far is this pixel?”
* **Aligned depth** means the depth value at an RGB pixel refers to that same visual
  direction. This is what later lets a detected person pixel become an approximate
  3D observation.
* **Point cloud** turns depth pixels plus camera calibration into XYZ points, so it
  shows surfaces and object shape in 3D in front of the camera.
* **IMU** measures acceleration and rotation cues. It does not by itself provide a
  reliable position; do not integrate raw acceleration to create fake odometry.

## Demo procedure

1. Open the RViz configuration:

   ```bash
   source /opt/ros/jazzy/setup.bash
   source /home/abx/ros2_ws/install/setup.bash
   rviz2 -d /home/abx/ros2_ws/install/sensor_visualization/share/sensor_visualization/rviz/lite3_sensor_demo.rviz
   ```

2. In RViz, the point cloud is shown in the D455 depth optical frame. The LaserScan
   uses its own `laser` frame deliberately. There is **no measured transform**
   between D455 and LiDAR yet, so these displays are not claimed to be spatially
   fused.

3. To check RGB/depth alignment, put a flat object at the image centre at a known
   approximate distance, then run:

   ```bash
   ros2 run sensor_visualization d455_center_depth_probe
   ```

   The probe reports the median of a 9×9 centre region from the *aligned* depth
   image. Compare it with a tape-measure distance; it is a sensor check, not a
   calibration certificate.

4. Move an object only around the sensors (not the robot). The LiDAR change appears
   as a 2D arc/range return; the D455 point cloud changes as a 3D surface.

## Engineering notes

### 2D scan versus a 3D point cloud

`/scan` has one distance for each angle around one plane. A `PointCloud2` contains
XYZ coordinates, reconstructed from depth image pixels and D455 intrinsics. Nav2
can use a 2D scan for obstacle costmaps; perception can use RGB plus aligned depth
for a person or object location.

### Why TF matters

Every measurement is meaningless without knowing the frame in which it was made.
The RealSense driver provides its camera optical-frame transforms. Future robot
integration needs accurately measured, rigid transforms:

```
base_link
├── lidar_link          # MEASURE_ON_ROBOT
└── camera_link         # MEASURE_ON_ROBOT
    ├── camera_color_optical_frame  # supplied by driver
    └── camera_depth_optical_frame  # supplied by driver
```

Do not invent `base_link → lidar_link` or `base_link → camera_link`. Wrong transforms
make localization, obstacle maps, and perceived object positions wrong even if each
sensor stream itself is perfect.

### Current session limitation

The D455 is currently on a USB 2 (480 Mb/s) link. The reduced 640×480, ~15 Hz
profile is suitable for a basic demonstration but has less margin and may show raw
depth timing jitter. Use a certified direct USB 3 SuperSpeed data cable/port before
the full RGB+depth+IMU robot integration. IMU was not enabled in this USB2 demo.

## Evidence labels

* **PROVEN_FROM_CURRENT_PROJECT:** current topics, published frame IDs, and live
  stream rates are observed at runtime.
* **SUPPORTED_BY_OFFICIAL_DRIVER_DESIGN:** aligned depth and driver optical TF frames
  are RealSense ROS driver capabilities.
* **REQUIRES_PHYSICAL_TEST:** the final sensor mounting transform, range accuracy in
  the mounted location, and USB3 sustained reliability.

## The full future chain

```
physical world
 → D455 / RPLIDAR
 → ROS 2 driver
 → image, depth, PointCloud2, LaserScan topics
 → correct sensor TF
 → odometry + localization
 → Nav2 costmaps / perception
 → Mission Manager decision
 → separately safety-gated robot action
```

A person detector must publish an observation to the Mission Manager, not command
the robot directly. If timestamps, TF, or a sensor stream go stale, the Mission
Manager must treat that observation as unreliable and use a safe recovery policy.
