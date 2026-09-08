"""Shared deterministic mathematics for Risk-aware V1 stage 1.

This module is intentionally independent of nnU-Net, NIfTI, checkpoints, data
loaders, and network code.  Public APIs operate only on explicit PyTorch
tensors.  Modality order is ``[T1n, T1c, T2w, FLAIR]`` and region order is
``[WT, TC, ET]``.
"""

from __future__ import annotations

import math
from typing import Sequence

import torch
from torch import Tensor

MODALITY_ORDER = ("T1n", "T1c", "T2w", "FLAIR")
REGION_ORDER = ("WT", "TC", "ET")
DEFAULT_ALPHA = 1.0
DEFAULT_LAMBDA_REGION = 0.2
DEFAULT_WEIGHT_CLAMP = (0.5, 1.5)
DEFAULT_SMOOTH = 1e-5

__all__ = [
    "MODALITY_ORDER",
    "REGION_ORDER",
    "DEFAULT_ALPHA",
    "DEFAULT_LAMBDA_REGION",
    "DEFAULT_WEIGHT_CLAMP",
    "DEFAULT_SMOOTH",
    "validate_availability",
    "apply_availability_to_mri",
    "broadcast_availability",
    "build_eight_channel_input",
    "build_region_targets",
    "logits_to_region_probabilities",
    "per_sample_region_soft_dice_loss",
    "compute_risk_weights",
    "weighted_region_loss",
    "combine_total_loss",
    "deep_supervision_region_loss",
]


def _require_tensor(value: object, name: str) -> Tensor:
    if not isinstance(value, Tensor):
        raise TypeError(f"{name} must be a torch.Tensor, got {type(value).__name__}")
    return value


def _require_floating(value: Tensor, name: str) -> None:
    if not value.is_floating_point():
        raise TypeError(f"{name} must have a floating dtype, got {value.dtype}")


def _require_finite(value: Tensor, name: str) -> None:
    if not torch.isfinite(value).all().item():
        raise ValueError(f"{name} must contain only finite values")


def validate_availability(
    availability: Tensor,
    *,
    batch_size: int | None = None,
    device: torch.device | None = None,
) -> Tensor:
    """Validate ``[B,4]`` availability and return detached float32 values.

    Bool, integer, and floating binary tensors are accepted.  Values must be
    exactly zero or one.  The returned tensor is detached, resides on the same
    device, and has dtype ``torch.float32``.
    """

    availability = _require_tensor(availability, "availability")
    if availability.ndim != 2 or availability.shape[1] != 4:
        raise ValueError(
            f"availability must have shape [B,4], got {tuple(availability.shape)}"
        )
    if availability.shape[0] < 1:
        raise ValueError("availability batch dimension must be positive")
    if batch_size is not None and availability.shape[0] != batch_size:
        raise ValueError(
            "availability batch size does not match MRI batch size: "
            f"{availability.shape[0]} != {batch_size}"
        )
    if device is not None and availability.device != torch.device(device):
        raise ValueError(
            "availability and MRI must be on the same device: "
            f"{availability.device} != {torch.device(device)}"
        )
    if availability.is_complex():
        raise TypeError("availability must not have a complex dtype")
    if availability.is_floating_point():
        _require_finite(availability, "availability")
    valid = torch.logical_or(availability == 0, availability == 1)
    if not valid.all().item():
        raise ValueError("availability values must be binary (exactly 0 or 1)")
    return availability.detach().to(dtype=torch.float32)


def _validate_mri(data: Tensor) -> None:
    data = _require_tensor(data, "data")
    if data.ndim != 5 or data.shape[1] != 4:
        raise ValueError(f"data must have shape [B,4,D,H,W], got {tuple(data.shape)}")
    if data.shape[0] < 1 or any(size < 1 for size in data.shape[2:]):
        raise ValueError("data batch and spatial dimensions must be positive")
    _require_floating(data, "data")
    _require_finite(data, "data")


def apply_availability_to_mri(data: Tensor, availability: Tensor) -> Tensor:
    """Return a non-inplace, deterministically zero-filled MRI tensor."""

    _validate_mri(data)
    available = validate_availability(
        availability, batch_size=data.shape[0], device=data.device
    ).to(dtype=data.dtype)
    return data * available.view(data.shape[0], 4, 1, 1, 1)


