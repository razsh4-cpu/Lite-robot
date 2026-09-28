# Patrol MVP requirements baseline

Status meanings:

- **PROVEN** — physically demonstrated on the Lite3 or directly observed live.
- **PARTIAL** — implemented/tested, but evidence or operational coverage is incomplete.
- **PLANNED** — architectural requirement only; not a delivered product capability.

| ID | Requirement | Status | Evidence / remaining boundary |
|---|---|---|---|
| MVP-001 | The operator can create and save a map of a new site without automatic robot motion. | PROVEN | `Home_Map` was created through the SLAM/operator workflow; production-map acceptance uses validation rather than SLAM completion alone. |
| MVP-002 | The robot can load a saved map and localize using a saved pose only as an initial hypothesis. | PROVEN | Home map, AMCL confidence gate and global fallback were exercised live. |
| MVP-003 | Navigation is enabled only after three consecutive localization measurements ≥80%. | PROVEN | Gate used before accepted autonomous chair run; run ended at ~95.4%. |
| MVP-004 | The robot can plan and autonomously navigate to a valid nearby goal. | PROVEN | Real NavigateToPose result `SUCCEEDED`, error code 0. |
| MVP-005 | The robot detects LiDAR-visible obstacles and plans around them with its configured footprint. | PROVEN | Physical chair avoidance on the right side, approximately 1.47 m planned path. |
| MVP-006 | Autonomous motion uses only AUTONOMY → arbiter → HIGH-LEVEL → vendor gait. | PROVEN | Accepted chair test used this end-to-end path and released to `COMMAND_SOURCE=NONE`. |
| MVP-007 | A stale command produces zero within the current 300 ms watchdog and releases ownership. | PROVEN | Offline tests and live software validation; retained as a mandatory regression. |
| MVP-008 | The operator can take over with laptop Xbox and release safely. | PROVEN | Manual localization motion and posture operation used C2/LAPTOP_XBOX with neutral/release. |
| MVP-009 | The operator can stand the robot without translational/lateral/yaw velocity. | PROVEN | `robot stand` physically validated with telemetry confirmation and temporary lease cleanup. |
| MVP-010 | The operator can command the supported down posture through the guarded CLI. | PARTIAL | Implemented with existing posture path; dedicated physical CLI test not yet recorded. |
| MVP-011 | Critical stale LiDAR, odometry, localization, telemetry or command data blocks/aborts navigation. | PARTIAL | Individual guards and tests exist; complete live fault-injection matrix is not yet demonstrated. |
| MVP-012 | Robot-critical heartbeat, telemetry and safety continue without the laptop or internet. | PROVEN | Persistent headless onboard runtime is independent of optional laptop/Xbox/GUI. |
| MVP-013 | System startup validates ROS/lifecycle/topic readiness rather than systemd `active` alone. | PROVEN | Readiness-based localization/HIGH-LEVEL recovery was live software validated. |
| MVP-014 | A patrol mission executes multiple named locations with observable results and cancel. | PLANNED | Mission contracts and dormant named-location scaffold only; Day 3 not started. |
| MVP-015 | A mission may target an operator-selected ad-hoc map pose. | PLANNED | Architectural target; direct Nav2 engineering goals exist but no Mission API. |
| MVP-016 | An alert produces a safe observation pose rather than blindly using the alert coordinate. | PLANNED | Architecture defined; no alert/perception mission implementation. |
| MVP-017 | The robot records bounded mission/fault/operator evidence for regression and diagnosis. | PARTIAL | Journal, rosbag and focused diagnostics exist; unified session recorder is designed only. |
| MVP-018 | Software/configuration/calibration/site data can be versioned, backed up and rolled back independently. | PLANNED | Data boundaries and target manifests defined; deployment lifecycle not implemented. |

This requirement set describes the first patrol MVP. It does not claim stairs,
rough-terrain autonomy, outdoor navigation, charging, fleet operation or AI
perception.
