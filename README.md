# BraTS 2023 Missing-Modality Segmentation

This repository records experiments for BraTS 2023 GLI missing-modality brain tumor segmentation.

## Current stage

- Full-only nnU-Net baseline completed.
- Zero-filled missing-modality direct-inference stress test completed.
- Modality Dropout nnU-Net baseline completed.
- Paper-ready tables and figures generated.

## Dataset

Dataset: BraTS 2023 GLI.

The dataset itself is not included in this repository.

## Important protocol

Current results are based on:

- fold 0
- 251 validation cases
- nnU-Net v2 3d_fullres
- checkpoint_best.pth
- zero-filled missing-modality direct-inference protocol
- single-fold preliminary benchmark

## Regions

- WT = labels 1 + 2 + 3
- TC = labels 1 + 3
- ET = label 3

## Main finding

Full-only nnU-Net shows region-dependent degradation under missing modalities. Missing T1c mainly damages TC and ET, while missing FLAIR mainly damages WT. Modality Dropout substantially mitigates this degradation, but residual ET degradation remains under missing T1c.

## Repository contents

- `docs/`: project state and experiment notes
- `scripts/`: utility scripts
- `results/paper_assets_moddrop/`: CSV, Excel, PNG figures and README for paper assets

## Do not upload

- BraTS raw data
- nnU-Net preprocessed data
- model checkpoints
- prediction NIfTI files
- API keys or tokens
