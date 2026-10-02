---
schema: bipolix.engineering_finding/v1
id: FINDING-20260921-001
title: MuJoCo contact geometry can create false unloading conclusions
date: 2026-09-21
status: DO_NOT_USE
categories: ROBOT_CONTROL, SAFETY, R_AND_D
evidence: docs/FR_ROBUST_SIMULATION_2026-09-21.md
---

# FINDING-20260921-001 - Simulation contact-model ambiguity

The native model allowed shank meshes to bear most of the simulated weight,
making foot-only load fractions meaningless. An earlier tool also aggregated
absolute contact normals and shank contacts rather than signed world-frame foot
Fz. Sphere-only normalization changed the interpretation materially.

- Evidence: [robust campaign](../../FR_ROBUST_SIMULATION_2026-09-21.md) and
  failed [TEST-20260921-001](../tests/TEST-20260921-001-fr-robust-unload-campaign.md).
- DO NOT REPEAT: equate a CoM inside the three-foot triangle, a safety pass, or
  foot-only fractions from native contact geometry with real unloading.
- Current alternative: calibrate contact/payload/actuator modeling and validate
  with independent physical load measurements before a lift search.

## Recovery provenance

Recovered from Git commit `173f61d` on 2026-10-02, preserving the original ID
and evidence classification. Recovery is a documentation operation, not a
new experiment, deployment, or independent physical validation.