def broadcast_availability(
    availability: Tensor,
    spatial_shape: Sequence[int],
    dtype: torch.dtype,
    device: torch.device,
) -> Tensor:
    """Broadcast ``[B,4]`` availability to constant ``[B,4,D,H,W]`` channels."""

    if len(tuple(spatial_shape)) != 3:
        raise ValueError(f"spatial_shape must contain D,H,W, got {spatial_shape}")
    shape = tuple(int(size) for size in spatial_shape)
    if any(size < 1 for size in shape):
        raise ValueError(f"spatial_shape entries must be positive, got {shape}")
    if not torch.empty((), dtype=dtype).is_floating_point():
        raise TypeError(f"dtype must be a floating MRI dtype, got {dtype}")
    available = validate_availability(availability, device=torch.device(device))
    return (
        available.to(dtype=dtype)
        .view(available.shape[0], 4, 1, 1, 1)
        .expand(available.shape[0], 4, *shape)
    )


def build_eight_channel_input(data: Tensor, availability: Tensor) -> Tensor:
    """Build MRI+availability input with fixed channel order ``[MRI4, mask4]``."""

    _validate_mri(data)
    available = validate_availability(
        availability, batch_size=data.shape[0], device=data.device
    )
    masked = apply_availability_to_mri(data, available)
    masks = broadcast_availability(
        available, data.shape[2:], dtype=data.dtype, device=data.device
    )
    zero_selector = available.to(dtype=torch.bool).logical_not()
    if zero_selector.any().item():
        selected = masked[zero_selector]
        if not torch.equal(selected, torch.zeros_like(selected)):
            raise RuntimeError("availability/MRI consistency assertion failed")
    result = torch.cat((masked, masks), dim=1)
    if result.shape != (data.shape[0], 8, *data.shape[2:]):
        raise RuntimeError(f"unexpected eight-channel shape: {tuple(result.shape)}")
    return result


def build_region_targets(target: Tensor) -> Tensor:
    """Convert BraTS labels to binary ``[B,3,D,H,W]`` WT/TC/ET targets."""

    target = _require_tensor(target, "target")
    if target.ndim == 5:
        if target.shape[1] != 1:
            raise ValueError(
                f"5D target must have one label channel, got {tuple(target.shape)}"
            )
        labels = target[:, 0]
    elif target.ndim == 4:
        labels = target
    else:
        raise ValueError(
            f"target must have shape [B,1,D,H,W] or [B,D,H,W], got {tuple(target.shape)}"
        )
    if labels.shape[0] < 1 or any(size < 1 for size in labels.shape[1:]):
        raise ValueError("target batch and spatial dimensions must be positive")
    if labels.is_complex() or labels.dtype == torch.bool:
        raise TypeError(f"target must use numeric class labels, got {labels.dtype}")
    if labels.is_floating_point():
        _require_finite(labels, "target")
    valid = (labels == 0) | (labels == 1) | (labels == 2) | (labels == 3)
    if not valid.all().item():
        raise ValueError("target labels must be drawn only from {0,1,2,3}")
    wt = (labels == 1) | (labels == 2) | (labels == 3)
    tc = (labels == 1) | (labels == 3)
    et = labels == 3
    return torch.stack((wt, tc, et), dim=1).to(dtype=torch.float32)


def logits_to_region_probabilities(logits: Tensor) -> Tensor:
    """Convert four-class logits to WT/TC/ET probabilities."""

    logits = _require_tensor(logits, "logits")
    if logits.ndim != 5 or logits.shape[1] != 4:
        raise ValueError(
            f"logits must have shape [B,4,D,H,W], got {tuple(logits.shape)}"
        )
    _require_floating(logits, "logits")
    _require_finite(logits, "logits")
    probabilities = torch.softmax(logits, dim=1)
    return torch.stack(
        (
            probabilities[:, 1] + probabilities[:, 2] + probabilities[:, 3],
            probabilities[:, 1] + probabilities[:, 3],
            probabilities[:, 3],
        ),
        dim=1,
    )


