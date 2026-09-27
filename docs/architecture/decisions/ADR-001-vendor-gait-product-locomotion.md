# ADR-001: Use the vendor gait for product locomotion

- Status: Accepted
- Date: 2026-09-28

## Context

The Lite3 product path has physically demonstrated manual planar motion,
localization, autonomous Nav2 motion, obstacle avoidance, arrival and safe
AUTONOMY release through the existing DeepRobotics HIGH-LEVEL Motion Host
runtime. Nav2 produces planar velocity intent; the robot vendor controller owns
balance, gait generation and joint-level locomotion.

The repository also contains low-level and learned-policy work, but that work
has different evidence and safety requirements.

## Decision

Use the vendor HIGH-LEVEL gait/controller for patrol and product locomotion.
Nav2 and future missions issue generic planar velocity only through the existing
AUTONOMY lease and HIGH-LEVEL safety chain.

## Consequences

- Product software does not implement balance or joint trajectories.
- Vendor command encoding stays below the Lite3 adapter boundary.
- Low-level work cannot silently replace the product locomotion path.
