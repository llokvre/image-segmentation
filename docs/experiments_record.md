# BraTS 2023 实验记录

本文档记录当前可用于论文工程归档的基线结果。所有数值均来自当前研究记录中人工确认的 fold 0 benchmark；原始预测、标签和 checkpoint 不在本仓库中。

## 统一实验条件

- Dataset: BraTS 2023 GLI。
- Configuration: nnU-Net v2 `3d_fullres`。
- Fold: 0。
- Validation cases: 251。
- Checkpoint: `checkpoint_best.pth`，仅记录名称，不上传文件。
- Input order: `_0000` T1n, `_0001` T1c, `_0002` T2w, `_0003` FLAIR/T2f。
- Regions: WT = 1+2+3, TC = 1+3, ET = 3。
- Missing-modality protocol: one input channel is zero-filled while the network still receives four channels。

## Experiment A: Full-only nnU-Net

训练阶段只使用完整四模态输入。完整输入结果作为 Full-only reference；缺失模态结果是同一模型的直接推理压力测试。

| Input | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full input | 0.9326 +/- 0.0839 | 0.9106 +/- 0.1645 | 0.8669 +/- 0.1943 | 0.9034 |
| Missing T1c | 0.9019 +/- 0.1116 | 0.2648 +/- 0.2955 | 0.0599 +/- 0.1643 | 0.4089 |
| Missing FLAIR | 0.7070 +/- 0.2335 | 0.8625 +/- 0.2317 | 0.8308 +/- 0.2296 | 0.8001 |
| Missing T2w | 0.8334 +/- 0.2183 | 0.8578 +/- 0.2462 | 0.8391 +/- 0.2106 | 0.8434 |
| Missing T1n | 0.9287 +/- 0.0613 | 0.9057 +/- 0.1547 | 0.8585 +/- 0.1837 | 0.8976 |

### Interpretation

Full-only 呈现明显的模态—区域特异性退化：Missing T1c 对 TC/ET 最严重，Missing FLAIR 对 WT 最明显，Missing T1n 的影响最小。这里的“最严重/最明显”只描述当前 fold 0 结果，不表示统计检验结论。

## Experiment B: Modality Dropout nnU-Net

Trainer: `nnUNetTrainerModalityDropout`。

- 50% 概率保留完整四模态；
- 50% 概率随机选择一个模态置零；
- 每次最多缺失一个模态；
- 验证和推理阶段不执行随机 dropout。

| Input | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full input | 0.9360 +/- 0.0835 | 0.9133 +/- 0.1558 | 0.8723 +/- 0.1833 | 0.9072 |
| Missing T1c | 0.9272 +/- 0.0887 | 0.8095 +/- 0.1782 | 0.6540 +/- 0.2179 | 0.7969 |
| Missing FLAIR | 0.9016 +/- 0.1027 | 0.9024 +/- 0.1763 | 0.8626 +/- 0.1956 | 0.8889 |
| Missing T2w | 0.9290 +/- 0.0855 | 0.9049 +/- 0.1689 | 0.8619 +/- 0.1967 | 0.8986 |
| Missing T1n | 0.9338 +/- 0.0839 | 0.9059 +/- 0.1657 | 0.8660 +/- 0.1868 | 0.9019 |

### Interpretation

Modality Dropout 在四种单模态缺失压力测试中均降低了 Full-only 的性能下降；完整输入下没有观察到明显代价。Missing T1c 下 ET 的 0.6540 仍明显低于 Modality Dropout 的完整输入 ET 0.8723，因此该 baseline 不能完全消除风险。

## 需要继续核对的数值

旧版实验记录曾保存另一组 Full-only 完整输入数值（0.9358 / 0.9130 / 0.8770）。本文件以当前资产脚本和用户确认的 benchmark 数值 0.9326 / 0.9106 / 0.8669 为 canonical comparison，但旧记录不应被静默视为同一实验结果。后续必须从真实 JSON/CSV 和病例清单核对两组数值的来源、checkpoint 或评估脚本差异。

## 结论边界

这些结果属于 single-fold preliminary benchmark。不能据此宣称最终临床性能、SOTA、统计显著或临床验证。Modality Dropout 是 strong baseline；风险感知伪标签与训练方法仍处于设计阶段。
