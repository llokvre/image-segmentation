"""A2 nnU-Net Trainer: Modality Dropout + explicit availability channels."""

import torch
from torch import autocast, nn

from nnunetv2.training.loss.dice import get_tp_fp_fn_tn
from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer
from nnunetv2.utilities.helpers import dummy_context
from nnunetv2.utilities.plans_handling.plans_handler import (
    ConfigurationManager,
    PlansManager,
)

from availability_integration import (
    A1_MODALITY_DROPOUT_PROBABILITY,
    build_a2_input,
    build_full_validation_input,
    sample_modality_dropout_with_availability,
)


class nnUNetTrainerModDropAvailabilityMask(nnUNetTrainer):
    """A2 trainer preserving A1 sampling/loss while changing input 4 -> 8."""

    modality_dropout_probability = A1_MODALITY_DROPOUT_PROBABILITY

    @staticmethod
    def build_network_architecture(
        plans_manager: PlansManager,
        configuration_manager: ConfigurationManager,
        num_input_channels: int,
        num_output_channels: int,
        enable_deep_supervision: bool = True,
    ) -> nn.Module:
        """Build the standard nnU-Net architecture with eight input channels."""

        if num_input_channels != 4:
            raise ValueError(
                "Dataset501 must report four MRI input channels before A2 "
                f"adaptation, got {num_input_channels}"
            )
        return nnUNetTrainer.build_network_architecture(
            plans_manager,
            configuration_manager,
            8,
            num_output_channels,
            enable_deep_supervision,
        )

    @staticmethod
    def apply_modality_dropout_with_availability(
        data: torch.Tensor, probability: float
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return A1-equivalent masked MRI and its single sampled pattern."""

        return sample_modality_dropout_with_availability(data, probability)

    def _prepare_a2_training_input(
        self, data: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        masked_data, availability = self.apply_modality_dropout_with_availability(
            data=data,
            probability=self.modality_dropout_probability,
        )
        network_input = build_a2_input(data, masked_data, availability)
        return network_input, availability

    def _prepare_a2_validation_input(
        self, data: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        return build_full_validation_input(data)

    def train_step(self, batch: dict) -> dict:
        """Preserve the real A1 train control flow with one explicit pattern."""

        data = batch["data"]
        target = batch["target"]

        data = data.to(self.device, non_blocking=True)
        data, _availability = self._prepare_a2_training_input(data)

        if isinstance(target, list):
            target = [item.to(self.device, non_blocking=True) for item in target]
        else:
            target = target.to(self.device, non_blocking=True)

        self.optimizer.zero_grad(set_to_none=True)

        with (
            autocast(self.device.type, enabled=True)
            if self.device.type == "cuda"
            else dummy_context()
        ):
            output = self.network(data)
            loss = self.loss(output, target)

        if self.grad_scaler is not None:
            self.grad_scaler.scale(loss).backward()
            self.grad_scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.network.parameters(), 12)
            self.grad_scaler.step(self.optimizer)
            self.grad_scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network.parameters(), 12)
            self.optimizer.step()

        return {"loss": loss.detach().cpu().numpy()}

    def validation_step(self, batch: dict) -> dict:
        """Use full MRI plus four all-one availability channels."""

        data = batch["data"]
        target = batch["target"]

        data = data.to(self.device, non_blocking=True)
        data, availability = self._prepare_a2_validation_input(data)
        if not torch.equal(
            availability, torch.ones_like(availability)
        ):
            raise AssertionError("A2 validation availability must be all ones")

        if isinstance(target, list):
            target = [item.to(self.device, non_blocking=True) for item in target]
        else:
            target = target.to(self.device, non_blocking=True)

        with (
            autocast(self.device.type, enabled=True)
            if self.device.type == "cuda"
            else dummy_context()
        ):
            output = self.network(data)
            del data
            loss = self.loss(output, target)

        if self.enable_deep_supervision:
            output = output[0]
            target = target[0]

        axes = [0] + list(range(2, output.ndim))
        if self.label_manager.has_regions:
            predicted_segmentation_onehot = (torch.sigmoid(output) > 0.5).long()
        else:
            output_seg = output.argmax(1)[:, None]
            predicted_segmentation_onehot = torch.zeros(
                output.shape, device=output.device, dtype=torch.float16
            )
            predicted_segmentation_onehot.scatter_(1, output_seg, 1)
            del output_seg

        if self.label_manager.has_ignore_label:
            if not self.label_manager.has_regions:
                mask = (target != self.label_manager.ignore_label).float()
                target[target == self.label_manager.ignore_label] = 0
            else:
                if target.dtype == torch.bool:
                    mask = ~target[:, -1:]
                else:
                    mask = 1 - target[:, -1:]
                target = target[:, :-1]
        else:
            mask = None

        tp, fp, fn, _ = get_tp_fp_fn_tn(
            predicted_segmentation_onehot, target, axes=axes, mask=mask
        )
        tp_hard = tp.detach().cpu().numpy()
        fp_hard = fp.detach().cpu().numpy()
        fn_hard = fn.detach().cpu().numpy()
        if not self.label_manager.has_regions:
            tp_hard = tp_hard[1:]
            fp_hard = fp_hard[1:]
            fn_hard = fn_hard[1:]

        return {
            "loss": loss.detach().cpu().numpy(),
            "tp_hard": tp_hard,
            "fp_hard": fp_hard,
            "fn_hard": fn_hard,
        }
