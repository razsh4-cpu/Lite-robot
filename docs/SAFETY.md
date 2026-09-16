# Safety contract

## Supervised conditions

- Original controller/E-stop available; clear floor and leg area.
- Fresh telemetry, known state 6, battery >=25% (prefer >35% for mapping).
- Exactly one control process; start neutral; one bounded action, no auto retry.

## Fail closed

- Command/deadman/telemetry older than 300 ms -> neutral.
- Non-state-6, unknown/low battery, malformed or non-finite input -> neutral.
- Shutdown -> five redundant neutral packets.

Abort on unexpected direction/posture, instability, telemetry/odometry loss,
fault/protection state, inability to stop or uncertain command ownership.

Never bypass gates, run competing controllers, use `KEEP_STEPPING`, retry
legacy 320/321/325, inject tty data, or enable Nav2 motion before acceptance.

