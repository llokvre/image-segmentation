"""Synthetic CPU integration tests for A2 ModDrop + availability channels."""

from __future__ import annotations

import hashlib
import inspect
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
import torch.nn.functional as F

import availability_integration as integration
from nnUNetTrainerModDropAvailabilityMask import (
    nnUNetTrainerModDropAvailabilityMask,
)
from nnunetv2.training.loss.compound_losses import DC_and_CE_loss
from nnunetv2.training.loss.deep_supervision import DeepSupervisionWrapper
from nnunetv2.training.loss.dice import MemoryEfficientSoftDiceLoss
from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer
from nnunetv2.training.nnUNetTrainer.nnUNetTrainerModalityDropout import (
    nnUNetTrainerModalityDropout,
)
from nnunetv2.utilities.plans_handling.plans_handler import PlansManager


ROOT = Path("/root/autodl-tmp/nnunet_brats")
PLANS_PATH = ROOT / "nnUNet_preprocessed/Dataset501_BraTS2023/nnUNetPlans.json"
DATASET_JSON_PATH = ROOT / "nnUNet_preprocessed/Dataset501_BraTS2023/dataset.json"
BASELINE_PATH = Path(inspect.getsourcefile(nnUNetTrainerModalityDropout))
BASELINE_SHA256 = "e579f2d854db6b8819be1a99dde6a9855921163a358cd6c8b3f563f7c2647dde"
CHECKPOINT_PATH = ROOT / (
    "nnUNet_results/Dataset501_BraTS2023/"
    "nnUNetTrainerModalityDropout__nnUNetPlans__3d_fullres/fold_0/"
    "checkpoint_best.pth"
)


def build_real_networks() -> tuple[torch.nn.Module, torch.nn.Module, int]:
    plans = json.loads(PLANS_PATH.read_text(encoding="utf-8"))
    dataset_json = json.loads(DATASET_JSON_PATH.read_text(encoding="utf-8"))
    plans_manager = PlansManager(plans)
    configuration = plans_manager.get_configuration("3d_fullres")
    output_classes = plans_manager.get_label_manager(
        dataset_json
    ).num_segmentation_heads
    a1 = nnUNetTrainer.build_network_architecture(
        plans_manager, configuration, 4, output_classes, True
    )
    a2 = nnUNetTrainerModDropAvailabilityMask.build_network_architecture(
        plans_manager, configuration, 4, output_classes, True
    )
    return a1, a2, output_classes


def make_base_loss(num_scales: int) -> torch.nn.Module:
    leaf = DC_and_CE_loss(
        {
            "batch_dice": False,
            "smooth": 1e-5,
            "do_bg": False,
            "ddp": False,
        },
        {},
        weight_ce=1,
        weight_dice=1,
        ignore_label=None,
        dice_class=MemoryEfficientSoftDiceLoss,
    )
    weights = np.array([1 / (2**index) for index in range(num_scales)])
    weights[-1] = 0
    weights = weights / weights.sum()
    return DeepSupervisionWrapper(leaf, weights)


def targets_for_outputs(
    label: torch.Tensor, outputs: list[torch.Tensor]
) -> list[torch.Tensor]:
    targets = []
    for output in outputs:
        if label.shape[2:] == output.shape[2:]:
            targets.append(label)
        else:
            targets.append(
                F.interpolate(
                    label.float(), size=output.shape[2:], mode="nearest-exact"
                ).long()
            )
    return targets


