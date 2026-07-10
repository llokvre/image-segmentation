#!/usr/bin/env python3
"""Generate reproducible paper assets for the missing-modality benchmark.

The script reads metric JSON/CSV files when they are available. If the source
metrics cannot be found, it uses the manually verified fold-0 values recorded
in ``FALLBACK`` and marks every affected row in the validation log. The script
only writes derived assets under ``OUTPUT_DIR``; it never edits raw images,
predictions, labels, or model checkpoints.

Examples
--------
Use the checked-in fallback values and write local assets::

    python scripts/generate_moddrop_paper_assets.py \
        --output-dir results/paper_assets_moddrop

Use source metrics from an explicitly supplied experiment directory::

    python scripts/generate_moddrop_paper_assets.py \
        --project-root /path/to/nnunet_project \
        --benchmark-root /path/to/missing_modality_benchmark \
        --output-dir results/paper_assets_moddrop

The three path arguments also accept the environment variables
``BRATS_PROJECT_ROOT``, ``BRATS_BENCHMARK_ROOT`` and
``PAPER_ASSET_OUTPUT_DIR``. No remote or machine-specific path is assumed.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from openpyxl import load_workbook
    from openpyxl.formatting.rule import ColorScaleRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    HAVE_OPENPYXL = True
except Exception:
    HAVE_OPENPYXL = False


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = REPO_ROOT
BENCHMARK_ROOT = REPO_ROOT / "results" / "paper_assets_moddrop"
OUTPUT_DIR = REPO_ROOT / "results" / "paper_assets_moddrop"
DPI = 300
REGIONS = ["WT", "TC", "ET"]
MODELS = ["Full-only", "Modality Dropout"]
SETTINGS = ["Full input", "Missing T1c", "Missing FLAIR", "Missing T2w", "Missing T1n"]
MISSING = SETTINGS[1:]
CANDIDATES: dict[tuple[str, str], list[Path]] = {}
LOG: list[str] = []


# These values are a provenance-preserving fallback, not a replacement for
# machine-readable source metrics. They match the current manually confirmed
# fold-0 benchmark described in the repository documentation.
FALLBACK = {
    "Full-only": {
        "Full input": {"WT": (0.9326, 0.0839), "TC": (0.9106, 0.1645), "ET": (0.8669, 0.1943), "Mean": (0.9034, np.nan)},
        "Missing T1c": {"WT": (0.9019, 0.1116), "TC": (0.2648, 0.2955), "ET": (0.0599, 0.1643), "Mean": (0.4089, np.nan)},
        "Missing FLAIR": {"WT": (0.7070, 0.2335), "TC": (0.8625, 0.2317), "ET": (0.8308, 0.2296), "Mean": (0.8001, np.nan)},
        "Missing T2w": {"WT": (0.8334, 0.2183), "TC": (0.8578, 0.2462), "ET": (0.8391, 0.2106), "Mean": (0.8434, np.nan)},
        "Missing T1n": {"WT": (0.9287, 0.0613), "TC": (0.9057, 0.1547), "ET": (0.8585, 0.1837), "Mean": (0.8976, np.nan)},
    },
    "Modality Dropout": {
        "Full input": {"WT": (0.9360, 0.0835), "TC": (0.9133, 0.1558), "ET": (0.8723, 0.1833), "Mean": (0.9072, np.nan)},
        "Missing T1c": {"WT": (0.9272, 0.0887), "TC": (0.8095, 0.1782), "ET": (0.6540, 0.2179), "Mean": (0.7969, np.nan)},
        "Missing FLAIR": {"WT": (0.9016, 0.1027), "TC": (0.9024, 0.1763), "ET": (0.8626, 0.1956), "Mean": (0.8889, np.nan)},
        "Missing T2w": {"WT": (0.9290, 0.0855), "TC": (0.9049, 0.1689), "ET": (0.8619, 0.1967), "Mean": (0.8986, np.nan)},
        "Missing T1n": {"WT": (0.9338, 0.0839), "TC": (0.9059, 0.1657), "ET": (0.8660, 0.1868), "Mean": (0.9019, np.nan)},
    },
}


def parse_args() -> argparse.Namespace:
    """Parse explicit paths so the script is portable across machines."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=os.getenv("BRATS_PROJECT_ROOT"), help="Root containing nnUNet_results or source experiment folders.")
    parser.add_argument("--benchmark-root", default=os.getenv("BRATS_BENCHMARK_ROOT"), help="Root containing missing-modality metric folders.")
    parser.add_argument("--output-dir", default=os.getenv("PAPER_ASSET_OUTPUT_DIR"), help="Directory receiving generated assets.")
    parser.add_argument("--fail-on-fallback", action="store_true", help="Exit with an error if any source metric falls back to verified values.")
    return parser.parse_args()


