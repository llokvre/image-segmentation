# BraTS Missing-Modality Paper Assets

## Reproduction

```bash
python scripts/generate_moddrop_paper_assets.py --output-dir results/paper_assets_moddrop
```

When source metrics are available, provide their actual paths with
`--project-root` and `--benchmark-root`. This repository does not assume a
remote server path.

## Data provenance

The current checked-in CSV, XLSX and PNG assets use the manually verified
fold-0 fallback values because the source metric JSON/CSV files are not in the
repository. The script marks these rows with `used_fallback=True` and writes
the source status to `validation_log.txt`.

This is a single-fold preliminary benchmark under the zero-filled
missing-modality direct-inference stress-test protocol. Modality Dropout is a
strong baseline, not the final proposed method. The results do not establish
statistical significance or clinical validation.

## Current observations

- Missing T1c mainly affects TC and ET for the Full-only model.
- Missing FLAIR mainly affects WT for the Full-only model.
- Modality Dropout reduces the observed degradation across all four missing-modality settings.
- Residual ET degradation remains under Missing T1c.

## Asset list

- `all_results_long.csv`: long-format values and source/fallback flags.
- `all_results_wide.csv`: wide-format values and per-model Dice drops.
- `all_results_summary.xlsx`: summary tables, protocol and validation log.
- `absolute_dice_fullonly_vs_moddrop.png`: absolute Dice comparison.
- `dice_drop_fullonly_vs_moddrop.png`: Dice drop from complete input.
- `modality_region_risk_heatmap_fullonly.png`: Full-only risk matrix.
- `modality_region_risk_heatmap_moddrop.png`: Modality Dropout risk matrix.
- `modality_dropout_recovery_heatmap.png`: recovery gain heatmap.
- `modality_dropout_recovery_table.png`: recovery gain table.
- `mean_dice_comparison.png`: mean Dice comparison.
