# 论文草稿提纲（工作版）

> 文档性质：研究记录 + 论文草稿，不是最终定稿。当前证据来自 fold 0 的 single-fold preliminary benchmark。

## 暂定题目

**面向缺失模态脑肿瘤分割的模态—区域风险分析与鲁棒训练：一项 BraTS 2023 GLI 初步研究**

## 核心叙事

1. 多模态 MRI 缺失会导致分割性能下降，但下降不是在所有模态和肿瘤区域上均匀发生。
2. Full-only nnU-Net 的 zero-filled direct-inference stress test 显示了清晰的模态—区域退化模式。
3. Modality Dropout 作为 strong baseline 能够明显缓解单模态缺失，但在 Missing T1c × ET/TC 上仍有残余风险。
4. 该残余风险为下一阶段的 modality-region risk-aware pseudo-labeling 和 risk-calibrated missing-modality training 提供动机。

## 文章结构与证据

| 部分 | 主要内容 | 当前证据状态 |
|---|---|---|
| Introduction | 临床/工程动机，缺失模态问题，本文范围 | 初稿 |
| Related work | 缺失模态分割、模态 dropout、不确定性和教师—学生方法 | 需补真实文献 |
| Method | Full-only 和 Modality Dropout 基线；下一阶段方法设计 | 基线已完成，方法未完成 |
| Experiments | 数据、fold、输入协议、指标和比较方式 | 已有 fold 0 记录 |
| Results | WT/TC/ET Dice、drop 和 recovery gain | 已有初步结果 |
| Discussion | 模态—区域风险解释、baseline 边界、后续方法动机 | 初稿 |
| Limitations | 单折、zero-fill、fallback、无临床验证 | 已知限制 |
| Next steps | 数据源核对、多折、定性和风险感知训练 | 计划 |

## 需要保护的主要表述

- 使用“observed in the current fold-0 benchmark”“preliminary evidence”等措辞。
- 不写 SOTA、statistically significant、clinically validated。
- Modality Dropout 写作 strong baseline，不写成最终创新。
- 下一阶段方法用 planned/proposed design，不能写成已完成实验。

## 关键图表计划

- 图 1：Full-only 与 Modality Dropout 在五种输入条件下的 WT/TC/ET/Mean Dice。
- 图 2：Full-only 模态—区域 Dice drop heatmap。
- 图 3：Modality Dropout 的风险矩阵和 recovery gain。
- 表 1：实验协议和模型配置。
- 表 2：当前结果及均值下降。
- 表 3：计划中的风险感知方法消融。

## 当前版本的结论出口

结论只能到达“当前压力测试支持存在模态—区域特异性风险，并说明 Modality Dropout 具有鲁棒性基线价值”。能否推广到多折、其他缺失机制或临床流程，需要后续实验。
