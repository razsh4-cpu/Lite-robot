# Lite3 test catalog foundation

No test in this catalog is authorized merely by being listed. Live tests require
an experiment record, exact preflight, abort readiness and explicit approval.

| ID | Test / mode | Objective | PASS | FAIL / ABORT | Existing evidence |
|---|---|---|---|---|---|
| T001 | Boot recovery / LIVE no-motion | Prove network→HIGH-LEVEL→odom/scan→localization startup deterministically reaches a real ready or exact failed stage | Core ROS nodes/topics/TF and lifecycle recover without manual restart; source `NONE` | FAIL on stuck/false-ready stage; ABORT service changes if heartbeat/posture risk appears | LIVE SOFTWARE VALIDATED; long soak still useful |
| T002 | Robot status / OFFLINE+LIVE read-only | Report connection, posture, HIGH-LEVEL, ownership and localization from real state | Accurate values; offline target fails quickly and clearly; no ownership | FAIL on traceback, stale value presented as live, or any command | OFFLINE TESTED and live used |
| T003 | Stand / LIVE motion | Use guarded posture path without planar motion | SITTING→STANDING in telemetry; planar velocity zero; temporary lease released to NONE | FAIL if no transition/cleanup; ABORT on unexpected gait/motion, stale state or unhealthy link | PHYSICALLY PROVEN |
| T004 | Down / LIVE posture | Safely lower through supported guarded path | Standing/down preflight, confirmed final posture, zero motion and source NONE | FAIL on unconfirmed posture/lease; ABORT on active mission or unexpected motion | IMPLEMENTED; dedicated physical test pending |
| T005 | Manual control / LIVE motion | Validate laptop Xbox direction mapping and safe release | Approved forward/back/lateral/yaw respond correctly within limits; disconnect/stop neutralizes and releases | FAIL wrong axis/continued motion; ABORT stale telemetry, unsafe motion or loss of operator stop | PHYSICALLY PROVEN in prior manual/localization work |
| T006 | Command arbiter / OFFLINE+LIVE no-motion | Prove one owner only and no takeover | Each source acquires only from NONE; competing source refused; release returns NONE | FAIL dual owner, stale owner not cleaned safely, or unauthorized source accepted | OFFLINE TESTED; live source transitions observed |
| T007 | 300 ms watchdog / OFFLINE then LIVE bounded | Prove stale command becomes zero and ownership releases | Command loss yields zero/release inside defined tolerance; old velocity never restored | FAIL continued/non-zero command; ABORT live test on any abnormal response | OFFLINE TESTED + LIVE SOFTWARE VALIDATED |
| T008 | LiDAR / LIVE no-motion | Verify device identity, `/scan`, frame and stable obstacle returns | Fresh stable scan in `lidar_link`; expected object detected; health OK | FAIL stale/wrong frame/duplicate driver; no motion needed | LIVE SOFTWARE VALIDATED |
| T009 | Odometry / LIVE controlled motion | Verify startup origin, direction and approximate displacement | Fresh `/odom`, sole publisher/TF owner; measured path consistent with physical displacement within declared test tolerance | FAIL jump, wrong axis/yaw, competing publisher; ABORT unexpected robot motion | Physical 1 m-style validation performed; product runs further exercised odometry |
| T010 | Saved-map localization / LIVE mostly no-motion | Load map and achieve accepted pose | Correct map; scan alignment; three consecutive confidence samples ≥80%; correct live heading | FAIL false LOCALIZED or wrong alignment; ABORT/stop Nav2 if localization invalid | PHYSICALLY/LIVE PROVEN on Home_Map |
| T011 | Relocalization / OFFLINE then LIVE bounded motion | Recover when saved hypothesis cannot converge | Explicit default-no approval; bounded recovery only after yes; ≥80%×3 or clean UNLOCALIZED; zero/release | FAIL ownership before approval or stale cleanup; ABORT obstacle/TF/scan/odom/telemetry/posture issue | Approval/cancel OFFLINE TESTED; live manual/global localization used; dedicated CLI motion test partial |
| T012 | Nav2 short goal / LIVE motion | End-to-end goal→path→AUTONOMY→arrival | Valid safe path, bounded command, meaningful displacement, SUCCEEDED, stop and NONE | FAIL no progress/unsafe tracking/incorrect terminal state; ABORT stale data, unsafe clearance or localization loss | Short physical navigation exercised during Day 2; accepted chair goal is stronger evidence |
| T013 | Nav2 turn/lateral goal / LIVE motion | Validate heading change and holonomic command path | Planned turn/lateral behavior tracked within safety limits and arrives | FAIL wrong direction/unstable controller; ABORT abnormal rotation/lateral motion or clearance | PHYSICALLY PROVEN in chair runs |
| T014 | Obstacle avoidance / LIVE motion | Detect chair→costmap→safe path→avoid→arrive | Obstacle real in scan/costmap; no contact; NavigateToPose SUCCEEDED; stop/release NONE | FAIL missing obstacle/contact/path through obstacle; ABORT insufficient clearance or stale inputs | PHYSICALLY PROVEN: ~1.47 m right-side chair avoidance, 95.4% final localization |
| T015 | Mission cancel / OFFLINE/integration then LIVE | Future mission cancellation propagates to Nav2 and safe release | Terminal CANCELLED, zero command, AUTONOMY release, evidence preserved | FAIL continued motion/ownership or old mission resumes; ABORT live test on cleanup uncertainty | PLANNED; Mission Layer not implemented |

## Evidence policy

- `PHYSICALLY PROVEN` refers to the recorded configuration and ODD, not all
  future sites or parameter combinations.
- Offline variants should use fixtures/inert transports and prove negative
  paths before a live test.
- A live test records software/config/calibration/site revisions and final
  `COMMAND_SOURCE`.
- T004, dedicated T011 and T015 remain open; their absence must not be hidden
  by adjacent successful tests.
