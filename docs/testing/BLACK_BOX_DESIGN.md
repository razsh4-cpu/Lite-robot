# Experiment recorder / black-box design

This is a small future interface, not a logging-platform implementation.

## Operator contract

```text
test start <experiment_name>
  → validate name and free recorder session
  → capture immutable metadata and preflight snapshot
  → start bounded topic/event recording
  → print session_id and recording state

test stop
  → stop/flush recorders
  → capture final health/ownership/action snapshot
  → write result skeleton and checksums
  → print experiment directory
```

`test start` and `test stop` must never acquire a motion lease, must never publish
a motion or posture command, and do not authorize the experiment. Motion approval
remains a separate operator/safety action.

## Target artifact

```text
runs/<session_id>/
├── metadata.yaml
├── events.jsonl
├── diagnostics_start.json
├── diagnostics_end.json
├── rosbag2/
├── result.yaml
└── checksums.sha256
```

Metadata records robot ID/type, site/map, experiment name/question, operator,
start/end times, software commit/release, config/calibration versions, ODD,
limits and evidence class. Events record approvals, source acquisition/release,
service/lifecycle changes, action feedback/result, faults, watchdog stops and
operator aborts.

## Default topic/evidence profile

- `/scan`, `/odom`, `/tf`, `/tf_static`;
- `/cmd_vel` and protected command output when a physical motion test is
  explicitly approved;
- `/localization/status`, `/amcl_pose`, `/map` metadata/reference;
- Nav2 action/status/path and relevant costmap metadata;
- `/lite3/battery_percent`, `/lite3/ultrasound` and normalized robot state when
  available;
- command-source state/lease transitions and system-health snapshot;
- systemd journal cursor and diagnostic command output.

Large static map/costmap/point-cloud streams use an explicit profile rather than
unbounded default recording. RealSense is not started by the recorder.

## Ownership and failure behavior

The onboard recorder owns time-critical robot evidence; the laptop may request,
observe and copy a completed session. Laptop/network loss must not corrupt the
onboard session. Recording uses bounded storage/retention and reports degraded
state. Recorder failure never disables a safety stop or holds command ownership.

An unclean shutdown is recovered as `INCOMPLETE`, never `PASS`. Temporary files
are finalized atomically where possible. Credentials, Bluetooth secrets and
unrelated personal data are excluded.

## Minimum safe implementation path

1. Wrap the existing `lite3_bag_recorder.py`, reliability snapshot and journal
   queries without changing them.
2. Add schema validation and one-session locking.
3. Test start/stop/crash/disk-full entirely offline.
4. Validate read-only capture live before using it with physical motion.

Do not implement automatic test motion inside the recorder.