def configure_paths(args: argparse.Namespace) -> None:
    """Resolve configured paths and construct candidate metric locations."""
    global PROJECT_ROOT, BENCHMARK_ROOT, OUTPUT_DIR, CANDIDATES
    PROJECT_ROOT = Path(args.project_root or REPO_ROOT).expanduser().resolve()
    BENCHMARK_ROOT = Path(args.benchmark_root or (REPO_ROOT / "results" / "paper_assets_moddrop")).expanduser().resolve()
    OUTPUT_DIR = Path(args.output_dir or (REPO_ROOT / "results" / "paper_assets_moddrop")).expanduser().resolve()

    CANDIDATES = {
        ("Full-only", "Full input"): [BENCHMARK_ROOT / "fold_0_full_best" / "metrics", BENCHMARK_ROOT / "fold_0_full_best"],
        ("Full-only", "Missing T1c"): [BENCHMARK_ROOT / "fold_0_missing_T1c" / "metrics", BENCHMARK_ROOT / "fold_0_missing_T1c"],
        ("Full-only", "Missing FLAIR"): [BENCHMARK_ROOT / "fold_0_missing_FLAIR" / "metrics", BENCHMARK_ROOT / "fold_0_missing_FLAIR"],
        ("Full-only", "Missing T2w"): [BENCHMARK_ROOT / "fold_0_missing_T2w" / "metrics", BENCHMARK_ROOT / "fold_0_missing_T2w"],
        ("Full-only", "Missing T1n"): [BENCHMARK_ROOT / "fold_0_missing_T1n" / "metrics", BENCHMARK_ROOT / "fold_0_missing_T1n"],
        ("Modality Dropout", "Full input"): [
            PROJECT_ROOT / "nnUNet_results" / "Dataset501_BraTS2023" / "nnUNetTrainerModalityDropout__nnUNetPlans__3d_fullres" / "fold_0" / "metrics",
            PROJECT_ROOT / "nnUNet_results" / "Dataset501_BraTS2023" / "nnUNetTrainerModalityDropout__nnUNetPlans__3d_fullres" / "fold_0",
        ],
        ("Modality Dropout", "Missing T1c"): [BENCHMARK_ROOT / "moddrop_fold_0_missing_T1c" / "metrics", BENCHMARK_ROOT / "moddrop_fold_0_missing_T1c"],
        ("Modality Dropout", "Missing FLAIR"): [BENCHMARK_ROOT / "moddrop_fold_0_missing_FLAIR" / "metrics", BENCHMARK_ROOT / "moddrop_fold_0_missing_FLAIR"],
        ("Modality Dropout", "Missing T2w"): [BENCHMARK_ROOT / "moddrop_fold_0_missing_T2w" / "metrics", BENCHMARK_ROOT / "moddrop_fold_0_missing_T2w"],
        ("Modality Dropout", "Missing T1n"): [BENCHMARK_ROOT / "moddrop_fold_0_missing_T1n" / "metrics", BENCHMARK_ROOT / "moddrop_fold_0_missing_T1n"],
    }


def log(message: str, level: str = "INFO") -> None:
    line = f"[{level}] {message}"
    LOG.append(line)
    print(line)


def finite(value: Any) -> bool:
    try:
        return value is not None and math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def normalize_key(value: Any) -> str:
    return str(value).replace("_", " ").replace("-", " ").strip().lower()


def find_value(obj: Any, names: list[str]) -> Any:
    """Find a named value in common nested nnU-Net JSON structures."""
    wanted = {normalize_key(name) for name in names}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if normalize_key(key) in wanted:
                return value
        for value in obj.values():
            result = find_value(value, names)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for value in obj:
            result = find_value(value, names)
            if result is not None:
                return result
    return None


