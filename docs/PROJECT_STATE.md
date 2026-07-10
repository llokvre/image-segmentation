# BraTS 2023 缺失模态脑肿瘤分割项目状态

> 最后更新：2026-07-10
> 当前阶段：Full-only 与 Modality Dropout 的 fold 0 初步基线已完成；下一阶段进入模态—区域风险感知方法设计。

## 当前研究路线

1. 完整模态 nnU-Net 基线；
2. zero-filled missing-modality direct-inference 压力测试；
3. Modality Dropout 强鲁棒性基线；
4. 模态—区域风险矩阵与不确定性分析；
5. 风险校准伪标签和缺失模态感知训练；
6. 多折验证、消融实验和定性可视化。

## 当前证据

- 数据集：BraTS 2023 GLI；数据不随仓库分发。
- 配置：nnU-Net v2 `3d_fullres`，fold 0。
- 验证病例：251。
- Full-only：训练时只使用完整四模态。
- Modality Dropout：50% 保留完整输入，50% 随机置零一个模态；验证和推理不随机 dropout。
- 评估：Full、Missing T1c、Missing FLAIR、Missing T2w、Missing T1n。
- 当前结果：single-fold preliminary benchmark，不宣称 SOTA、统计显著或临床验证。

## 当前核心判断

Full-only 模型的退化与缺失模态和分割区域共同相关。Missing T1c 对 TC/ET 尤其不利，Missing FLAIR 对 WT 更不利；Modality Dropout 在当前四种压力测试中明显缓解退化，但 Missing T1c 下 ET 仍有残余下降。

## 数据来源状态

论文资产脚本会优先读取显式配置的 metric JSON；当前仓库没有原始实验 JSON/CSV 路径，因此现有表格使用人工确认的 fallback 数值。后续应在真实实验目录可用时通过 `--project-root` 和 `--benchmark-root` 传入路径，重新生成资产并保存来源日志。

## 不应混淆的范围

- 本仓库不是 BraTS 数据分发仓库。
- 当前结果不是最终临床性能。
- Modality Dropout 是 strong baseline，不是最终创新方法。
- 下一阶段的 risk-aware pseudo-labeling / risk-calibrated training 目前只是设计，不应写成已完成实验。