class Stage2AIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        torch.set_num_threads(min(8, torch.get_num_threads()))
        cls.a1, cls.a2, cls.output_classes = build_real_networks()
        cls.a1_params = sum(parameter.numel() for parameter in cls.a1.parameters())
        cls.a2_params = sum(parameter.numel() for parameter in cls.a2.parameters())

    def setUp(self) -> None:
        self.data = torch.arange(
            3 * 4 * 4 * 4 * 4, dtype=torch.float32
        ).reshape(3, 4, 4, 4, 4) + 1

    def test_a2_trainer_class_imports(self) -> None:
        self.assertEqual(
            nnUNetTrainerModDropAvailabilityMask.__name__,
            "nnUNetTrainerModDropAvailabilityMask",
        )

    def test_a2_and_baseline_are_different_classes(self) -> None:
        self.assertIsNot(
            nnUNetTrainerModDropAvailabilityMask,
            nnUNetTrainerModalityDropout,
        )
        self.assertIs(
            nnUNetTrainerModDropAvailabilityMask.__base__, nnUNetTrainer
        )

    def test_baseline_trainer_source_unmodified(self) -> None:
        actual = hashlib.sha256(BASELINE_PATH.read_bytes()).hexdigest()
        self.assertEqual(actual, BASELINE_SHA256)

    def test_real_signatures_are_parent_compatible(self) -> None:
        self.assertEqual(
            inspect.signature(
                nnUNetTrainerModDropAvailabilityMask.build_network_architecture
            ),
            inspect.signature(nnUNetTrainer.build_network_architecture),
        )
        self.assertEqual(
            inspect.signature(nnUNetTrainerModDropAvailabilityMask.train_step),
            inspect.signature(nnUNetTrainer.train_step),
        )
        self.assertEqual(
            inspect.signature(nnUNetTrainerModDropAvailabilityMask.validation_step),
            inspect.signature(nnUNetTrainer.validation_step),
        )

    def test_moddrop_sampler_returns_availability(self) -> None:
        masked, availability = integration.sample_modality_dropout_with_availability(
            self.data, 0.5
        )
        self.assertEqual(masked.shape, self.data.shape)
        self.assertEqual(availability.shape, (3, 4))
        self.assertTrue(torch.all((availability == 0) | (availability == 1)).item())

    def test_same_pattern_drives_zeroing_and_availability(self) -> None:
        with patch("torch.rand", return_value=torch.tensor([0.1, 0.9, 0.2])), patch(
            "torch.randint", return_value=torch.tensor([0, 1, 3])
        ):
            masked, availability = integration.sample_modality_dropout_with_availability(
                self.data, 0.5
            )
        expected = torch.tensor([[0, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 0]])
        self.assertTrue(torch.equal(availability, expected.float()))
        integration.assert_availability_matches_mri(
            self.data, masked, availability
        )

    def test_full_sample_generates_all_ones(self) -> None:
        masked, availability = integration.sample_modality_dropout_with_availability(
            self.data, 0
        )
        self.assertTrue(torch.equal(availability, torch.ones_like(availability)))
        self.assertTrue(torch.equal(masked, self.data))

    def test_missing_t1c_generates_expected_vector(self) -> None:
        with patch("torch.rand", return_value=torch.zeros(3)), patch(
            "torch.randint", return_value=torch.ones(3, dtype=torch.int64)
        ):
            masked, availability = integration.sample_modality_dropout_with_availability(
                self.data, 0.5
            )
        self.assertTrue(
            torch.equal(
                availability,
                torch.tensor([[1, 0, 1, 1]] * 3, dtype=torch.float32),
            )
        )
        self.assertEqual(torch.count_nonzero(masked[:, 1]).item(), 0)

    def test_batch_sampling_matches_a1_protocol(self) -> None:
        for seed in (0, 7, 1234):
            torch.manual_seed(seed)
            expected = nnUNetTrainerModalityDropout.apply_modality_dropout(
                self.data, 0.5
            )
            torch.manual_seed(seed)
            actual, availability = (
                integration.sample_modality_dropout_with_availability(
                    self.data, 0.5
                )
            )
            self.assertTrue(torch.equal(actual, expected))
            integration.assert_availability_matches_mri(
                self.data, actual, availability
            )

    def test_input_changes_from_four_to_eight_channels(self) -> None:
        masked, availability = integration.sample_modality_dropout_with_availability(
            self.data, 0
        )
        result = integration.build_a2_input(self.data, masked, availability)
        self.assertEqual(result.shape, (3, 8, 4, 4, 4))

    def test_availability_channels_are_spatial_constants(self) -> None:
        availability = torch.tensor(
            [[1, 0, 1, 1], [0, 1, 1, 1], [1, 1, 1, 0]]
        )
        masked = integration.apply_availability_to_mri(self.data, availability)
        result = integration.build_a2_input(self.data, masked, availability)
        for batch in range(3):
            for modality in range(4):
                self.assertTrue(
                    torch.all(
                        result[batch, modality + 4]
                        == availability[batch, modality]
                    ).item()
                )

    def test_validation_input_uses_full_availability(self) -> None:
        result, availability = integration.build_full_validation_input(self.data)
        self.assertTrue(torch.equal(availability, torch.ones_like(availability)))
        self.assertTrue(torch.equal(result[:, :4], self.data))
        self.assertTrue(torch.equal(result[:, 4:], torch.ones_like(result[:, 4:])))

    def test_validation_does_not_call_random_sampler(self) -> None:
        trainer = object.__new__(nnUNetTrainerModDropAvailabilityMask)
        with patch(
            "nnUNetTrainerModDropAvailabilityMask."
            "sample_modality_dropout_with_availability"
        ) as sampler:
            result, availability = trainer._prepare_a2_validation_input(self.data)
        sampler.assert_not_called()
        self.assertEqual(result.shape[1], 8)
        self.assertTrue(torch.equal(availability, torch.ones_like(availability)))

    def test_real_network_input_channels_are_eight(self) -> None:
        first = next(
            module for module in self.a2.modules() if isinstance(module, torch.nn.Conv3d)
        )
        self.assertEqual(first.in_channels, 8)

    def test_real_network_output_classes_are_four(self) -> None:
        self.assertEqual(self.output_classes, 4)
        final_convs = [
            module
            for module in self.a2.modules()
            if isinstance(module, torch.nn.Conv3d) and module.out_channels == 4
        ]
        self.assertGreaterEqual(len(final_convs), 1)

    def test_deep_supervision_configuration_is_unchanged(self) -> None:
        a1_heads = [
            module.out_channels
            for module in self.a1.modules()
            if isinstance(module, torch.nn.Conv3d) and module.out_channels == 4
        ]
        a2_heads = [
            module.out_channels
            for module in self.a2.modules()
            if isinstance(module, torch.nn.Conv3d) and module.out_channels == 4
        ]
        self.assertEqual(a2_heads, a1_heads)
        self.assertEqual(len(a2_heads), 5)

    def test_parameter_increase_only_first_convolution(self) -> None:
        a1_shapes = dict(self.a1.named_parameters())
        a2_shapes = dict(self.a2.named_parameters())
        self.assertEqual(set(a1_shapes), set(a2_shapes))
        differences = [
            name
            for name in a1_shapes
            if a1_shapes[name].shape != a2_shapes[name].shape
        ]
        self.assertEqual(differences, ["encoder.stages.0.0.convs.0.conv.weight"])
        self.assertEqual(self.a2_params - self.a1_params, 3456)

    def test_original_base_loss_accepts_a2_outputs(self) -> None:
        self.a2.train()
        data = torch.randn(1, 4, 64, 64, 64)
        availability = torch.ones(1, 4)
        masked = integration.apply_availability_to_mri(data, availability)
        network_input = integration.build_a2_input(data, masked, availability)
        outputs = self.a2(network_input)
        self.assertIsInstance(outputs, list)
        target = torch.randint(0, 4, (1, 1, 64, 64, 64))
        loss = make_base_loss(len(outputs))(outputs, targets_for_outputs(target, outputs))
        self.assertTrue(torch.isfinite(loss).item())

    def test_synthetic_cpu_full_and_missing_forward_backward(self) -> None:
        self.a2.train()
        for availability in (
            torch.ones(1, 4),
            torch.tensor([[1, 0, 1, 1]], dtype=torch.float32),
        ):
            self.a2.zero_grad(set_to_none=True)
            data = torch.randn(1, 4, 64, 64, 64)
            original = data.clone()
            masked = integration.apply_availability_to_mri(data, availability)
            network_input = integration.build_a2_input(
                data, masked, availability
            )
            self.assertTrue(torch.equal(data, original))
            outputs = self.a2(network_input)
            self.assertEqual(len(outputs), 5)
            self.assertTrue(all(output.shape[1] == 4 for output in outputs))
            target = torch.randint(0, 4, (1, 1, 64, 64, 64))
            loss = make_base_loss(len(outputs))(
                outputs, targets_for_outputs(target, outputs)
            )
            self.assertTrue(torch.isfinite(loss).item())
            loss.backward()
            gradients = [
                parameter.grad
                for parameter in self.a2.parameters()
                if parameter.grad is not None
            ]
            self.assertTrue(gradients)
            self.assertTrue(all(torch.isfinite(gradient).all().item() for gradient in gradients))

    def test_training_preparation_samples_exactly_once(self) -> None:
        trainer = object.__new__(nnUNetTrainerModDropAvailabilityMask)
        trainer.modality_dropout_probability = 0.5
        fake_availability = torch.ones(3, 4)
        with patch.object(
            nnUNetTrainerModDropAvailabilityMask,
            "apply_modality_dropout_with_availability",
            return_value=(self.data.clone(), fake_availability),
        ) as sampler:
            result, availability = trainer._prepare_a2_training_input(self.data)
        sampler.assert_called_once()
        self.assertEqual(result.shape[1], 8)
        self.assertTrue(torch.equal(availability, fake_availability))

    def test_old_checkpoint_is_explicitly_incompatible(self) -> None:
        checkpoint = torch.load(
            CHECKPOINT_PATH, map_location="cpu", weights_only=False
        )
        state = checkpoint["network_weights"]
        first_name = next(name for name, value in state.items() if value.ndim == 5)
        old_shape = tuple(state[first_name].shape)
        a2_shape = tuple(dict(self.a2.state_dict())[first_name].shape)
        self.assertEqual(old_shape[1], 4)
        self.assertEqual(a2_shape[1], 8)
        self.assertNotEqual(old_shape, a2_shape)
        del checkpoint

    def test_input_tensor_is_not_modified(self) -> None:
        original = self.data.clone()
        masked, availability = integration.sample_modality_dropout_with_availability(
            self.data, 1
        )
        _ = integration.build_a2_input(self.data, masked, availability)
        self.assertTrue(torch.equal(self.data, original))

    def test_fixed_input_is_deterministic(self) -> None:
        availability = torch.tensor(
            [[1, 0, 1, 1], [1, 1, 1, 1], [0, 1, 1, 1]]
        )
        masked = integration.apply_availability_to_mri(self.data, availability)
        first = integration.build_a2_input(self.data, masked, availability)
        second = integration.build_a2_input(self.data, masked, availability)
        self.assertTrue(torch.equal(first, second))

    def test_diagnostic_assertion_reports_indices(self) -> None:
        availability = torch.tensor([[1, 0, 1, 1]] * 3)
        masked = self.data.clone()
        with self.assertRaisesRegex(
            AssertionError, r"batch index=0, modality index=1"
        ):
            integration.assert_availability_matches_mri(
                self.data, masked, availability
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
