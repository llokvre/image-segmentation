# BraTS 2023 Missing-Modality Segmentation

This repository records experiments for BraTS 2023 GLI missing-modality brain tumor segmentation.

## Current status — 2026-10-20

- A0/A1/A2, teacher qualification, B1–B4 and the 800-case projection audit are archived.
- B1–B4 did not improve the Missing T1c ET primary endpoint; the tested case-level projection route failed its gate.
- No new training is authorized. Next: a zero-training feasibility/leakage audit, not another 1000-epoch run.
- [完整中文进度与展望](docs/progress/PROGRESS_AND_OUTLOOK_20261020.md)
- [当前唯一下一步](CURRENT_NEXT_STEP.md) · [核实指标与来源哈希](results/progress_20261020/README.md)
- The sections below describe the historical baseline protocol, not a new independent validation. The repeatedly used 200 cases are development data; the historical 251 cases are not an untouched external cohort.

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
