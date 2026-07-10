# Modality Dropout 基线

## 目的

验证训练阶段显式模拟单模态缺失，是否能降低推理时固定缺失模态造成的性能退化。

## Trainer 和规则

Trainer: `nnUNetTrainerModalityDropout`。

每个训练样本独立执行：

- 50% 概率保留完整四模态；
- 50% 概率随机选择一个模态并将完整通道置零；
- 每个样本最多置零一个模态；
- 验证和推理阶段不执行随机 dropout。

逻辑测试曾使用 `(8, 4, 8, 8, 8)` 全 1 张量在 `p=1.0` 下验证：每个样本恰好置零一个通道，通道 0/1/2/3 均有覆盖，原始输入张量未被修改。

## 模型和评估

- nnU-Net v2 `3d_fullres`。
- Fold 0。
- 训练记录为 1000 epochs。
- Validation: 251 cases。
- Checkpoint: `checkpoint_best.pth`。
- Inference conditions: Full、Missing T1c、Missing FLAIR、Missing T2w、Missing T1n。

## 结果

| Input | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full input | 0.9360 +/- 0.0835 | 0.9133 +/- 0.1558 | 0.8723 +/- 0.1833 | 0.9072 |
| Missing T1c | 0.9272 +/- 0.0887 | 0.8095 +/- 0.1782 | 0.6540 +/- 0.2179 | 0.7969 |
| Missing FLAIR | 0.9016 +/- 0.1027 | 0.9024 +/- 0.1763 | 0.8626 +/- 0.1956 | 0.8889 |
| Missing T2w | 0.9290 +/- 0.0855 | 0.9049 +/- 0.1689 | 0.8619 +/- 0.1967 | 0.8986 |
| Missing T1n | 0.9338 +/- 0.0839 | 0.9059 +/- 0.1657 | 0.8660 +/- 0.1868 | 0.9019 |

## 主要结论

Modality Dropout 对四种单模态缺失均有恢复作用，且完整输入下没有观察到明显性能代价。Missing T1c 下 ET 仍从完整输入的 0.8723 降到 0.6540，表明该方法是 strong baseline，但不能完全消除 high-risk modality-region pair 的不确定性。

## 解释边界

“提升”是当前单折均值的差异，不等同于统计显著提升。该 baseline 不是下一阶段方法本身；后续 risk-aware pseudo-labeling 和 risk-calibrated training 尚未实现。
