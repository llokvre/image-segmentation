# 4. 实验设计草稿

## 4.1 数据与划分

实验使用 BraTS 2023 GLI。当前可复核结果来自 fold 0：训练记录为 1000 cases，验证为 251 cases。数据本身不包含在 GitHub 仓库中。最终版本需要补充准确的数据许可、预处理版本和病例清单来源。

## 4.2 模型与训练

| 模型 | Trainer | 训练输入策略 | 推理输入 |
|---|---|---|---|
| Full-only | nnUNetTrainer | 只用完整四模态 | Full 或单模态 zero-fill |
| Modality Dropout | nnUNetTrainerModalityDropout | 50% full，50% 随机缺失一个模态 | Full 或单模态 zero-fill |

两者均使用 nnU-Net v2 `3d_fullres`、fold 0 和 `checkpoint_best.pth`。推理时不进行随机 dropout。

## 4.3 缺失模态协议

对每个验证病例保留四通道输入形状，并分别将 T1c、FLAIR、T2w 或 T1n 通道置零。该协议称为 **zero-filled missing-modality direct-inference stress test**。它用于控制变量比较，并不等同于所有真实临床缺失机制。

## 4.4 指标

当前报告 WT、TC 和 ET Dice 的均值与标准差，并计算每个模型相对其完整输入的 Dice drop。Mean Dice 为 WT/TC/ET 均值的算术平均。后续计划加入 HD95、病例级分布、置信区间和校准分析。

## 4.5 当前比较

主要比较包括：

1. Full-only 在完整输入与四种缺失输入之间的差异；
2. Modality Dropout 在完整输入与四种缺失输入之间的差异；
3. 同一缺失条件下 Modality Dropout 相对 Full-only 的恢复幅度；
4. 模态—区域 risk matrix 的结构。

## 4.6 计划中的方法实验

待实现方法将至少包含：Full-only、Modality Dropout、risk-aware pseudo-labeling、去掉风险矩阵、去掉不确定性过滤、统一阈值和区域自适应阈值等消融。所有新实验需要先固定数据划分、随机种子、checkpoint 选择和评估脚本。

## 4.7 可复现性要求

- 记录实际 metric JSON/CSV 路径和文件哈希。
- 记录训练命令、环境版本、随机种子和 checkpoint。
- 输出不覆盖原始数据、预测和模型。
- 资产生成脚本只写入指定输出目录。
- fallback 数值必须在结果中显式标记，不能与真实源文件结果混写。
