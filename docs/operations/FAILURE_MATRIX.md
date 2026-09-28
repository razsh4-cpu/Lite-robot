# Safety and failure matrix

Status means the response is `IMPLEMENTED`, `PARTIAL`, or `PLANNED`; it does
not promote offline evidence to physical proof.

| Failure | Detection | Required response | Owner | Status |
|---|---|---|---|---|
| LiDAR `/scan` stale | Nav2 safety/readiness freshness probe | Block acquisition or abort navigation; zero/release AUTONOMY | Nav2 safety monitor + AUTONOMY source | IMPLEMENTED |
| `/odom` stale | Nav2 safety/health freshness probe | Block/abort navigation; zero/release | Nav2 safety monitor + AUTONOMY source | IMPLEMENTED |
| Required TF unavailable/stale | localization/Nav2 readiness | Remain unready; block or abort navigation | localization + Nav2 | IMPLEMENTED |
| Localization below gate | confidence guard (`>=0.80` for three consecutive samples to enter ready) | Block AUTONOMY; abort on invalid/prolonged loss according to active guard | localization guard + AUTONOMY | IMPLEMENTED |
| `/cmd_vel` stale/invalid | source validation and 300 ms watchdog | Publish safe zero, release AUTONOMY | AUTONOMY source | IMPLEMENTED |
| Xbox/C2 input stale or disconnected | request/heartbeat/Joy freshness | Neutral, revoke manual authorization, release source; keep HIGH-LEVEL alive | owning manual source | IMPLEMENTED |
| HIGH-LEVEL ROS-dead/systemd-active | ROS graph, telemetry freshness, watchdog | Block motion and recover persistent runtime without restoring ownership | HIGH-LEVEL watchdog/systemd | IMPLEMENTED |
| Robot telemetry stale | HIGH-LEVEL freshness gate | Suppress non-zero output; upstream zero/release | HIGH-LEVEL + source | IMPLEMENTED |
| Competing command source | kernel lease and source marker | Refuse acquisition; do not steal ownership | Command Arbiter/source lease | IMPLEMENTED |
| Source process partial failure / ghost marker | lock, process and marker reconciliation | Zero if owned, clear authorization, release to `NONE` | source cleanup | PARTIAL |
| Nav2 action failure | action result/controller state | Stop command stream and abort action; future mission policy records result | Nav2; future Mission Layer | PARTIAL |
| Mini-PC restart | systemd startup and source initialization | Start with `COMMAND_SOURCE=NONE`; never restore velocity/authorization | platform startup | IMPLEMENTED |
| Laptop/network loss during LAPTOP_XBOX | C2 heartbeat timeout | Neutral and release LAPTOP_XBOX; onboard safety continues | C2 robot-side relay | IMPLEMENTED |
| Laptop loss during onboard autonomy | C2/network health | Autonomous execution may continue only while onboard safety inputs remain valid | onboard autonomy/safety | PARTIAL |
| Battery below navigation threshold | battery telemetry / safety monitor | Abort navigation, zero and release; no automatic posture policy yet | Nav2 safety monitor | PARTIAL |
| Storage full / black-box unavailable | future storage health | Report degraded; preserve motion safety; bound/delete evidence by policy | Health/Logging | PLANNED |
| CPU overload / missed deadlines | load/latency health | Degrade/abort affected operation based on stale-data guards | Health/Safety | PARTIAL |
| LiDAR physically blocked/mis-mounted | scan quality + calibration validation | Block localization/navigation; require inspection | Sensor Management | PLANNED |
| Low battery return-home/down policy | battery policy | Mission-aware return or controlled safe posture | future Mission Layer + Safety | PLANNED |

The deployed mechanisms named above remain authoritative. This matrix does not
create a second supervisor or permission path.