def mean_std(value: Any) -> tuple[float, float]:
    if finite(value):
        return float(value), np.nan
    if not isinstance(value, dict):
        return np.nan, np.nan
    mean = np.nan
    std = np.nan
    for key, item in value.items():
        key_name = normalize_key(key)
        if key_name in {"mean", "avg", "average", "dice mean", "score", "value"} and finite(item):
            mean = float(item)
        if key_name in {"std", "stdev", "standard deviation", "dice std"} and finite(item):
            std = float(item)
    if finite(mean):
        return mean, std
    if len(value) == 1:
        return mean_std(next(iter(value.values())))
    return np.nan, np.nan


def aliases(region: str) -> list[str]:
    return {
        "WT": ["WT", "whole tumor", "whole_tumor"],
        "TC": ["TC", "tumor core", "tumor_core"],
        "ET": ["ET", "enhancing tumor", "enhancing_tumor"],
        "Mean": ["Mean", "mean dice", "mean_dice"],
    }[region]


def parse_json(path: Path) -> dict[str, tuple[float, float]] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log(f"Cannot parse {path}: {exc}", "WARNING")
        return None

    root = find_value(data, ["all_cases", "all cases"]) or data
    result: dict[str, tuple[float, float]] = {}
    for region in ["WT", "TC", "ET", "Mean"]:
        mean, std = mean_std(find_value(root, aliases(region)))
        if not finite(mean) and isinstance(root, dict):
            normalized = {normalize_key(key).replace(" ", "_"): value for key, value in root.items()}
            for alias in aliases(region):
                base = normalize_key(alias).replace(" ", "_")
                if not finite(mean) and finite(normalized.get(f"{base}_mean")):
                    mean = float(normalized[f"{base}_mean"])
                if not finite(std) and finite(normalized.get(f"{base}_std")):
                    std = float(normalized[f"{base}_std"])
        result[region] = (mean, std)
    return result if sum(finite(result[region][0]) for region in result) >= 3 else None


def parse_csv(path: Path) -> dict[str, tuple[float, float]] | None:
    """Read simple wide or long CSV exports without assuming a remote schema."""
    try:
        frame = pd.read_csv(path)
    except (OSError, ValueError) as exc:
        log(f"Cannot parse {path}: {exc}", "WARNING")
        return None

    normalized = {normalize_key(column).replace(" ", "_"): column for column in frame.columns}
    result: dict[str, tuple[float, float]] = {}
    region_column = next((normalized[key] for key in ("region", "metric", "label") if key in normalized), None)
    mean_column = next((normalized[key] for key in ("dice_mean", "mean", "score", "value") if key in normalized), None)
    std_column = next((normalized[key] for key in ("dice_std", "std", "stdev") if key in normalized), None)

    for region in ["WT", "TC", "ET", "Mean"]:
        mean = std = np.nan
        for alias in aliases(region):
            base = normalize_key(alias).replace(" ", "_")
            wide_mean = normalized.get(f"{base}_mean")
            wide_std = normalized.get(f"{base}_std")
            if wide_mean and len(frame):
                mean = frame.iloc[0][wide_mean]
                std = frame.iloc[0][wide_std] if wide_std else np.nan
                break
        if not finite(mean) and region_column and mean_column:
            rows = frame[frame[region_column].astype(str).str.strip().str.upper() == region.upper()]
            if not rows.empty:
                mean = rows.iloc[0][mean_column]
                std = rows.iloc[0][std_column] if std_column else np.nan
        result[region] = (float(mean) if finite(mean) else np.nan, float(std) if finite(std) else np.nan)
    return result if sum(finite(result[region][0]) for region in result) >= 3 else None


def metric_files(directories: list[Path]) -> list[Path]:
    """Return only likely metric files from explicitly configured directories."""
    found: list[Path] = []
    seen: set[Path] = set()
    names = ["wt_tc_et_summary", "summary", "metrics"]
    for directory in directories:
        if not directory.exists():
            continue
        if directory.is_file() and directory.suffix.lower() in {".json", ".csv"}:
            found.append(directory)
            continue
        for stem in names:
            for suffix in [".json", ".csv"]:
                path = directory / f"{stem}{suffix}"
                if path.exists() and path not in seen:
                    found.append(path)
                    seen.add(path)
        for child_name in ["metrics", "validation"]:
            child = directory / child_name
            if child.exists():
                for path in child.iterdir():
                    if path.suffix.lower() in {".json", ".csv"} and path not in seen:
                        found.append(path)
                        seen.add(path)
    return found


