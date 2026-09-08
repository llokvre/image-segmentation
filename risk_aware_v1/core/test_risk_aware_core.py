"""CPU-only unittest coverage for the Risk-aware V1 shared mathematical core."""

from __future__ import annotations

import importlib
import unittest

import torch

import risk_aware_core as core


class RiskAwareCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = torch.arange(2 * 4 * 2 * 3 * 4, dtype=torch.float32).reshape(
            2, 4, 2, 3, 4
        )
        self.full = torch.ones((2, 4), dtype=torch.int64)
        self.mixed = torch.tensor([[1, 1, 1, 1], [1, 0, 1, 1]], dtype=torch.float32)
        self.risk = torch.tensor(
            [[0.2, 0.1, 0.0], [0.3, 0.5, 1.0], [0.1, 0.2, 0.3], [0.4, 0.2, 0.1]],
            dtype=torch.float32,
        )

    def test_full_availability_keeps_all_modalities(self) -> None:
        result = core.apply_availability_to_mri(self.data, self.full)
        self.assertTrue(torch.equal(result, self.data))

    def test_missing_t1c_zeroes_only_channel_1(self) -> None:
        availability = torch.tensor([[1, 0, 1, 1], [1, 0, 1, 1]])
        result = core.apply_availability_to_mri(self.data, availability)
        self.assertTrue(torch.equal(result[:, 1], torch.zeros_like(result[:, 1])))
        for channel in (0, 2, 3):
            self.assertTrue(torch.equal(result[:, channel], self.data[:, channel]))

    def test_per_sample_missing_patterns(self) -> None:
        availability = torch.tensor([[0, 1, 1, 1], [1, 1, 0, 1]])
        result = core.apply_availability_to_mri(self.data, availability)
        self.assertTrue(torch.equal(result[0, 0], torch.zeros_like(result[0, 0])))
        self.assertTrue(torch.equal(result[1, 2], torch.zeros_like(result[1, 2])))
        self.assertTrue(torch.equal(result[0, 2], self.data[0, 2]))
        self.assertTrue(torch.equal(result[1, 0], self.data[1, 0]))

    def test_input_is_not_modified_in_place(self) -> None:
        original = self.data.clone()
        _ = core.apply_availability_to_mri(self.data, self.mixed)
        _ = core.build_eight_channel_input(self.data, self.mixed)
        self.assertTrue(torch.equal(self.data, original))

    def test_invalid_availability_shape_rejected(self) -> None:
        for value in (torch.ones(4), torch.ones(2, 3), torch.ones(2, 4, 1)):
            with self.subTest(shape=tuple(value.shape)):
                with self.assertRaises(ValueError):
                    core.validate_availability(value)
        with self.assertRaises(ValueError):
            core.apply_availability_to_mri(self.data, torch.ones(1, 4))

    def test_invalid_availability_values_rejected(self) -> None:
        for bad in (-1.0, 1.1, 0.5):
            value = torch.ones(2, 4)
            value[0, 0] = bad
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    core.validate_availability(value)

    def test_broadcast_availability_shape_and_constants(self) -> None:
        result = core.broadcast_availability(
            self.mixed, (2, 3, 4), self.data.dtype, self.data.device
        )
        self.assertEqual(result.shape, (2, 4, 2, 3, 4))
        self.assertEqual(result.dtype, self.data.dtype)
        for batch in range(2):
            for channel in range(4):
                expected = torch.full(
                    (2, 3, 4), self.mixed[batch, channel], dtype=self.data.dtype
                )
                self.assertTrue(torch.equal(result[batch, channel], expected))

    def test_eight_channel_input_shape_and_order(self) -> None:
        result = core.build_eight_channel_input(self.data, self.mixed)
        self.assertEqual(result.shape, (2, 8, 2, 3, 4))
        expected_mri = core.apply_availability_to_mri(self.data, self.mixed)
        self.assertTrue(torch.equal(result[:, :4], expected_mri))
        self.assertTrue(
            torch.equal(
                result[:, 4:],
                core.broadcast_availability(
                    self.mixed, self.data.shape[2:], self.data.dtype, self.data.device
                ),
            )
        )

    def test_mask_matches_actual_zeroing(self) -> None:
        result = core.build_eight_channel_input(self.data + 1, self.mixed)
        masks = result[:, 4:]
        for batch in range(2):
            for channel in range(4):
                if self.mixed[batch, channel] == 0:
                    self.assertEqual(torch.count_nonzero(result[batch, channel]).item(), 0)
                    self.assertEqual(torch.count_nonzero(masks[batch, channel]).item(), 0)
                else:
                    self.assertTrue(torch.equal(result[batch, channel], self.data[batch, channel] + 1))
                    self.assertTrue(torch.all(masks[batch, channel] == 1).item())

    def test_region_targets_wt_tc_et_logic(self) -> None:
        labels = torch.tensor([[[[0, 1, 2, 3]]]], dtype=torch.int64)
        regions = core.build_region_targets(labels)
        self.assertEqual(regions.shape, (1, 3, 1, 1, 4))
        self.assertTrue(torch.equal(regions[0, 0, 0, 0], torch.tensor([0., 1., 1., 1.])))
        self.assertTrue(torch.equal(regions[0, 1, 0, 0], torch.tensor([0., 1., 0., 1.])))
        self.assertTrue(torch.equal(regions[0, 2, 0, 0], torch.tensor([0., 0., 0., 1.])))
        labels_5d = labels.unsqueeze(1)
        self.assertTrue(torch.equal(regions, core.build_region_targets(labels_5d)))

    def test_invalid_segmentation_labels_rejected(self) -> None:
        for bad in (-1, 4):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    core.build_region_targets(torch.tensor([[[[bad]]]]))

    def test_region_probabilities_shape_and_logic(self) -> None:
        probabilities = torch.tensor([0.1, 0.2, 0.3, 0.4])
        logits = probabilities.log().reshape(1, 4, 1, 1, 1)
        result = core.logits_to_region_probabilities(logits)
        self.assertEqual(result.shape, (1, 3, 1, 1, 1))
        self.assertTrue(
            torch.allclose(result.flatten(), torch.tensor([0.9, 0.6, 0.4]), atol=1e-6)
        )

    def test_region_loss_per_sample_per_region_shape(self) -> None:
        probabilities = torch.rand(2, 3, 2, 3, 4)
        targets = (torch.rand(2, 3, 2, 3, 4) > 0.5).float()
        result = core.per_sample_region_soft_dice_loss(probabilities, targets)
        self.assertEqual(result.shape, (2, 3))

    def test_empty_gt_empty_prediction_loss_near_zero(self) -> None:
        probabilities = torch.zeros(2, 3, 2, 2, 2)
        targets = torch.zeros_like(probabilities)
        result = core.per_sample_region_soft_dice_loss(probabilities, targets)
        self.assertTrue(torch.allclose(result, torch.zeros_like(result), atol=1e-7))

    def test_empty_gt_nonempty_prediction_is_penalized(self) -> None:
        targets = torch.zeros(1, 3, 2, 2, 2)
        low = core.per_sample_region_soft_dice_loss(torch.full_like(targets, 0.01), targets)
        high = core.per_sample_region_soft_dice_loss(torch.full_like(targets, 0.5), targets)
        self.assertTrue(torch.all(low > 0).item())
        self.assertTrue(torch.all(high > low).item())

    def test_region_loss_has_no_nan_or_inf(self) -> None:
        probabilities = torch.zeros(2, 3, 1, 1, 1)
        targets = torch.zeros_like(probabilities)
        targets[1, :, 0, 0, 0] = 1
        result = core.per_sample_region_soft_dice_loss(probabilities, targets)
        self.assertTrue(torch.isfinite(result).all().item())

    def test_full_input_risk_weights_equal_one(self) -> None:
        result = core.compute_risk_weights(self.full, self.risk)
        self.assertTrue(torch.equal(result, torch.ones_like(result)))

    def test_missing_t1c_risk_weights_are_sample_specific(self) -> None:
        result = core.compute_risk_weights(self.mixed, self.risk)
        self.assertTrue(torch.equal(result[0], torch.ones(3)))
        self.assertFalse(torch.equal(result[1], result[0]))

    def test_risk_weights_mean_equals_one(self) -> None:
        availability = torch.tensor([[1, 0, 1, 1], [0, 1, 0, 1], [1, 1, 1, 1]])
        result = core.compute_risk_weights(availability, self.risk)
        self.assertTrue(torch.allclose(result.mean(dim=1), torch.ones(3), atol=1e-6))

    def test_risk_weights_respect_clamp_and_renormalization(self) -> None:
        availability = torch.tensor([[1, 0, 1, 1]])
        risk = torch.zeros(4, 3)
        risk[1, 2] = 1
        result = core.compute_risk_weights(availability, risk, alpha=100.0)
        raw = torch.tensor([[1.0, 1.0, 101.0]])
        normalized = 3 * raw / raw.sum(dim=1, keepdim=True)
        clipped = normalized.clamp(0.5, 1.5)
        expected = 3 * clipped / clipped.sum(dim=1, keepdim=True)
        self.assertTrue(torch.allclose(result, expected, atol=1e-6))

    def test_risk_matrix_has_no_gradient(self) -> None:
        risk = self.risk.clone()
        availability = self.mixed.clone().requires_grad_(True)
        weights = core.compute_risk_weights(availability, risk)
        logits = torch.randn(2, 4, 1, 2, 2, requires_grad=True)
        targets = torch.zeros(2, 1, 1, 2, 2, dtype=torch.int64)
        per_sample = core.per_sample_region_soft_dice_loss(
            core.logits_to_region_probabilities(logits),
            core.build_region_targets(targets),
        )
        core.weighted_region_loss(per_sample, weights).backward()
        self.assertIsNone(risk.grad)
        self.assertIsNone(availability.grad)
        self.assertIsNotNone(logits.grad)

    def test_weighted_region_loss_scalar(self) -> None:
        losses = torch.tensor([[0.3, 0.6, 0.9], [0.2, 0.4, 0.6]])
        weights = torch.ones_like(losses)
        result = core.weighted_region_loss(losses, weights)
        self.assertEqual(result.ndim, 0)
        self.assertAlmostEqual(result.item(), 0.5, places=6)

    def test_total_loss_lambda_point_two(self) -> None:
        base = torch.tensor(2.0)
        region = torch.tensor(0.5)
        result = core.combine_total_loss(base, region)
        self.assertAlmostEqual(result.item(), 2.1, places=6)

    def test_total_loss_backward_is_finite(self) -> None:
        base = torch.tensor(2.0, requires_grad=True)
        logits = torch.randn(2, 4, 2, 2, 2, requires_grad=True)
        labels = torch.randint(0, 4, (2, 1, 2, 2, 2))
        per_sample = core.per_sample_region_soft_dice_loss(
            core.logits_to_region_probabilities(logits),
            core.build_region_targets(labels),
        )
        region = core.weighted_region_loss(
            per_sample, core.compute_risk_weights(self.mixed, self.risk)
        )
        total = core.combine_total_loss(base, region)
        total.backward()
        self.assertIsNotNone(logits.grad)
        self.assertTrue(torch.isfinite(logits.grad).all().item())
        self.assertTrue(torch.isfinite(base.grad).all().item())

    def test_region_loss_backward_is_finite(self) -> None:
        logits = torch.randn(2, 4, 2, 2, 2, requires_grad=True)
        labels = torch.randint(0, 4, (2, 1, 2, 2, 2))
        per_sample = core.per_sample_region_soft_dice_loss(
            core.logits_to_region_probabilities(logits),
            core.build_region_targets(labels),
        )
        region = core.weighted_region_loss(
            per_sample, core.compute_risk_weights(self.mixed, self.risk)
        )
        region.backward()
        self.assertIsNotNone(logits.grad)
        self.assertTrue(torch.isfinite(logits.grad).all().item())

    def test_deep_supervision_multiple_scales(self) -> None:
        outputs = [
            torch.randn(2, 4, 4, 4, 4, requires_grad=True),
            torch.randn(2, 4, 2, 2, 2, requires_grad=True),
        ]
        targets = [
            torch.randint(0, 4, (2, 1, 4, 4, 4)),
            torch.randint(0, 4, (2, 1, 2, 2, 2)),
        ]
        result = core.deep_supervision_region_loss(
            outputs, targets, [0.75, 0.25], self.mixed, self.risk
        )
        self.assertEqual(result.ndim, 0)
        self.assertTrue(torch.isfinite(result).item())
        result.backward()
        self.assertTrue(all(output.grad is not None for output in outputs))

    def test_zero_weight_deep_supervision_scale_ignored(self) -> None:
        output = torch.randn(2, 4, 2, 2, 2, requires_grad=True)
        ignored = torch.full((2, 5, 1, 1, 1), float("nan"))
        targets = [
            torch.randint(0, 4, (2, 1, 2, 2, 2)),
            torch.zeros(2, 1, 1, 1, 1, dtype=torch.int64),
        ]
        result = core.deep_supervision_region_loss(
            [output, ignored], targets, [1.0, 0.0], self.mixed, self.risk
        )
        self.assertTrue(torch.isfinite(result).item())

    def test_deep_supervision_mismatched_lengths_rejected(self) -> None:
        with self.assertRaises(ValueError):
            core.deep_supervision_region_loss(
                [torch.randn(2, 4, 2, 2, 2)],
                [torch.zeros(2, 1, 2, 2, 2, dtype=torch.int64)] * 2,
                [1.0],
                self.mixed,
                self.risk,
            )

    def test_batch_with_full_and_missing_t1c_samples(self) -> None:
        eight = core.build_eight_channel_input(self.data + 1, self.mixed)
        weights = core.compute_risk_weights(self.mixed, self.risk)
        self.assertTrue(torch.equal(eight[0, :4], self.data[0] + 1))
        self.assertEqual(torch.count_nonzero(eight[1, 1]).item(), 0)
        self.assertTrue(torch.equal(weights[0], torch.ones(3)))
        self.assertFalse(torch.equal(weights[1], weights[0]))

    def test_repeated_run_is_deterministic(self) -> None:
        labels = torch.randint(0, 4, (2, 1, 2, 3, 4))
        probabilities = torch.rand(2, 3, 2, 3, 4)
        first = (
            core.apply_availability_to_mri(self.data, self.mixed),
            core.build_eight_channel_input(self.data, self.mixed),
            core.build_region_targets(labels),
            core.compute_risk_weights(self.mixed, self.risk),
            core.per_sample_region_soft_dice_loss(
                probabilities, core.build_region_targets(labels)
            ),
        )
        second = (
            core.apply_availability_to_mri(self.data, self.mixed),
            core.build_eight_channel_input(self.data, self.mixed),
            core.build_region_targets(labels),
            core.compute_risk_weights(self.mixed, self.risk),
            core.per_sample_region_soft_dice_loss(
                probabilities, core.build_region_targets(labels)
            ),
        )
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(first, second)))

    def test_public_api_imports_successfully(self) -> None:
        module = importlib.import_module("risk_aware_core")
        required = {
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
        }
        self.assertTrue(required.issubset(set(module.__all__)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
