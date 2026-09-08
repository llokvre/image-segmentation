# Risk-aware V1 / A2 reproducibility snapshot

This directory freezes the source, tests, protocols, and compact evidence available when the A2 fold 0 five-condition benchmark was completed.

## Contents

- `design/`: Risk-aware V2 engineering design, resolved decisions, readiness checklist, and source touchpoints.
- `core/`: Stage 1 mathematical core, API documentation, tests, and compact validation log.
- `availability/`: Stage 2A availability integration, nnU-Net trainer, tests, and compact validation log.
- `training/`: A2 fold 0 protocol, preflight metadata, launch/monitor helpers, and the exact trainer package snapshot used by the launcher.
- `inference/`: Stage 2C availability-aware adapter, predictor, protocol, tests, and compact smoke evidence.
- `results/`: compact text summaries only; no medical images, prediction volumes, or checkpoints.

## Frozen scope

- A0 Full-only: complete.
- A1 Modality Dropout: complete.
- A2 Modality Dropout + Explicit Availability: complete; availability decision = **WEAK**.
- Next stage: Teacher Qualification.
- Current research hypothesis: **missingness-conditioned selective privileged distillation**; not yet validated.

Teacher, knowledge distillation (KD), vulnerability, and reliability components are not implemented in this snapshot. This repository does not contain BraTS data, NIfTI volumes, prediction volumes, model weights, full training logs, runtime outputs, credentials, or archives.
