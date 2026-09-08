# Risk-aware V1 Stage 1 Core API

Status: shared deterministic mathematics only. This module is not integrated
into an nnU-Net Trainer.

## Constants and ordering

- Modality order: `[T1n, T1c, T2w, FLAIR]`
- Region order: `[WT, TC, ET]`
- `DEFAULT_ALPHA = 1.0`
- `DEFAULT_LAMBDA_REGION = 0.2`
- `DEFAULT_WEIGHT_CLAMP = (0.5, 1.5)`
- `DEFAULT_SMOOTH = 1e-5`

All APIs are CPU/GPU-agnostic, but Stage 1 validation uses CPU only. No public
function reads files, performs random sampling, accesses the network, or
modifies nnU-Net.

## Public functions

### `validate_availability(availability, *, batch_size=None, device=None) -> Tensor`

- Input: bool, integer, or floating binary tensor `[B,4]`.
- Output: detached float32 tensor `[B,4]` on the same device.
- Gradient: deliberately disabled by detaching.
- Errors: wrong rank/channel count/batch, non-binary or non-finite values,
  complex dtype, or requested device mismatch.

### `apply_availability_to_mri(data, availability) -> Tensor`

- Input: floating finite MRI `[B,4,D,H,W]`; availability `[B,4]`.
- Output: non-inplace zero-filled MRI with the same shape, dtype, and device.
- Gradient: supported for `data`; disabled for availability.
- Errors: shape, dtype, finite, batch, binary, or device violations.
- It never infers availability from zero-valued MRI voxels.

### `broadcast_availability(availability, spatial_shape, dtype, device) -> Tensor`

- Input: availability `[B,4]`, positive `(D,H,W)`, floating MRI dtype/device.
- Output: constant channels `[B,4,D,H,W]`.
- Gradient: disabled; no trainable parameter is created.
- Errors: invalid spatial shape/dtype, availability, or device mismatch.
- No normalization or augmentation is applied.

### `build_eight_channel_input(data, availability) -> Tensor`

- Input: MRI `[B,4,D,H,W]`, availability `[B,4]`.
- Output: `[B,8,D,H,W]` in exact order
  `[T1n,T1c,T2w,FLAIR,a_T1n,a_T1c,a_T2w,a_FLAIR]`.
- Gradient: supported for MRI values; availability is detached.
- Performs zeroing, broadcasts masks, concatenates, then asserts consistency.
- Does not modify `data`.

### `build_region_targets(target) -> Tensor`

- Input: labels `[B,1,D,H,W]` or `[B,D,H,W]`, values only `{0,1,2,3}`.
- Output: float32 `[B,3,D,H,W]` with WT=`{1,2,3}`, TC=`{1,3}`, ET=`{3}`.
- Device: preserved. Gradient: not applicable to class labels.
- Errors: invalid shape/channel/dtype/value or non-finite floating labels.

### `logits_to_region_probabilities(logits) -> Tensor`

- Input: finite floating four-class logits `[B,4,D,H,W]`.
- Output: `[B,3,D,H,W]`; softmax uses `dim=1`, then
  `P_WT=P1+P2+P3`, `P_TC=P1+P3`, `P_ET=P3`.
- Dtype/device: preserved. Gradient: supported.
- Background is not an output region.

### `per_sample_region_soft_dice_loss(region_probabilities, region_targets, *, smooth=1e-5) -> Tensor`

- Inputs: matching floating `[B,3,D,H,W]` tensors on one device.
- Output: `[B,3]`, retaining each sample and WT/TC/ET region.
- Formula:
  `1-(2*sum(P*Y)+smooth)/(sum(P)+sum(Y)+smooth)`.
- No squaring, no background, no early batch mean, and no empty-GT skip.
- Empty/empty gives zero; empty/nonempty gives a positive finite penalty.
- Gradient: supported through probabilities.

### `compute_risk_weights(availability, risk_matrix, *, alpha=1.0, weight_clamp=(0.5,1.5)) -> Tensor`

- Inputs: availability `[B,4]`; frozen floating nonnegative matrix `[4,3]`.
- Output: detached `[B,3]` WT/TC/ET weights with per-sample mean one.
- Formula: missing indicator, matrix product, `1+alpha*s`, mean normalize,
  clamp, then mean re-normalize exactly as V2.
- Full availability is exactly `[1,1,1]`.
- Errors: shape/dtype/device/finite/binary violations, negative risk, invalid
  alpha/clamp, or `risk_matrix.requires_grad=True`.

### `weighted_region_loss(per_sample_region_loss, region_weights) -> Tensor`

- Inputs: matching floating `[B,3]`.
- Output scalar:
  `mean_b((w_WT*L_WT+w_TC*L_TC+w_ET*L_ET)/3)`.
- Gradient: supported through loss, not through detached weights.
- Full-modality weights therefore equal the un-biased three-region mean.

### `combine_total_loss(base_loss, region_loss, *, lambda_region=0.2) -> Tensor`

- Inputs: finite scalar floating tensors on one device.
- Output: `base_loss + lambda_region * region_loss`.
- Does not recompute base loss. Gradient is supported for both scalar inputs.

### `deep_supervision_region_loss(outputs, targets, deep_supervision_weights, availability, risk_matrix, ...) -> Tensor`

- Inputs: output and target lists/tuples with equal scale count, explicit scale
  weights, availability `[B,4]`, and frozen risk matrix `[4,3]`.
- Each output is `[B,4,Dj,Hj,Wj]`; each already-downsampled target is
  `[B,1,Dj,Hj,Wj]` or `[B,Dj,Hj,Wj]`.
- Output: scalar weighted scale sum.
- It never resamples targets. Zero-weight scales do not contribute.
- Availability/risk weights are shared across scales.
- Errors: list length, scale shape, batch, weight, dtype/device, and finite
  violations.
- Gradient: supported through every positive-weight output.

## Future ablation integration boundary

- A2 will use availability zeroing/broadcast/8-channel construction only.
- A3 will keep a 4-channel network and use availability solely for risk weights
  and region loss.
- A4 will use both 8-channel construction and risk-weighted region loss.
- Trainer subclasses, predictor wrappers, random ModDrop sampling, calibration,
  NIfTI, checkpoint loading, and real-data execution are outside Stage 1.
