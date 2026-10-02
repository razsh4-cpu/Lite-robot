---
schema: bipolix.engineering_finding/v1
id: FINDING-20261002-011
title: Updated gateway source must become the running deployed process
date: 2026-10-02
status: RESOLVED
categories: DEPLOYMENT, NOMAD
evidence: /home/raz/ros-robot-cc/NOMAD/scripts/edge/deploy_bipolix_phase3b.sh
---

# FINDING-20261002-011 — Updated gateway source must become the running deployed process

## Finding and applicability

Nested NOMAD commit 6df9c00 repairs the deploy path to restart updated gateway units and adds deployment regression coverage. The later a0cda36 written live non-motion result is related integration evidence. A source copy or successful build alone does not show that the running process uses it; retain version/unit/process provenance and separate offline repair from installed validation.

This is retrospective knowledge capture on 2026-10-02. Root cause, exact
configuration/run SHA, and retest measurements remain `UNKNOWN` wherever the
source does not establish them. A resolved software defect is not a completed
physical acceptance or reliability soak.

## Evidence and relationships

- [deploy_bipolix_phase3b.sh](../../../../NOMAD/scripts/edge/deploy_bipolix_phase3b.sh).
- [BIPOLIX_NON_MOTION_MVP.md](../../../../NOMAD/docs/integrations/BIPOLIX_NON_MOTION_MVP.md).

- Related records: [TEST-20261001-001](../tests/TEST-20261001-001-nomad-phase3b-live-static.md), [FINDING-20260929-001](FINDING-20260929-001-source-of-truth.md).
- DO NOT REPEAT: erase a failure/refusal after a later pass, transfer proof
  between command paths, or substitute configuration/source presence for
  measured physical or deployed behavior.
