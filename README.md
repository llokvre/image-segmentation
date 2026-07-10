# BraTS 2023 GLI Missing-Modality Segmentation

This repository records a research workflow for robust brain-tumor segmentation under missing MRI modalities. The current benchmark compares a full-modality nnU-Net baseline with a Modality Dropout training baseline on BraTS 2023 GLI data.

> Current status: fold 0 single-fold preliminary benchmark. The results are stress-test evidence, not a final clinical evaluation, SOTA claim, or statistical-significance claim.

## Project Overview

The project asks how segmentation quality changes when one of four MRI modalities is unavailable at inference time, and whether training with randomized single-modality dropout improves robustness. The immediate scientific focus is the interaction between the missing modality and the tumor region being segmented.

## Research Motivation

Missing-modality degradation is unlikely to be uniform across all tumor regions. A model may preserve whole-tumor segmentation while losing tumor-core or enhancing-tumor detail. The current baseline experiments are therefore used to map a modality-region risk pattern before designing a risk-aware training method.

## Dataset Notice

The experiments use BraTS 2023 GLI data. The dataset, patient images, labels, predictions, nnU-Net preprocessing outputs, and model checkpoints are **not included** in this repository. Users must obtain and use the data according to the dataset and challenge terms.

## Task Definition

- Input: four-channel 3D MRI volumes.
- Output: BraTS tumor segmentation labels.
- Baseline configuration: nnU-Net v2, `3d_fullres`, fold 0.
- Validation set: 251 cases.
- Checkpoint: `checkpoint_best.pth` in the original training environment; the checkpoint is not stored here.

## MRI Modalities

| Channel | Modality |
|---|---|
| `_0000` | T1n |
| `_0001` | T1c |
| `_0002` | T2w |
| `_0003` | FLAIR / T2f |

## BraTS Labels and Regions

| Label | Meaning |
|---:|---|
| 0 | Background |
| 1 | NCR/NET |
| 2 | Edema |
| 3 | Enhancing tumor |

| Region | Definition |
|---|---|
| WT | labels 1 + 2 + 3 |
| TC | labels 1 + 3 |
| ET | label 3 |

## Experimental Protocol

### Full-only baseline

The baseline is trained using complete four-modality input only. At inference, one modality is replaced with an all-zero volume while the model still receives four channels. This is the **zero-filled missing-modality direct-inference protocol**.

### Modality Dropout baseline

The custom trainer `nnUNetTrainerModalityDropout` uses the following training policy:

- 50% probability: keep all four modalities;
- 50% probability: randomly zero exactly one modality;
- at most one modality is zeroed per sample;
- validation and inference use deterministic fixed input conditions.

Both models are evaluated with full input and with one missing modality in turn: T1c, FLAIR, T2w, and T1n.

## Current Results Summary

The following values are the current fold 0 benchmark values used by the paper assets. Regional values are reported as mean +/- standard deviation; the reported Mean is the arithmetic mean of WT, TC, and ET means.

| Model | Input | WT | TC | ET | Mean |
|---|---|---:|---:|---:|---:|
| Full-only | Full | 0.9326 +/- 0.0839 | 0.9106 +/- 0.1645 | 0.8669 +/- 0.1943 | 0.9034 |
| Full-only | Missing T1c | 0.9019 +/- 0.1116 | 0.2648 +/- 0.2955 | 0.0599 +/- 0.1643 | 0.4089 |
| Full-only | Missing FLAIR | 0.7070 +/- 0.2335 | 0.8625 +/- 0.2317 | 0.8308 +/- 0.2296 | 0.8001 |
| Full-only | Missing T2w | 0.8334 +/- 0.2183 | 0.8578 +/- 0.2462 | 0.8391 +/- 0.2106 | 0.8434 |
| Full-only | Missing T1n | 0.9287 +/- 0.0613 | 0.9057 +/- 0.1547 | 0.8585 +/- 0.1837 | 0.8976 |
| Modality Dropout | Full | 0.9360 +/- 0.0835 | 0.9133 +/- 0.1558 | 0.8723 +/- 0.1833 | 0.9072 |
| Modality Dropout | Missing T1c | 0.9272 +/- 0.0887 | 0.8095 +/- 0.1782 | 0.6540 +/- 0.2179 | 0.7969 |
| Modality Dropout | Missing FLAIR | 0.9016 +/- 0.1027 | 0.9024 +/- 0.1763 | 0.8626 +/- 0.1956 | 0.8889 |
| Modality Dropout | Missing T2w | 0.9290 +/- 0.0855 | 0.9049 +/- 0.1689 | 0.8619 +/- 0.1967 | 0.8986 |
| Modality Dropout | Missing T1n | 0.9338 +/- 0.0839 | 0.9059 +/- 0.1657 | 0.8660 +/- 0.1868 | 0.9019 |

