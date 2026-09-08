# Stage 2C A2 Missing-Modality Inference Protocol

## Scope

This stage performs inference only with the frozen A2 fold 0 `checkpoint_best.pth`.
It does not train, alter checkpoints, preprocess Dataset501 again, or run a formal benchmark.

## Explicit patterns

The fixed MRI order is T1n, T1c, T2w, FLAIR. The only accepted explicit patterns are:

- `full`: `[1, 1, 1, 1]`
- `t1n`: `[0, 1, 1, 1]`
- `t1c`: `[1, 0, 1, 1]`
- `t2w`: `[1, 1, 0, 1]`
- `flair`: `[1, 1, 1, 0]`

Availability is never inferred from voxel values. The frozen Stage 1/A2 primitives perform
MRI zeroing, availability broadcasting, and `[MRI4, availability4]` concatenation.

## Sliding-window contract

Each prediction call requires `missing_pattern`. Before sliding-window inference, the
preprocessed `[4,D,H,W]` tensor becomes `[8,D,H,W]`. Every network crop is asserted to
contain eight channels, constant availability channels, and exact zeroing for missing MRI.
The installed nnU-Net TTA implementation shifts configured mirror axes by two, so only
spatial dimensions are flipped; the channel dimension is never mirrored.

## Bounded smoke test

The smoke case is the lexicographically first case in fold 0 validation. Exactly two
predictions are permitted for that one case: `full` and `t1c`. Outputs are restricted to
`runtime/full/` and `runtime/missing_t1c/`. These smoke Dice values are not an A1/A2 comparison.
