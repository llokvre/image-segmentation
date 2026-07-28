# 当前下一步

> 最后更新：2026-07-10
> 当前阶段：完成基线结果归档，准备进入风险感知方法设计。

## 已完成

- Full-only nnU-Net：Full + Missing T1c / FLAIR / T2w / T1n。
- Modality Dropout nnU-Net：Full + Missing T1c / FLAIR / T2w / T1n。
- 生成 CSV、XLSX、PNG 和结果说明。
- 已建立论文草稿、实验记录、方法设计和 TODO 文档结构。

## 当前优先事项

1. 人工复核 PNG 在论文目标尺寸下的字体、误差线和标签可读性。
2. 获取并核对真实 metric JSON/CSV，消除 fallback 状态。
3. 统一历史实验记录中的 Full-only 基线数值，避免旧记录与当前资产混用。
4. 为典型病例建立 GT、预测和错误区域的定性可视化。
5. 设计 modality-region risk-aware pseudo-labeling 的最小可行实验。

## 路径约定

当前仓库只保存本地资产。脚本不再依赖写死的 AutoDL 路径；真实实验目录应在运行时通过 `--project-root`、`--benchmark-root` 或对应环境变量显式提供。