## Main Findings

1. The Full-only model shows a region-dependent degradation pattern under missing modalities.
2. Missing T1c mainly affects TC and ET, with the largest observed drop for ET.
3. Missing FLAIR mainly affects WT.
4. Missing T2w causes a moderate degradation in this protocol.
5. Missing T1n has the smallest observed effect.
6. Modality Dropout substantially reduces the observed degradation for all four single-modality stress tests.
7. No obvious complete-input performance penalty is observed in this single fold.
8. Residual degradation remains for ET and TC under Missing T1c, motivating a modality-region risk-aware method.

These statements describe the current benchmark only. They do not establish statistical significance, clinical validity, or generalization beyond the evaluated fold and protocol.

## Repository Structure

```text
.
├── README.md
├── .gitignore
├── docs/
│   ├── paper_draft/             # Chinese working draft for the paper
│   ├── experiments/             # Experiment-specific records
│   ├── method_idea/             # Planned next-stage method
│   ├── TODO.md
│   ├── PROJECT_STATE.md
│   ├── CURRENT_NEXT_STEP.md
│   └── experiments_record.md
├── scripts/
│   └── generate_moddrop_paper_assets.py
├── requirements-paper-assets.txt
└── results/
    └── paper_assets_moddrop/    # CSV, XLSX, PNG and provenance notes
```

## Reproduction Instructions

The repository contains the verified fallback benchmark values and generated assets, but not the source metric JSON files. To regenerate the current local paper assets from the checked-in fallback values:

```bash
python -m pip install -r requirements-paper-assets.txt
python scripts/generate_moddrop_paper_assets.py \
  --output-dir results/paper_assets_moddrop
```

When the original experiment directory is available, pass its actual local path explicitly rather than editing a hard-coded path in the script:

```bash
python scripts/generate_moddrop_paper_assets.py \
  --project-root /path/to/nnunet_project \
  --benchmark-root /path/to/missing_modality_benchmark \
  --output-dir results/paper_assets_moddrop
```

The script only reads candidate metric files and writes CSV, XLSX, PNG, README, and validation-log outputs under the selected output directory. It does not modify raw data, predictions, or model files. If no readable metric JSON is found, it records that the manually verified fallback values were used.

## Limitations

- The current benchmark uses only fold 0 and 251 validation cases.
- Missing modalities are simulated by zero-filling one channel during direct inference.
- The zero-filled protocol is a controlled stress test and is not the only possible clinical missing-modality setting.
- The current paper assets use fallback values because the source JSON/CSV metric paths are not present in this repository.
- No statistical test, multi-fold confidence interval, HD95, calibration analysis, or clinical validation is included yet.
- The current Modality Dropout implementation is a strong robustness baseline, not the final proposed contribution.

## Next Steps

1. Reconcile the source JSON/CSV paths and regenerate the assets from machine-readable metrics.
2. Add qualitative case-level visualizations and inspect figure typography at target publication size.
3. Run multi-fold evaluation and add complementary metrics such as HD95.
4. Prototype modality-region risk-aware pseudo-label filtering and risk-calibrated missing-modality training.
5. Plan ablations for uncertainty filtering, region-adaptive thresholds, consistency learning, and reliability weighting.

## Citation Placeholder

```bibtex
@misc{brats_missing_modality_placeholder,
  title  = {BraTS 2023 Missing-Modality Segmentation},
  author = {Author names to be added},
  year   = {2026},
  note   = {Preliminary research repository; citation details to be finalized}
}
```
