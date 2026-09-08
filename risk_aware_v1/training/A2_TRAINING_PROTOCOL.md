# A2 fold 0 formal training protocol

- Scientific purpose: test whether explicit per-modality availability channels improve robustness beyond A1 ModDrop.
- The only structural A1→A2 difference is the input expansion from four MRI channels to eight channels: `[T1n,T1c,T2w,FLAIR,a_T1n,a_T1c,a_T2w,a_FLAIR]`.
- Dataset/configuration/fold: Dataset501_BraTS2023, 3d_fullres, fold 0.
- ModDrop: independently per sample, probability 0.5; if triggered, one of four MRI channels is uniformly selected and zeroed exactly once.
- Availability is sampled from the same dropout decision and concatenated after the four MRI channels.
- Validation uses all MRI modalities and four all-one availability channels.
- Hyperparameters inherit the real A1/parent configuration: 1000 epochs; 250 train and 50 validation iterations per epoch; SGD lr 0.01, momentum 0.99, Nesterov, weight decay 3e-5; PolyLR; batch 2; patch 128³; deep supervision enabled; nnUNet_compile=false matching the final completed A1 run.
- Output is isolated under `nnUNetTrainerModDropAvailabilityMask__nnUNetPlans__3d_fullres/fold_0`.
- Checkpoints: best EMA pseudo Dice; latest every 50 epochs except final; final at training completion. Validation runs each epoch.
- Monitor with `bash risk_aware_v1_a2_training/monitor_a2_fold0.sh`.
- Stop only on explicit request with `bash risk_aware_v1_a2_training/stop_a2_fold0_safely.sh`; it sends SIGINT and never force-kills.
- After completion, inference/evaluation will be a separate explicitly authorized task.
- No hyperparameter may be changed in response to validation results during this run.
- A3, A4, calibration, inference and predictions are outside this task.
- Fold 0 is preliminary evidence only.
- A1 checkpoint or pretrained weights are never loaded; A2 starts from random initialization.

- Frozen-package import adjustment: only two imports were changed to package-relative imports; the complete diff is retained in runtime/import_adjustments.diff and all regressions were rerun.
