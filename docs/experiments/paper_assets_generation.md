# 论文资产生成记录

## 脚本

主脚本为 `scripts/generate_moddrop_paper_assets.py`。结果目录只保存生成的 CSV、XLSX、PNG、README 和日志；脚本副本不再放在结果目录中。

## 运行方式

```bash
python scripts/generate_moddrop_paper_assets.py \
  --output-dir results/paper_assets_moddrop
```

当真实实验目录可访问时，显式传入路径：

```bash
python scripts/generate_moddrop_paper_assets.py \
  --project-root /path/to/nnunet_project \
  --benchmark-root /path/to/missing_modality_benchmark \
  --output-dir results/paper_assets_moddrop
```

也可以使用 `BRATS_PROJECT_ROOT`、`BRATS_BENCHMARK_ROOT` 和 `PAPER_ASSET_OUTPUT_DIR` 环境变量。路径由运行者提供，仓库不内置 AutoDL 服务器路径。

## 读取逻辑

脚本按候选目录查找 `wt_tc_et_summary.json`、`summary.json`、`metrics.json` 及对应 CSV，并支持常见的嵌套 JSON、宽表 CSV 和长表 CSV 结构。真实目录的命名如果不同，应先在脚本的 `configure_paths` / `metric_files` 中增加经过确认的候选规则，再记录 schema。

## fallback 用途

如果候选 metric 文件不存在、无法解析或字段不足，脚本使用 `FALLBACK` 中的人工确认值，生成结果并在 `validation_log.txt` 和 README 中标记 `used_fallback=True`。fallback 的用途是保持当前研究记录和图表可复现，不是替代真实实验文件。

## 输出安全性

脚本只写入 `OUTPUT_DIR`：

- `all_results_long.csv`
- `all_results_wide.csv`
- `all_results_summary.xlsx`
- 7 个 PNG 资产
- `README_paper_assets.md`
- `validation_log.txt`

它不会打开写入原始 NIfTI、预测、标签、nnU-Net 目录或 checkpoint。建议在真实环境运行前使用 `--output-dir` 指向独立的结果目录，并检查 Git diff。

## 当前 validation_log 状态

旧版日志中十组模型—输入组合全部显示 fallback，原因是脚本写死的 AutoDL 路径在本地仓库不可用。现在脚本已去掉硬编码；要让日志显示真实来源，仍需要运行者提供实际 JSON/CSV 路径并核对解析结果。