def per_sample_region_soft_dice_loss(
    region_probabilities: Tensor,
    region_targets: Tensor,
    *,
    smooth: float = DEFAULT_SMOOTH,
) -> Tensor:
    """Return non-squared soft Dice losses with shape ``[B,3]``.

    Formula: ``1 - (2*sum(P*Y)+smooth)/(sum(P)+sum(Y)+smooth)``.
    Empty ground-truth regions are not skipped.
    """

    probabilities = _require_tensor(region_probabilities, "region_probabilities")
    targets = _require_tensor(region_targets, "region_targets")
    if probabilities.ndim != 5 or probabilities.shape[1] != 3:
        raise ValueError(
            "region_probabilities must have shape [B,3,D,H,W], got "
            f"{tuple(probabilities.shape)}"
        )
    if targets.shape != probabilities.shape:
        raise ValueError(
            "region_targets shape must match region_probabilities: "
            f"{tuple(targets.shape)} != {tuple(probabilities.shape)}"
        )
    if targets.device != probabilities.device:
        raise ValueError("region probabilities and targets must share a device")
    _require_floating(probabilities, "region_probabilities")
    _require_floating(targets, "region_targets")
    _require_finite(probabilities, "region_probabilities")
    _require_finite(targets, "region_targets")
    if (probabilities < 0).any().item() or (probabilities > 1).any().item():
        raise ValueError("region_probabilities must lie in [0,1]")
    if not ((targets == 0) | (targets == 1)).all().item():
        raise ValueError("region_targets must be binary")
    if not math.isfinite(smooth) or smooth <= 0:
        raise ValueError("smooth must be a positive finite number")
    dims = tuple(range(2, probabilities.ndim))
    intersection = (probabilities * targets).sum(dim=dims)
    denominator = (probabilities.sum(dim=dims) + targets.sum(dim=dims) + smooth)
    denominator = denominator.clamp_min(1e-8)
    dice = (2.0 * intersection + smooth) / denominator
    loss = 1.0 - dice
    _require_finite(loss, "per-sample region Dice loss")
    return loss


def compute_risk_weights(
    availability: Tensor,
    risk_matrix: Tensor,
    *,
    alpha: float = DEFAULT_ALPHA,
    weight_clamp: tuple[float, float] = DEFAULT_WEIGHT_CLAMP,
) -> Tensor:
    """Compute detached sample-specific WT/TC/ET risk weights ``[B,3]``."""

    available = validate_availability(availability)
    risk = _require_tensor(risk_matrix, "risk_matrix")
    if risk.shape != (4, 3):
        raise ValueError(f"risk_matrix must have shape [4,3], got {tuple(risk.shape)}")
    _require_floating(risk, "risk_matrix")
    _require_finite(risk, "risk_matrix")
    if risk.device != available.device:
        raise ValueError("risk_matrix and availability must share a device")
    if risk.requires_grad:
        raise ValueError("risk_matrix must be frozen with requires_grad=False")
    if (risk < 0).any().item():
        raise ValueError("risk_matrix must be non-negative")
    if not math.isfinite(alpha) or alpha < 0:
        raise ValueError("alpha must be a non-negative finite number")
    if len(weight_clamp) != 2:
        raise ValueError("weight_clamp must contain (minimum, maximum)")
    lower, upper = float(weight_clamp[0]), float(weight_clamp[1])
    if not (math.isfinite(lower) and math.isfinite(upper) and 0 < lower <= upper):
        raise ValueError("weight_clamp must satisfy 0 < minimum <= maximum")
    missing = 1.0 - available
    scores = missing @ risk.detach().to(dtype=available.dtype)
    raw = 1.0 + float(alpha) * scores
    normalized = 3.0 * raw / raw.sum(dim=1, keepdim=True).clamp_min(1e-8)
    clipped = normalized.clamp(min=lower, max=upper)
    final = 3.0 * clipped / clipped.sum(dim=1, keepdim=True).clamp_min(1e-8)
    final = final.detach()
    _require_finite(final, "risk weights")
    if not torch.allclose(
        final.mean(dim=1),
        torch.ones(final.shape[0], device=final.device, dtype=final.dtype),
        atol=1e-6,
        rtol=1e-6,
    ):
        raise RuntimeError("risk weights failed per-sample mean-one assertion")
    return final