def parse_metric_file(path: Path) -> dict[str, tuple[float, float]] | None:
    if path.suffix.lower() == ".json":
        return parse_json(path)
    if path.suffix.lower() == ".csv":
        return parse_csv(path)
    return None


def load_metrics(model: str, setting: str) -> tuple[dict[str, tuple[float, float]], str, bool]:
    for path in metric_files(CANDIDATES[(model, setting)]):
        parsed = parse_metric_file(path)
        if parsed:
            log(f"{model} | {setting}: loaded {path}")
            return parsed, str(path), False
    log(f"{model} | {setting}: fallback values used because metric JSON/CSV was unavailable or unparseable.", "WARNING")
    return FALLBACK[model][setting], "FALLBACK", True


def build_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    for model in MODELS:
        for setting in SETTINGS:
            values, source, used_fallback = load_metrics(model, setting)
            for region in ["WT", "TC", "ET", "Mean"]:
                mean, std = values[region]
                rows.append({
                    "model": model,
                    "setting": setting,
                    "missing_modality": "None" if setting == "Full input" else setting.replace("Missing ", ""),
                    "metric_group": "all_cases",
                    "region": region,
                    "dice_mean": mean,
                    "dice_std": std,
                    "source_metric": source,
                    "used_fallback": used_fallback,
                })
    long = pd.DataFrame(rows)

    rows = []
    for model in MODELS:
        reference = long[(long.model == model) & (long.setting == "Full input")].set_index("region")["dice_mean"].to_dict()
        for setting in SETTINGS:
            current = long[(long.model == model) & (long.setting == setting)].set_index("region")
            row = {"Model": model, "Input Setting": setting, "Missing Modality": "None" if setting == "Full input" else setting.replace("Missing ", "")}
            for region in ["WT", "TC", "ET", "Mean"]:
                mean = current.loc[region, "dice_mean"]
                std = current.loc[region, "dice_std"]
                row[f"{region}_mean"] = mean
                row[f"{region}_std"] = std
                row[f"{region}_display"] = f"{mean:.4f} ± {std:.4f}" if finite(std) else f"{mean:.4f}"
                row[f"{region}_drop_from_model_full"] = 0.0 if setting == "Full input" else reference[region] - mean
            rows.append(row)
    wide = pd.DataFrame(rows)

    full = wide[wide.Model == "Full-only"].set_index("Input Setting")
    moddrop = wide[wide.Model == "Modality Dropout"].set_index("Input Setting")
    absolute_rows = []
    drop_rows = []
    recovery_rows = []
    for setting in SETTINGS:
        row = {"Input Setting": setting}
        for region in ["WT", "TC", "ET", "Mean"]:
            row[f"Full-only {region}"] = full.loc[setting, f"{region}_mean"]
            row[f"ModDrop {region}"] = moddrop.loc[setting, f"{region}_mean"]
            row[f"ModDrop - Full-only {region}"] = moddrop.loc[setting, f"{region}_mean"] - full.loc[setting, f"{region}_mean"]
        absolute_rows.append(row)
    for setting in MISSING:
        drop_row = {"Missing Modality": setting.replace("Missing ", "")}
        recovery_row = {"Missing Modality": setting.replace("Missing ", "")}
        for region in ["WT", "TC", "ET", "Mean"]:
            full_drop = full.loc[setting, f"{region}_drop_from_model_full"]
            moddrop_drop = moddrop.loc[setting, f"{region}_drop_from_model_full"]
            drop_row[f"Full-only {region} Drop"] = full_drop
            drop_row[f"ModDrop {region} Drop"] = moddrop_drop
            drop_row[f"Drop Reduction {region}"] = full_drop - moddrop_drop
            recovery_row[f"{region} Recovery Gain"] = moddrop.loc[setting, f"{region}_mean"] - full.loc[setting, f"{region}_mean"]
        drop_rows.append(drop_row)
        recovery_rows.append(recovery_row)
    return long, wide, pd.DataFrame(absolute_rows), pd.DataFrame(drop_rows), pd.DataFrame(recovery_rows)


