"""A2 inference adapter with an explicit missing-modality pattern.

The four MRI channels are transformed by the frozen, tested A2 primitives.
Availability is never inferred from voxel values.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Final

import torch
from batchgenerators.utilities.file_and_folder_operations import load_json
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
from nnunetv2.utilities.plans_handling.plans_handler import PlansManager

ROOT: Final = Path("/root/autodl-tmp/nnunet_brats")
TRAINING_DIR: Final = ROOT / "risk_aware_v1_a2_training"
TRAINER_PACKAGE: Final = TRAINING_DIR / "trainer_package"
RESULTS_DIR: Final = ROOT / (
    "nnUNet_results/Dataset501_BraTS2023/"
    "nnUNetTrainerModDropAvailabilityMask__nnUNetPlans__3d_fullres"
)
BEST_CHECKPOINT: Final = RESULTS_DIR / "fold_0/checkpoint_best.pth"
A1_CHECKPOINT: Final = ROOT / (
    "nnUNet_results/Dataset501_BraTS2023/"
    "nnUNetTrainerModalityDropout__nnUNetPlans__3d_fullres/"
    "fold_0/checkpoint_best.pth"
)

if str(TRAINING_DIR) not in sys.path:
    sys.path.insert(0, str(TRAINING_DIR))

from trainer_package.availability_integration import (  # noqa: E402
    assert_availability_matches_mri,
)
from trainer_package.risk_aware_core import (  # noqa: E402
    build_eight_channel_input,
)
from trainer_package.nnUNetTrainerModDropAvailabilityMask import (  # noqa: E402
    nnUNetTrainerModDropAvailabilityMask,
)


MISSING_PATTERNS: Final[dict[str, tuple[int, int, int, int]]] = {
    "full": (1, 1, 1, 1),
    "t1n": (0, 1, 1, 1),
    "t1c": (1, 0, 1, 1),
    "t2w": (1, 1, 0, 1),
    "flair": (1, 1, 1, 0),
}


def availability_for_pattern(missing_pattern: str) -> tuple[int, int, int, int]:
    """Return the deterministic availability vector for an explicit pattern."""

    if not isinstance(missing_pattern, str):
        raise TypeError("missing_pattern must be a string")
    key = missing_pattern.strip().lower()
    if key not in MISSING_PATTERNS:
        raise ValueError(
            f"unsupported missing_pattern {missing_pattern!r}; "
            f"expected one of {tuple(MISSING_PATTERNS)}"
        )
    return MISSING_PATTERNS[key]


def build_a2_inference_input(
    mri: torch.Tensor, *, missing_pattern: str
) -> tuple[torch.Tensor, dict]:
    """Convert preprocessed ``[4,D,H,W]`` MRI into explicit ``[8,D,H,W]``."""

    if not isinstance(mri, torch.Tensor):
        raise TypeError("mri must be a torch.Tensor")
    if mri.ndim != 4 or mri.shape[0] != 4:
        raise ValueError(f"mri must have shape [4,D,H,W], got {tuple(mri.shape)}")
    if not mri.is_floating_point() or not torch.isfinite(mri).all().item():
        raise ValueError("mri must be a finite floating tensor")

    pattern = missing_pattern.strip().lower()
    vector = availability_for_pattern(pattern)
    availability = torch.tensor(
        [vector], dtype=torch.float32, device=mri.device
    )
    original = mri.unsqueeze(0)
    network_input = build_eight_channel_input(original, availability)
    assert_availability_matches_mri(
        original, network_input[:, :4], availability, require_full=(pattern == "full")
    )

    masks = network_input[:, 4:]
    for channel, expected in enumerate(vector):
        if not torch.all(masks[:, channel] == expected).item():
            raise AssertionError("availability channel is not spatially constant")

    if pattern == "full" and not torch.equal(network_input[:, :4], original):
        raise AssertionError("Full inference modified MRI channels")

    zeroed = [index for index, available in enumerate(vector) if available == 0]
    audit = {
        "missing_pattern": pattern,
        "mri_zeroed_channels": zeroed,
        "availability": list(vector),
        "network_channels": int(network_input.shape[1]),
        "availability_constant": True,
        "availability_zeroing_consistency": "PASS",
        "availability_inferred_from_zero_mri": False,
    }
    return network_input[0], audit


def checkpoint_input_channels(checkpoint_path: Path) -> int:
    """Read first convolution input width; reject ambiguous checkpoints."""

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    state = checkpoint.get("network_weights")
    if not isinstance(state, dict):
        raise ValueError("checkpoint has no network_weights state dict")
    candidates = [
        (name, tensor)
        for name, tensor in state.items()
        if isinstance(tensor, torch.Tensor) and tensor.ndim == 5
    ]
    if not candidates:
        raise ValueError("checkpoint has no 3D convolution weights")
    channels = int(candidates[0][1].shape[1])
    del checkpoint
    return channels


def require_a2_checkpoint(checkpoint_path: Path) -> int:
    channels = checkpoint_input_channels(checkpoint_path)
    if channels != 8:
        raise ValueError(
            f"A2 inference requires an 8-channel checkpoint, got {channels} channels"
        )
    return channels


class A2MissingModalityPredictor(nnUNetPredictor):
    """nnU-Net predictor that requires a missing pattern on every prediction."""

    last_input_audit: dict | None = None
    last_sliding_window_patch_count: int = 0
    checkpoint_report: dict | None = None
    _active_missing_pattern: str | None = None

    @torch.inference_mode()
    def predict_logits_from_preprocessed_data(
        self, data: torch.Tensor, *, missing_pattern: str
    ) -> torch.Tensor:
        prepared, audit = build_a2_inference_input(
            data, missing_pattern=missing_pattern
        )
        self.last_input_audit = audit
        self.last_sliding_window_patch_count = 0
        self._active_missing_pattern = audit["missing_pattern"]
        try:
            result = nnUNetPredictor.predict_logits_from_preprocessed_data(
                self, prepared
            )
        finally:
            self._active_missing_pattern = None
        if self.last_sliding_window_patch_count < 1:
            raise AssertionError("sliding-window inference did not reach network input")
        return result

    @torch.inference_mode()
    def _internal_maybe_mirror_and_predict(self, x: torch.Tensor) -> torch.Tensor:
        if self._active_missing_pattern is None:
            raise AssertionError("missing_pattern was not explicitly supplied")
        if x.ndim != 5 or x.shape[1] != 8:
            raise AssertionError(
                f"sliding-window network input must be [B,8,D,H,W], got {tuple(x.shape)}"
            )
        vector = availability_for_pattern(self._active_missing_pattern)
        for channel, expected in enumerate(vector):
            if not torch.all(x[:, channel + 4] == expected).item():
                raise AssertionError(
                    "sliding-window crop changed an availability channel"
                )
            if expected == 0 and torch.count_nonzero(x[:, channel]).item() != 0:
                raise AssertionError("missing MRI channel is nonzero in sliding-window crop")

        # The installed nnU-Net maps allowed axes to x dimensions 2+, so TTA is spatial only.
        if self.use_mirroring and self.allowed_mirroring_axes is not None:
            if any(axis not in (0, 1, 2) for axis in self.allowed_mirroring_axes):
                raise AssertionError("mirroring axis is not spatial")
        self.last_sliding_window_patch_count += 1
        return super()._internal_maybe_mirror_and_predict(x)


def load_a2_predictor(
    checkpoint_path: Path = BEST_CHECKPOINT,
    *,
    device: torch.device | None = None,
    use_mirroring: bool = True,
) -> A2MissingModalityPredictor:
    """Strictly load the frozen A2 trainer architecture and best checkpoint."""

    checkpoint_path = Path(checkpoint_path).resolve()
    if checkpoint_path != BEST_CHECKPOINT.resolve():
        raise ValueError(f"only checkpoint_best.pth is allowed: {checkpoint_path}")
    require_a2_checkpoint(checkpoint_path)

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if checkpoint.get("trainer_name") != "nnUNetTrainerModDropAvailabilityMask":
        raise ValueError(f"unexpected trainer: {checkpoint.get('trainer_name')}")
    if Path(inspect.getsourcefile(nnUNetTrainerModDropAvailabilityMask)).resolve().parent != TRAINER_PACKAGE.resolve():
        raise RuntimeError("A2 trainer did not come from the frozen trainer package")

    plans = load_json(str(RESULTS_DIR / "plans.json"))
    dataset_json = load_json(str(RESULTS_DIR / "dataset.json"))
    plans_manager = PlansManager(plans)
    configuration_name = checkpoint["init_args"]["configuration"]
    configuration_manager = plans_manager.get_configuration(configuration_name)
    output_classes = plans_manager.get_label_manager(dataset_json).num_segmentation_heads
    network = nnUNetTrainerModDropAvailabilityMask.build_network_architecture(
        plans_manager,
        configuration_manager,
        4,
        output_classes,
        enable_deep_supervision=False,
    )
    incompatible = network.load_state_dict(checkpoint["network_weights"], strict=True)
    missing_keys = list(incompatible.missing_keys)
    unexpected_keys = list(incompatible.unexpected_keys)
    if missing_keys or unexpected_keys:
        raise RuntimeError(
            f"checkpoint mismatch: missing={missing_keys}, unexpected={unexpected_keys}"
        )
    first_conv = next(m for m in network.modules() if isinstance(m, torch.nn.Conv3d))
    if first_conv.in_channels != 8 or output_classes != 4:
        raise RuntimeError("A2 checkpoint architecture validation failed")

    selected_device = device or torch.device("cuda")
    predictor = A2MissingModalityPredictor(
        tile_step_size=0.5,
        use_gaussian=True,
        use_mirroring=use_mirroring,
        perform_everything_on_device=True,
        device=selected_device,
        verbose=True,
        verbose_preprocessing=False,
        allow_tqdm=False,
    )
    predictor.manual_initialization(
        network,
        plans_manager,
        configuration_manager,
        [checkpoint["network_weights"]],
        dataset_json,
        checkpoint["trainer_name"],
        checkpoint.get("inference_allowed_mirroring_axes"),
    )
    predictor.checkpoint_report = {
        "checkpoint_path": str(checkpoint_path),
        "trainer_name": checkpoint["trainer_name"],
        "input_channels": int(first_conv.in_channels),
        "output_classes": int(output_classes),
        "missing_keys": missing_keys,
        "unexpected_keys": unexpected_keys,
    }
    del checkpoint
    return predictor
