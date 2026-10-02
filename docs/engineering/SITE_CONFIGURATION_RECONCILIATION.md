# Site configuration reconciliation

2026-10-02, based solely on the approved read-only Mini-PC snapshot and source comparison. No setting changed on the Mini-PC or promoted to defaults.

| Configuration | Classification | Evidence / unresolved applicability |
|---|---|---|
| SABLE repo motion caps0.5/0.3/0.6 | CANONICAL source defaults | Preserved; defaults are not physical SI calibration |
| Deployed caps2.0/1.5/2.0 | SITE_SPECIFIC; rationale UNKNOWN | Effective override only; no recovered justification or physical acceptance |
| Deployed odom_sign[1,1,1] versus repo[-1,1,1] | SITE_SPECIFIC; calibration UNKNOWN | No measured sign acceptance recovered; do not copy |
| SABLE ROS domain23/LOCALHOST | SITE_SPECIFIC | Product service configuration; preserve existing source discovery policy; domain itself not readiness |
| Legacy exporter domain0/status constants | STALE for target readiness; diagnostic applicability UNKNOWN | Different domain/runtime; do not infer current robot offline or strafe validated |
| Local edge broker1885 | SITE_SPECIFIC | Product deployment broker purpose observed; protected bridge destination unreadable |
| Teleop20Hz/deadman0.5s, driver0.4s | CANONICAL code and matching captured overrides | Network and physical stop timing unvalidated; general MQTTTTL15s is a separate contract |
| Axis vendor format in deployed bringup | CANONICAL supported product profile | Standalone config still supports nav variant; framing not physical acceptance |
| Camera on / SLAM launch | SITE_SPECIFIC | Different from historical on-demand D455/Home_Map AMCL; do not inherit historical PASS |
| Older local-Xbox units/staging/R&D checkout | SUPERSEDED target architecture / historical diagnostics | Presence is not active service or competing writer proof |
| MPPI on AVX-less J6413 | SUPERSEDED known-bad hardware choice | CPU fallback reimplemented offline; installed dependency/runtime acceptance still pending |
| Initial direct-ONNX gait/contact model tuning | EXPERIMENTAL | Research-only, not product deployment |

Primary: [deployed audit](MINIPC_DEPLOYED_STATE_AUDIT.md), [snapshot](evidence/MINIPC_READ_ONLY_20261002.json). Secret-bearing broker configuration remains unread; no credentials retained.