def annotate(ax: Any, bars: Any) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.3f}", (bar.get_x() + bar.get_width() / 2, height), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=7)


def plot_absolute(wide: pd.DataFrame) -> Path:
    full = wide[wide.Model == "Full-only"].set_index("Input Setting")
    moddrop = wide[wide.Model == "Modality Dropout"].set_index("Input Setting")
    x = np.arange(len(SETTINGS))
    width = 0.36
    figure, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for axis, region in zip(axes.flat, ["WT", "TC", "ET", "Mean"]):
        full_values = [full.loc[setting, f"{region}_mean"] for setting in SETTINGS]
        moddrop_values = [moddrop.loc[setting, f"{region}_mean"] for setting in SETTINGS]
        full_error = None if region == "Mean" else [full.loc[setting, f"{region}_std"] for setting in SETTINGS]
        moddrop_error = None if region == "Mean" else [moddrop.loc[setting, f"{region}_std"] for setting in SETTINGS]
        full_bars = axis.bar(x - width / 2, full_values, width, label="Full-only", yerr=full_error, capsize=2)
        moddrop_bars = axis.bar(x + width / 2, moddrop_values, width, label="Modality Dropout", yerr=moddrop_error, capsize=2)
        annotate(axis, full_bars)
        annotate(axis, moddrop_bars)
        axis.set_title(f"{region} Dice")
        axis.set_ylim(0, 1.05)
        axis.set_ylabel("Dice")
        axis.set_xticks(x, SETTINGS, rotation=20, ha="right")
        axis.grid(axis="y", alpha=0.25)
        if region == "WT":
            axis.legend(loc="lower left")
    figure.suptitle("Absolute Dice Comparison", y=1.02)
    figure.tight_layout()
    path = OUTPUT_DIR / "absolute_dice_fullonly_vs_moddrop.png"
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_drop(drop: pd.DataFrame) -> Path:
    x = np.arange(len(MISSING))
    width = 0.36
    figure, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for axis, region in zip(axes.flat, ["WT", "TC", "ET", "Mean"]):
        full_values = drop[f"Full-only {region} Drop"]
        moddrop_values = drop[f"ModDrop {region} Drop"]
        full_bars = axis.bar(x - width / 2, full_values, width, label="Full-only")
        moddrop_bars = axis.bar(x + width / 2, moddrop_values, width, label="Modality Dropout")
        annotate(axis, full_bars)
        annotate(axis, moddrop_bars)
        axis.set_title(f"{region} Dice Drop")
        axis.set_ylabel("Dice Drop from Complete-Modality Input")
        axis.set_xticks(x, [setting.replace("Missing ", "") for setting in MISSING], rotation=20, ha="right")
        axis.grid(axis="y", alpha=0.25)
        if region == "WT":
            axis.legend()
    figure.suptitle("Robustness Dice Drop Comparison", y=1.02)
    figure.tight_layout()
    path = OUTPUT_DIR / "dice_drop_fullonly_vs_moddrop.png"
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def heat(matrix: np.ndarray, rows: list[str], title: str, path: Path, vmin: float, vmax: float, label: str) -> Path:
    figure, axis = plt.subplots(figsize=(7, 4.6))
    image = axis.imshow(matrix, aspect="auto", vmin=vmin, vmax=vmax)
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label(label)
    axis.set_xticks(np.arange(3), REGIONS)
    axis.set_yticks(np.arange(len(rows)), rows)
    axis.set_xlabel("Tumor Region")
    axis.set_ylabel("Missing Modality")
    axis.set_title(title)
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(column_index, row_index, f"{matrix[row_index, column_index]:.4f}", ha="center", va="center", fontsize=9)
    figure.tight_layout()
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_heatmaps(drop: pd.DataFrame, recovery: pd.DataFrame) -> list[Path]:
    rows = drop["Missing Modality"].tolist()
    full_matrix = drop[[f"Full-only {region} Drop" for region in REGIONS]].to_numpy(float)
    moddrop_matrix = drop[[f"ModDrop {region} Drop" for region in REGIONS]].to_numpy(float)
    maximum = max(float(np.nanmax(full_matrix)), float(np.nanmax(moddrop_matrix)), 0.01)
    full_path = heat(full_matrix, rows, "Modality-Region Risk Matrix: Full-only Model", OUTPUT_DIR / "modality_region_risk_heatmap_fullonly.png", 0, maximum, "Dice Drop")
    moddrop_path = heat(moddrop_matrix, rows, "Modality-Region Risk Matrix: Modality Dropout Model", OUTPUT_DIR / "modality_region_risk_heatmap_moddrop.png", 0, maximum, "Dice Drop")
    recovery_matrix = recovery[[f"{region} Recovery Gain" for region in REGIONS]].to_numpy(float)
    limit = max(abs(float(recovery_matrix.min())), abs(float(recovery_matrix.max())), 0.01)
    recovery_path = heat(recovery_matrix, rows, "Recovery Gain of Modality Dropout over Full-only", OUTPUT_DIR / "modality_dropout_recovery_heatmap.png", -limit, limit, "Recovery Gain")
    return [full_path, moddrop_path, recovery_path]


