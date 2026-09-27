# ADR-003: Keep low-level MotionSDK/ONNX work as a separate R&D path

- Status: Accepted
- Date: 2026-09-28

## Context

The repository contains guarded low-level validation, supported-stand,
body-shift, leg-lift and ONNX experiments. Their validation permits, ownership
model and hardware evidence differ from the HIGH-LEVEL vendor-gait product
stack. The patrol MVP already has a working HIGH-LEVEL path.

## Decision

Preserve low-level/MotionSDK/ONNX code as an isolated R&D path. Do not couple it
to the generic product Robot Interface or use it for patrol locomotion unless a
future decision follows its own ordered safety milestones and evidence review.

## Consequences

- Existing validation-console restrictions remain unchanged.
- Product architecture cannot import low-level controllers as an implicit
  fallback.
- R&D may continue without destabilizing the patrol MVP.
