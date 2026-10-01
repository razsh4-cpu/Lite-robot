# Current engineering state

Updated: 2026-10-01. This summary is evidence-bounded; it is not a live health
check.

## Physically proven

- guarded supported Stand and cleanup;
- laptop Xbox/C2 manual path in the prior product workflow;
- RPLIDAR-backed mapping/localization and `Home_Map` operation;
- Nav2 through AUTONOMY/arbiter/HIGH-LEVEL/vendor gait;
- accepted right-side chair avoidance, goal success, stop, and final
  `COMMAND_SOURCE=NONE`.

## Live-static proven

- saved-map localization using the normal `>=80%` ×3 gate;
- real Mini-PC Phase-3B exporter/MQTT/gateway integration with fail-closed
  offline robot state and no physical output;
- headless/on-demand resource reduction snapshots.

## Offline proven

- relocalize approval/cancel cleanup;
- Robot Interface/contracts and architecture invariants;
- NOMAD Phase-1 status, Phase-2 authority reservation, and Phase-3A mock
  TeleopIntent safety chain;
- guarded Phase-3C adapter logic and tests at commit `35c8173`, with later
  working-tree readiness/exporter changes not yet promoted to physical proof.

## Blocked or untested

- first real NOMAD Phase-3C browser/Xbox locomotion remains unexecuted;
- dedicated `robot down` physical CLI acceptance;
- full physical relocalize CLI session;
- Mission and Patrol physical execution;
- D455 perception/Nav2 integration;
- long-soak closure for rtl8851bu/network reliability.

## Next planned physical test

[TEST-20261001-002](tests/TEST-20261001-002-phase3c-xbox-physical.md): one
bounded forward/STOP sequence through the protected Phase-3C Xbox path. It is
`PLANNED`, requires separate approval, and has no result yet.

Primary baselines: [known-good product baseline](../testing/KNOWN_GOOD_BASELINE.md)
and [Day-2 closeout](../HIGH_LEVEL_NAV2_CLOSEOUT_2026-09-27.md).