def plot_mean(wide: pd.DataFrame) -> Path:
    full = wide[wide.Model == "Full-only"].set_index("Input Setting")
    moddrop = wide[wide.Model == "Modality Dropout"].set_index("Input Setting")
    x = np.arange(len(SETTINGS))
    width = 0.36
    figure, axis = plt.subplots(figsize=(9, 5))
    full_bars = axis.bar(x - width / 2, [full.loc[s, "Mean_mean"] for s in SETTINGS], width, label="Full-only")
    moddrop_bars = axis.bar(x + width / 2, [moddrop.loc[s, "Mean_mean"] for s in SETTINGS], width, label="Modality Dropout")
    annotate(axis, full_bars)
    annotate(axis, moddrop_bars)
    axis.set_xticks(x, SETTINGS, rotation=20, ha="right")
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("Mean Dice")
    axis.set_title("Mean Dice Across Input Conditions")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    path = OUTPUT_DIR / "mean_dice_comparison.png"
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_recovery_table(recovery: pd.DataFrame) -> Path:
    figure, axis = plt.subplots(figsize=(8.8, 2.5))
    axis.axis("off")
    display = recovery.copy()
    for column in display.columns[1:]:
        display[column] = display[column].map(lambda value: f"{value:+.4f}")
    table = axis.table(cellText=display.values, colLabels=display.columns, cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.6)
    axis.set_title("Recovery Gain of Modality Dropout over Full-only", pad=12)
    figure.tight_layout()
    path = OUTPUT_DIR / "modality_dropout_recovery_table.png"
    figure.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def protocol() -> pd.DataFrame:
    rows = []
    for model in MODELS:
        for setting in SETTINGS:
            rows.append({
                "Model": model,
                "Trainer": "nnUNetTrainer" if model == "Full-only" else "nnUNetTrainerModalityDropout",
                "Training Input Policy": "Complete 4-modality input only" if model == "Full-only" else "50% complete; 50% one randomly zero-filled modality",
                "Inference Input": setting,
                "Missing Modality": "None" if setting == "Full input" else setting.replace("Missing ", ""),
                "Fold": 0,
                "Checkpoint": "checkpoint_best.pth",
                "Validation Cases": 251,
                "Evaluation Regions": "WT / TC / ET",
                "Notes": "single-fold preliminary benchmark; zero-filled missing-modality direct-inference protocol",
            })
    return pd.DataFrame(rows)


def export_excel(long: pd.DataFrame, wide: pd.DataFrame, absolute: pd.DataFrame, drop: pd.DataFrame, recovery: pd.DataFrame) -> Path:
    path = OUTPUT_DIR / "all_results_summary.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        absolute.round(4).to_excel(writer, sheet_name="Absolute_Dice", index=False)
        drop.round(4).to_excel(writer, sheet_name="Dice_Drop", index=False)
        recovery.round(4).to_excel(writer, sheet_name="Recovery_Gain", index=False)
        protocol().to_excel(writer, sheet_name="Protocol", index=False)
        long.round(4).to_excel(writer, sheet_name="Raw_Long_Format", index=False)
        wide.round(4).to_excel(writer, sheet_name="Wide_All_Results", index=False)
        pd.DataFrame({"Log": LOG}).to_excel(writer, sheet_name="Validation_Log", index=False)
    if HAVE_OPENPYXL:
        workbook = load_workbook(path)
        header_fill = PatternFill("solid", fgColor="D9EAF7")
        for sheet in workbook.worksheets:
            sheet.freeze_panes = "A2"
            for cell in sheet[1]:
                cell.font = Font(bold=True)
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            for index, column in enumerate(sheet.columns, 1):
                width = max(len(str(cell.value or "")) for cell in column) + 2
                sheet.column_dimensions[get_column_letter(index)].width = min(max(width, 12), 42)
            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    if isinstance(cell.value, (float, np.floating)):
                        cell.number_format = "0.0000"
        for name in ["Dice_Drop", "Recovery_Gain"]:
            sheet = workbook[name]
            sheet.conditional_formatting.add(
                f"B2:{get_column_letter(sheet.max_column)}{sheet.max_row}",
                ColorScaleRule(start_type="min", start_color="FFFFFF", mid_type="percentile", mid_value=50, mid_color="FFF2CC", end_type="max", end_color="F4CCCC"),
            )
        workbook.save(path)
    return path


