# A2 Fold 0 Availability Benchmark Summary

## Experiment identity

- Dataset: BraTS 2023 GLI
- Backbone: nnU-Net v2 `3d_fullres`
- Fold: 0
- A1: Modality Dropout
- A2: Modality Dropout + Explicit Availability
- Benchmark completeness: 1255/1255 predictions PASS

## A2 results

| Condition | WT | TC | ET | Mean |
|---|---:|---:|---:|---:|
| Full | 0.93461020 | 0.91254931 | 0.87157229 | 0.90624393 |
| Missing T1n | 0.93498348 | 0.91039477 | 0.86396869 | 0.90311564 |
| Missing T1c | 0.92922966 | 0.81458839 | 0.65283265 | 0.79888357 |
| Missing T2w | 0.93035692 | 0.91093994 | 0.86898677 | 0.90342788 |
| Missing FLAIR | 0.90415494 | 0.90822155 | 0.86379868 | 0.89205839 |

## A2 versus A1

| Comparison | Paired mean difference |
|---|---:|
| Full Mean | -0.00093919 |
| Missing T1c TC | +0.00506348 |
| Missing T1c ET | -0.00119277 |
| Missing T1c Mean | +0.00196931 |
| Missing FLAIR WT | +0.00258751 |

## Frozen decision

**Availability = WEAK.**

Availability alone is not promoted as a core methodological contribution. It may remain as an explicit missing-pattern conditioning variable. The available fold 0 evidence must not be described as statistically significant, as robust improvement, or as state of the art (SOTA).

The current research hypothesis is **missingness-conditioned selective privileged distillation**. This is a future hypothesis, not a validated method. Teacher, knowledge distillation (KD), vulnerability, and reliability components have not been implemented.
