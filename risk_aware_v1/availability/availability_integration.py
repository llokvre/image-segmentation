"""A2 adapter around the tested Stage 1 availability primitives.

No random policy is duplicated outside :func:`sample_modality_dropout_with_availability`.
The function intentionally mirrors the active A1 implementation's random-call
order: one per-sample Bernoulli draw, followed (only when needed) by one
per-sample channel draw.  The resulting single pattern drives both MRI zeroing
and the explicit availability vector.
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch
from torch import Tensor

STAGE1_DIRECTORY = Path(
    "/root/autodl-tmp/nnunet_brats/risk_aware_v1_implementation_stage1"
)
STAGE1_CORE = STAGE1_DIRECTORY / "risk_aware_core.py"
if not STAGE1_CORE.is_file():
    raise ImportError(f"Stage 1 core not found at {STAGE1_CORE}")
if str(STAGE1_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(STAGE1_DIRECTORY))

from risk_aware_core import (  # noqa: E402
    apply_availability_to_mri,
    broadcast_availability,
    build_eight_channel_input,
    validate_availability,
)

MODALITY_ORDER = ("T1n", "T1c", "T2w", "FLAIR")
A1_MODALITY_DROPOUT_PROBABILITY = 0.5

__all__ = [
    "MODALITY_ORDER",
    "A1_MODALITY_DROPOUT_PROBABILITY",
    "sample_modality_dropout_with_availability",
    "assert_availability_matches_mri",
    "build_a2_input",
    "build_full_validation_input",
]


def _validate_mri(data: Tensor) -> None:
    if not isinstance(data, Tensor):
        raise TypeError(f"data must be a torch.Tensor, got {type(data).__name__}")
    if data.ndim != 5:
        raise ValueError(
            f"data must be five-dimensional [B,4,D,H,W], got {tuple(data.shape)}"
        )
    if data.shape[1] != 4:
        raise ValueError(
            f"data must contain exactly four MRI modalities, got {data.shape[1]}"
        )
    if not data.is_floating_point():
        raise TypeError(f"data must have a floating dtype, got {data.dtype}")
    if not torch.isfinite(data).all().item():
        raise ValueError("data must contain only finite values")


def assert_availability_matches_mri(
    original_data: Tensor,
    masked_data: Tensor,
    availability: Tensor,
    *,
    require_full: bool = False,
) -> None:
    """Assert exact per-sample/per-modality zeroing with diagnostic indices."""

    _validate_mri(original_data)
    _validate_mri(masked_data)
    if original_data.shape != masked_data.shape:
        raise ValueError(
            f"original/masked shapes differ: {tuple(original_data.shape)} vs "
            f"{tuple(masked_data.shape)}"
        )
    if original_data.device != masked_data.device:
        raise ValueError(
            f"original/masked devices differ: {original_data.device} vs "
            f"{masked_data.device}"
        )
    available = validate_availability(
        availability,
        batch_size=original_data.shape[0],
        device=original_data.device,
    )
    if require_full and not torch.equal(available, torch.ones_like(available)):
        bad = torch.nonzero(available != 1, as_tuple=False)[0].tolist()
        raise AssertionError(
            "validation availability must be all ones; "
            f"batch index={bad[0]}, modality index={bad[1]}, expected=1, "
            f"actual={available[bad[0], bad[1]].item()}"
        )
    for batch_index in range(original_data.shape[0]):
        for modality_index in range(4):
            expected = int(available[batch_index, modality_index].item())
            actual_channel = masked_data[batch_index, modality_index]
            if expected == 0:
                nonzero = int(torch.count_nonzero(actual_channel).item())
                if nonzero != 0:
                    raise AssertionError(
                        "missing modality was not strictly zero; "
                        f"batch index={batch_index}, modality index={modality_index}, "
                        f"expected state=all-zero, actual nonzero voxels={nonzero}"
                    )
            elif not torch.equal(
                actual_channel, original_data[batch_index, modality_index]
            ):
                max_delta = (
                    actual_channel - original_data[batch_index, modality_index]
                ).abs().max().item()
                raise AssertionError(
                    "available modality was modified; "
                    f"batch index={batch_index}, modality index={modality_index}, "
                    f"expected state=unchanged, actual max_abs_delta={max_delta}"
                )


def sample_modality_dropout_with_availability(
    data: Tensor,
    probability: float = A1_MODALITY_DROPOUT_PROBABILITY,
) -> tuple[Tensor, Tensor]:
    """Mirror A1 ModDrop and return one shared zeroing/availability pattern.

    Each sample independently triggers with probability 0.5 by default.
    Triggered samples uniformly choose exactly one of four MRI modalities.
    Non-triggered samples remain full.  No availability is inferred from MRI
    voxel values.
    """

    _validate_mri(data)
    if not isinstance(probability, (int, float)):
        raise TypeError("probability must be numeric")
    probability = float(probability)
    if probability < 0 or probability > 1:
        raise ValueError(f"probability must lie in [0,1], got {probability}")

    batch_size = data.shape[0]
    availability = torch.ones(
        (batch_size, 4), dtype=torch.float32, device=data.device
    )
    if probability > 0:
        apply_mask = torch.rand(batch_size, device=data.device) < probability
        if torch.any(apply_mask):
            chosen_channels = torch.randint(
                low=0,
                high=4,
                size=(batch_size,),
                device=data.device,
            )
            selected_samples = torch.arange(
                batch_size, device=data.device
            )[apply_mask]
            selected_channels = chosen_channels[apply_mask]
            availability[selected_samples, selected_channels] = 0

    # Stage 1 is the sole implementation of deterministic zeroing.
    masked_data = apply_availability_to_mri(data, availability)
    assert_availability_matches_mri(data, masked_data, availability)
    return masked_data, availability


def build_a2_input(
    original_data: Tensor,
    masked_data: Tensor,
    availability: Tensor,
) -> Tensor:
    """Build the fixed-order A2 tensor from a previously sampled pattern."""

    assert_availability_matches_mri(original_data, masked_data, availability)
    # Stage 1 performs validation, deterministic zeroing, spatial broadcast,
    # and fixed [MRI4, availability4] concatenation.
    result = build_eight_channel_input(original_data, availability)
    if not torch.equal(result[:, :4], masked_data):
        raise AssertionError(
            "shared sampled pattern mismatch: Stage 1 zeroing differs from "
            "the sampled masked MRI"
        )
    masks = broadcast_availability(
        availability,
        spatial_shape=original_data.shape[2:],
        dtype=original_data.dtype,
        device=original_data.device,
    )
    if not torch.equal(result[:, 4:], masks):
        raise AssertionError("availability broadcast/channel-order mismatch")
    if result.shape[1] != 8:
        raise AssertionError(
            f"A2 network input must have 8 channels, got {result.shape[1]}"
        )
    return result


def build_full_validation_input(data: Tensor) -> tuple[Tensor, Tensor]:
    """Build validation input with explicit full ``[1,1,1,1]`` availability."""

    _validate_mri(data)
    availability = torch.ones((data.shape[0], 4), device=data.device)
    result = build_eight_channel_input(data, availability)
    assert_availability_matches_mri(
        data, result[:, :4], availability, require_full=True
    )
    if not torch.equal(result[:, 4:], torch.ones_like(result[:, 4:])):
        raise AssertionError("validation availability channels must all equal one")
    return result, availability
