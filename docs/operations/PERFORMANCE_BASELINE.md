# Performance baseline and headroom

These are observed snapshots from the headless Mini-PC optimization, not
capacity guarantees or benchmark distributions.

| State | Load average | RAM used | RealSense | GUI |
|---|---:|---:|---:|---|
| Before headless/on-demand cleanup | `9.02 / 7.69 / 5.11` | about `1.7 GiB` | about `98%` of one CPU core | running/available in onboard workload |
| After cleanup | `1.33 / 1.08 / 0.56` | about `1.0 GiB` | `0%` when unused | off; RViz runs on laptop |

The current Day-2 product workload keeps robot-critical HIGH-LEVEL, LiDAR,
odometry/TF, localization, Nav2, safety and robot-side C2 onboard. D455
processing is on-demand because current LiDAR Nav2 does not consume it.

## Performance headroom concept

Headroom is the measured margin between nominal workload and a defined failure
threshold across CPU/load, memory/pressure, scheduling latency, DDS/topic
freshness, temperature and storage. A release baseline should record sustained
and peak values during boot, localization, planning and navigation—not only one
idle snapshot.

Initial future acceptance should establish:

- per-core CPU and load during representative missions;
- RAM, swap and PSI memory/CPU/I/O pressure;
- `/scan`, `/odom`, TF, telemetry and command end-to-end latency/jitter;
- thermal state and throttling under sustained load;
- storage growth and evidence-retention limits;
- safety watchdog behavior under controlled overload.

Do not optimize further from these two snapshots alone. First reproduce the
workload, measure the limiting resource and protect safety timing. Moving a
robot-critical or latency-sensitive component to the laptop merely to lower
load is not an acceptable optimization.

