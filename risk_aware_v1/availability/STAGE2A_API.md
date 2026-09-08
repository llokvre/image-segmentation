# Risk-aware V1 Stage 2A API

Status: synthetic integration/smoke level only. No full training or real-case
inference has started.

## A2 Trainer

- File: `nnUNetTrainerModDropAvailabilityMask.py`
- Class: `nnUNetTrainerModDropAvailabilityMask`
- Parent: `nnUNetTrainer`
- Reason for direct parent: the active A1 class performs ModDrop inside its
  `train_step`. Calling that parent method would sample a second missing pattern.
  A2 instead preserves the same control flow in a new class and samples once.

### Real-signature overrides

```python
@staticmethod
def build_network_architecture(
    plans_manager: PlansManager,
    configuration_manager: ConfigurationManager,
    num_input_channels: int,
    num_output_channels: int,
    enable_deep_supervision: bool = True,
) -> nn.Module

def train_step(self, batch: dict) -> dict

def validation_step(self, batch: dict) -> dict
```

The builder asserts Dataset501 reports four MRI inputs and delegates to the
unchanged parent builder with `num_input_channels=8`. Output heads, backbone,
initialization, deep supervision, loss, optimizer, schedule, and all formal
training settings remain parent-defined.

## Availability integration

File: `availability_integration.py`

Public functions:

- `sample_modality_dropout_with_availability(data, probability=0.5)`
- `assert_availability_matches_mri(original_data, masked_data, availability, *, require_full=False)`
- `build_a2_input(original_data, masked_data, availability)`
- `build_full_validation_input(data)`

Stage 1 is imported from:

`/root/autodl-tmp/nnunet_brats/risk_aware_v1_implementation_stage1/risk_aware_core.py`

The adapter reuses Stage 1 validation, deterministic zeroing, broadcast, and
eight-channel construction rather than copying the mathematics.

## A1-preserving sampler

The active A1 policy is preserved exactly:

1. Data has already passed the existing augmentation pipeline.
2. Each sample independently triggers ModDrop with probability `0.5`.
3. A triggered sample uniformly selects one of four MRI modalities.
4. Exactly that channel is absent; non-triggered samples remain Full.
5. The single sampled pattern creates both the zero-filled MRI and `[B,4]`
   availability. It is never sampled twice or inferred from MRI zeros.

Train flow:

`augmented MRI -> one pattern -> availability -> Stage 1 zeroing -> Stage 1 broadcast/concat -> 8-channel network -> original nnU-Net loss`

Channel order:

`[T1n MRI, T1c MRI, T2w MRI, FLAIR MRI, a_T1n, a_T1c, a_T2w, a_FLAIR]`

Validation uses explicit `[1,1,1,1]` for every sample and never calls the random
sampler.

## Checkpoint boundary

The A1 checkpoint first convolution has four input channels. A2's actual first
convolution has eight. The old checkpoint is intentionally incompatible and is
not loaded into A2. A2 uses the same nnU-Net random initialization protocol and
will write only to its distinct Trainer result directory during future formal
training.

## Parameter counts

Counts from actual Dataset501 `3d_fullres` network construction:

- A1 four-channel parameters: `31,199,796`
- A2 eight-channel parameters: `31,203,252`
- Increase: `3,456`
- Only changed parameter shape:
  `encoder.stages.0.0.convs.0.conv.weight`, input dimension 4 -> 8

All other parameter shapes, five deep-supervision heads, four output classes,
and network initialization code are unchanged.

## Current and future scope

- Implemented now: A2 Trainer, one-pattern integration, CPU unittest, real
  network construction, synthetic CPU and single synthetic GPU smoke tests.
- Not implemented: predictor, A3, A4, risk calibration, NIfTI I/O.
- Not executed: optimizer step, checkpoint save, epoch, full training, or
  real-case inference.

Future formal training template (documentation only; **not executed**):

```bash
PYTHONPATH=/root/autodl-tmp/nnunet_brats/risk_aware_v1_implementation_stage2a:$PYTHONPATH \
nnUNetv2_train 501 3d_fullres 0 \
  -tr nnUNetTrainerModDropAvailabilityMask
```