def weighted_region_loss(
    per_sample_region_loss: Tensor, region_weights: Tensor
) -> Tensor:
    """Return ``mean_b(sum_r(weight[b,r]*loss[b,r])/3)``."""

    losses = _require_tensor(per_sample_region_loss, "per_sample_region_loss")
    weights = _require_tensor(region_weights, "region_weights")
    if losses.ndim != 2 or losses.shape[1] != 3:
        raise ValueError(
            f"per_sample_region_loss must have shape [B,3], got {tuple(losses.shape)}"
        )
    if weights.shape != losses.shape:
        raise ValueError(
            f"region_weights must match loss shape: {tuple(weights.shape)}"
        )
    if weights.device != losses.device:
        raise ValueError("region losses and weights must share a device")
    _require_floating(losses, "per_sample_region_loss")
    _require_floating(weights, "region_weights")
    _require_finite(losses, "per_sample_region_loss")
    _require_finite(weights, "region_weights")
    result = (losses * weights.detach().to(dtype=losses.dtype)).sum(dim=1).div(3).mean()
    _require_finite(result, "weighted region loss")
    return result


def combine_total_loss(
    base_loss: Tensor,
    region_loss: Tensor,
    *,
    lambda_region: float = DEFAULT_LAMBDA_REGION,
) -> Tensor:
    """Return ``base_loss + lambda_region * region_loss`` without recomputation."""

    base = _require_tensor(base_loss, "base_loss")
    region = _require_tensor(region_loss, "region_loss")
    if base.ndim != 0 or region.ndim != 0:
        raise ValueError("base_loss and region_loss must both be scalar tensors")
    if base.device != region.device:
        raise ValueError("base_loss and region_loss must share a device")
    _require_floating(base, "base_loss")
    _require_floating(region, "region_loss")
    _require_finite(base, "base_loss")
    _require_finite(region, "region_loss")
    if not math.isfinite(lambda_region) or lambda_region < 0:
        raise ValueError("lambda_region must be a non-negative finite number")
    total = base + float(lambda_region) * region
    _require_finite(total, "total loss")
    return total


def deep_supervision_region_loss(
    outputs: Sequence[Tensor],
    targets: Sequence[Tensor],
    deep_supervision_weights: Sequence[float],
    availability: Tensor,
    risk_matrix: Tensor,
    *,
    alpha: float = DEFAULT_ALPHA,
    weight_clamp: tuple[float, float] = DEFAULT_WEIGHT_CLAMP,
    smooth: float = DEFAULT_SMOOTH,
) -> Tensor:
    """Compute the weighted sum of per-scale region losses.

    Targets must already correspond one-to-one with outputs.  No target is
    downsampled here.  Scales with zero weight are ignored.
    """

    if not isinstance(outputs, (list, tuple)) or not isinstance(targets, (list, tuple)):
        raise TypeError("outputs and targets must be list/tuple deep-supervision scales")
    if len(outputs) != len(targets) or len(outputs) != len(deep_supervision_weights):
        raise ValueError(
            "outputs, targets, and deep_supervision_weights must have equal lengths"
        )
    if len(outputs) < 1:
        raise ValueError("at least one deep-supervision scale is required")
    scale_weights = [float(weight) for weight in deep_supervision_weights]
    if any(not math.isfinite(weight) or weight < 0 for weight in scale_weights):
        raise ValueError("deep-supervision weights must be finite and non-negative")
    if not any(weight > 0 for weight in scale_weights):
        raise ValueError("at least one deep-supervision weight must be positive")
    sample_weights = compute_risk_weights(
        availability, risk_matrix, alpha=alpha, weight_clamp=weight_clamp
    )
    result: Tensor | None = None
    for index, (output, target, scale_weight) in enumerate(
        zip(outputs, targets, scale_weights)
    ):
        if scale_weight == 0:
            continue
        output = _require_tensor(output, f"outputs[{index}]")
        target = _require_tensor(target, f"targets[{index}]")
        region_targets = build_region_targets(target).to(
            device=output.device, dtype=output.dtype
        )
        if output.shape[0] != sample_weights.shape[0]:
            raise ValueError(f"outputs[{index}] batch size does not match availability")
        if output.shape[2:] != region_targets.shape[2:]:
            raise ValueError(
                f"outputs[{index}] and targets[{index}] spatial shapes differ"
            )
        probabilities = logits_to_region_probabilities(output)
        per_sample = per_sample_region_soft_dice_loss(
            probabilities, region_targets, smooth=smooth
        )
        scale_loss = weighted_region_loss(
            per_sample, sample_weights.to(device=output.device)
        )
        contribution = scale_weight * scale_loss
        result = contribution if result is None else result + contribution
    if result is None:
        raise RuntimeError("no positive-weight deep-supervision scale was evaluated")
    _require_finite(result, "deep-supervision region loss")
    return result
