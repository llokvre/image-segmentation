"""Synthetic and interface tests for the A2 missing-modality predictor."""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from a2_inference_adapter import (
    A1_CHECKPOINT,
    BEST_CHECKPOINT,
    A2MissingModalityPredictor,
    availability_for_pattern,
    build_a2_inference_input,
    checkpoint_input_channels,
    require_a2_checkpoint,
)


class Stage2CInferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = torch.arange(
            4 * 5 * 6 * 7, dtype=torch.float32
        ).reshape(4, 5, 6, 7) + 1

    def test_01_full_mapping(self):
        self.assertEqual(availability_for_pattern("full"), (1, 1, 1, 1))

    def test_02_t1n_mapping(self):
        self.assertEqual(availability_for_pattern("t1n"), (0, 1, 1, 1))

    def test_03_t1c_mapping(self):
        self.assertEqual(availability_for_pattern("t1c"), (1, 0, 1, 1))

    def test_04_t2w_mapping(self):
        self.assertEqual(availability_for_pattern("t2w"), (1, 1, 0, 1))

    def test_05_flair_mapping(self):
        self.assertEqual(availability_for_pattern("flair"), (1, 1, 1, 0))

    def test_06_invalid_pattern_rejected(self):
        with self.assertRaises(ValueError):
            availability_for_pattern("unknown")

    def test_07_full_does_not_zero_mri(self):
        result, _ = build_a2_inference_input(self.data, missing_pattern="full")
        self.assertTrue(torch.equal(result[:4], self.data))

    def test_08_t1c_zeros_only_channel_one(self):
        result, _ = build_a2_inference_input(self.data, missing_pattern="t1c")
        self.assertEqual(torch.count_nonzero(result[1]).item(), 0)
        for channel in (0, 2, 3):
            self.assertTrue(torch.equal(result[channel], self.data[channel]))

    def test_09_full_availability_all_one(self):
        result, _ = build_a2_inference_input(self.data, missing_pattern="full")
        self.assertTrue(torch.equal(result[4:], torch.ones_like(result[4:])))

    def test_10_t1c_availability_correct(self):
        result, _ = build_a2_inference_input(self.data, missing_pattern="t1c")
        expected = torch.tensor([1, 0, 1, 1], dtype=result.dtype)
        for channel in range(4):
            self.assertTrue(torch.all(result[channel + 4] == expected[channel]).item())

    def test_11_network_input_has_eight_channels(self):
        result, _ = build_a2_inference_input(self.data, missing_pattern="full")
        self.assertEqual(result.shape, (8, 5, 6, 7))

    def test_12_availability_is_spatially_constant(self):
        result, _ = build_a2_inference_input(self.data, missing_pattern="t2w")
        for channel in range(4, 8):
            self.assertEqual(torch.unique(result[channel]).numel(), 1)

    def test_13_best_checkpoint_is_eight_channel(self):
        self.assertEqual(require_a2_checkpoint(BEST_CHECKPOINT), 8)

    def test_14_a1_checkpoint_is_rejected(self):
        self.assertEqual(checkpoint_input_channels(A1_CHECKPOINT), 4)
        with self.assertRaises(ValueError):
            require_a2_checkpoint(A1_CHECKPOINT)

    def test_15_predictor_requires_explicit_missing_pattern(self):
        signature = inspect.signature(
            A2MissingModalityPredictor.predict_logits_from_preprocessed_data
        )
        parameter = signature.parameters["missing_pattern"]
        self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(parameter.default, inspect.Parameter.empty)

    def test_16_no_zero_value_inference(self):
        data = self.data.clone()
        data[2] = 0
        result, audit = build_a2_inference_input(data, missing_pattern="full")
        self.assertEqual(audit["availability"], [1, 1, 1, 1])
        self.assertFalse(audit["availability_inferred_from_zero_mri"])
        self.assertTrue(torch.all(result[6] == 1).item())

    def test_17_sliding_window_receives_eight_channels(self):
        predictor = object.__new__(A2MissingModalityPredictor)
        predictor.last_input_audit = None
        predictor.last_sliding_window_patch_count = 1
        seen = {}

        def fake_base(_self, prepared):
            seen["shape"] = tuple(prepared.shape)
            _self.last_sliding_window_patch_count = 1
            return torch.zeros(4, *prepared.shape[1:])

        with patch(
            "nnunetv2.inference.predict_from_raw_data.nnUNetPredictor."
            "predict_logits_from_preprocessed_data",
            new=fake_base,
        ):
            predictor.predict_logits_from_preprocessed_data(
                self.data, missing_pattern="t1c"
            )
        self.assertEqual(seen["shape"][0], 8)

    def test_18_output_classes_are_four(self):
        import json
        from nnunetv2.utilities.plans_handling.plans_handler import PlansManager
        from a2_inference_adapter import RESULTS_DIR

        plans = json.loads((RESULTS_DIR / "plans.json").read_text())
        dataset_json = json.loads((RESULTS_DIR / "dataset.json").read_text())
        self.assertEqual(
            PlansManager(plans).get_label_manager(dataset_json).num_segmentation_heads,
            4,
        )

    def test_19_pattern_mapping_is_deterministic(self):
        for name in ("full", "t1n", "t1c", "t2w", "flair"):
            self.assertEqual(
                availability_for_pattern(name), availability_for_pattern(name)
            )

    def test_20_crop_preserves_availability_constants(self):
        result, _ = build_a2_inference_input(self.data, missing_pattern="t1c")
        crop = result[:, 1:4, 2:6, 1:5]
        for channel, expected in enumerate((1, 0, 1, 1)):
            self.assertTrue(torch.all(crop[channel + 4] == expected).item())

    def test_21_mirroring_source_flips_only_spatial_axes(self):
        source = inspect.getsource(A2MissingModalityPredictor.__mro__[1]._internal_maybe_mirror_and_predict)
        self.assertIn("mirror_axes = [m + 2 for m in mirror_axes]", source)

    def test_22_audit_records_exact_t1c_state(self):
        _, audit = build_a2_inference_input(self.data, missing_pattern="t1c")
        self.assertEqual(audit["mri_zeroed_channels"], [1])
        self.assertEqual(audit["availability"], [1, 0, 1, 1])
        self.assertEqual(audit["network_channels"], 8)
        self.assertEqual(audit["availability_zeroing_consistency"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