def write_readme(absolute: pd.DataFrame, drop: pd.DataFrame, recovery: pd.DataFrame) -> Path:
    fallback_lines = "\n".join(f"- {line}" for line in LOG if "fallback values used" in line) or "- No fallback metrics were required."
    content = f"""# BraTS Missing-Modality Paper Assets

## Reproduction

```bash
python scripts/generate_moddrop_paper_assets.py --output-dir results/paper_assets_moddrop
```

To read the original experiment metrics, provide their actual paths with
`--project-root` and `--benchmark-root`. The repository does not assume or
embed an AutoDL path.

## Data provenance

The script searches explicitly configured metric JSON and CSV files first.
Fallback values are used only when a source metric file is unavailable or
unparseable. The current checked-in assets therefore remain reproducible, but
their fallback provenance must be replaced by source-file provenance before a
final paper claim.

{fallback_lines}

## Scope

The current values describe a fold 0 single-fold preliminary benchmark under
the zero-filled missing-modality direct-inference stress test. Modality
Dropout is a strong baseline, not the final proposed method. These assets do
not establish statistical significance or clinical validation.

## Main Tables

### Absolute Dice
{absolute.to_markdown(index=False, floatfmt=".4f")}

### Robustness Dice Drop
{drop.to_markdown(index=False, floatfmt=".4f")}

### Recovery Gain
{recovery.to_markdown(index=False, floatfmt=".4f")}
"""
    path = OUTPUT_DIR / "README_paper_assets.md"
    path.write_text(content, encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    configure_paths(args)
    LOG.clear()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Started {datetime.now().isoformat(timespec='seconds')}")
    log(f"Project root: {PROJECT_ROOT}")
    log(f"Benchmark root: {BENCHMARK_ROOT}")
    log(f"Output directory: {OUTPUT_DIR}")

    long, wide, absolute, drop, recovery = build_frames()
    long_path = OUTPUT_DIR / "all_results_long.csv"
    wide_path = OUTPUT_DIR / "all_results_wide.csv"
    long.round(4).to_csv(long_path, index=False)
    wide.round(4).to_csv(wide_path, index=False)
    log(f"Saved {long_path}")
    log(f"Saved {wide_path}")

    excel_path = export_excel(long, wide, absolute, drop, recovery)
    log(f"Saved {excel_path}")
    figure_paths = [plot_absolute(wide), plot_drop(drop), *plot_heatmaps(drop, recovery), plot_mean(wide), plot_recovery_table(recovery)]
    for path in figure_paths:
        log(f"Saved figure {path}")
    readme_path = write_readme(absolute, drop, recovery)
    log(f"Saved {readme_path}")

    validation_path = OUTPUT_DIR / "validation_log.txt"
    outputs = [long_path, wide_path, excel_path, *figure_paths, readme_path]
    for path in outputs:
        if not path.exists() or path.stat().st_size == 0:
            log(f"Missing or empty output {path}", "WARNING")
    if args.fail_on_fallback and long["used_fallback"].any():
        log("Fallback values were required; source metrics must be supplied.", "ERROR")
        validation_path.write_text("\n".join(LOG) + "\n", encoding="utf-8")
        raise SystemExit(2)
    validation_path.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print("\nGenerated files:")
    for path in sorted(OUTPUT_DIR.iterdir()):
        print(path.resolve())


if __name__ == "__main__":
    main()
