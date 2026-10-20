# BraTS 2023 实验记录

## Experiment A0: Full-Modality nnU-Net Baseline

- Dataset: BraTS 2023 GLI
- Model: nnU-Net v2
- Configuration: 3d_fullres
- Input modalities: T1n + T1c + T2w + FLAIR
- Training fold: Fold 0
- Training epochs: 1000
- Training cases: 1000
- Validation cases: 251

### Validation Metrics

| Metric | Result |
|---|---:|
| WT Dice | 0.9358 ± 0.0832 |
| TC Dice | 0.9130 ± 0.1594 |
| ET Dice | 0.8770 ± 0.1777 |
| Mean WT/TC/ET Dice | 0.9086 |

### Notes

- Training completed successfully.
- No missing validation labels.
- No prediction/ground-truth shape mismatches.
- This experiment is the full-modality reference baseline for all later missing-modality experiments.

---

## Experiment B1: Missing T1c Direct Inference

### Protocol
- Model: nnU-Net v2, 3d_fullres, fold 0
- Checkpoint: checkpoint_best.pth
- Validation cases: 251
- Input: T1n + T2w + FLAIR were retained; T1c (_0001) was replaced with an all-zero NIfTI image.
- Evaluation: WT / TC / ET Dice on the same fold 0 validation cases.

### Results

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-Best | 0.9326 | 0.9106 | 0.8669 | 0.9034 |
| Missing T1c | 0.9019 | 0.2648 | 0.0599 | 0.4089 |
| Dice Drop | 0.0307 | 0.6458 | 0.8070 | 0.4945 |

### Preliminary Interpretation
T1c removal caused only a modest reduction in whole-tumor segmentation, but resulted in severe degradation in tumor-core and enhancing-tumor segmentation. This provides preliminary evidence of modality-region-specific risk: T1c is critically associated with reliable TC and ET prediction under the present zero-filled missing-modality inference protocol.

---

## Experiment B2: Missing FLAIR Direct Inference

### Protocol
- Model: nnU-Net v2, 3d_fullres, fold 0
- Checkpoint: checkpoint_best.pth
- Validation cases: 251
- Input: T1n, T1c, and T2w were retained; FLAIR (_0003) was replaced with an all-zero NIfTI image.
- Evaluation: WT / TC / ET Dice on the same fold 0 validation cases.

### Results

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-Best | 0.9326 | 0.9106 | 0.8669 | 0.9034 |
| Missing FLAIR | 0.7070 | 0.8625 | 0.8308 | 0.8001 |
| Dice Drop | 0.2256 | 0.0481 | 0.0361 | 0.1033 |

### Preliminary Interpretation
Zero-filled FLAIR absence primarily degraded whole-tumor segmentation, while tumor-core and enhancing-tumor segmentation remained relatively stable. Together with the Missing T1c experiment, this result supports the hypothesis that missing MRI modalities induce modality-region-specific segmentation risk.

---

## Experiment B3: Missing T2w Direct Inference

### Protocol
- Model: nnU-Net v2, 3d_fullres, fold 0
- Checkpoint: checkpoint_best.pth
- Validation cases: 251
- Input: T1n, T1c, and FLAIR were retained; T2w (_0002) was replaced with an all-zero NIfTI image.
- Evaluation: WT / TC / ET Dice on the same fold 0 validation cases.

### Results

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-Best | 0.9326 | 0.9106 | 0.8669 | 0.9034 |
| Missing T2w | 0.8334 | 0.8578 | 0.8391 | 0.8434 |
| Dice Drop | 0.0992 | 0.0528 | 0.0278 | 0.0600 |

### Preliminary Interpretation
Zero-filled T2w absence produced a moderate degradation, primarily affecting WT segmentation. The impact on TC and ET was comparatively limited relative to missing T1c. This result further supports modality-region-specific performance degradation under missing-modality direct inference.

---

## Experiment B4: Missing T1n Direct Inference

### Protocol
- Model: nnU-Net v2, 3d_fullres, fold 0
- Checkpoint: checkpoint_best.pth
- Validation cases: 251
- Input: T1c, T2w, and FLAIR were retained; T1n (_0000) was replaced with an all-zero NIfTI image.
- Evaluation: WT / TC / ET Dice on the same fold 0 validation cases.

### Results

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-Best | 0.9326 | 0.9106 | 0.8669 | 0.9034 |
| Missing T1n | 0.9287 | 0.9057 | 0.8585 | 0.8976 |
| Dice Drop | 0.0039 | 0.0049 | 0.0084 | 0.0058 |

### Preliminary Interpretation
Zero-filled T1n absence caused negligible degradation across WT, TC, and ET. Under the current fold 0 direct-inference protocol, T1n appears substantially less critical than T1c and FLAIR for tumor-region segmentation.

---

# 实验 C：nnU-Net + Modality Dropout Baseline

## 当前状态

- Trainer 已创建并完成独立逻辑测试；
- 尚未开始正式训练。

## Trainer 名称

`nnUNetTrainerModalityDropout`

## Modality Dropout 规则

训练阶段中，每个样本独立执行：

- 50% 概率：保留完整四模态输入；
- 50% 概率：随机选择一个输入模态并将该完整通道置零；
- 每次最多只缺失一个模态。

通道顺序：

| 通道 | 模态 |
|---|---|
| 0 | T1n |
| 1 | T1c |
| 2 | T2w |
| 3 | FLAIR |

## 验证与推理

- 验证阶段：不执行随机 Modality Dropout；
- 推理阶段：不执行随机 Modality Dropout；
- 后续仍使用 Full、Missing T1c、Missing FLAIR、Missing T2w、Missing T1n 五种固定输入协议进行评估。

## 逻辑测试结果

使用形状为 `(8, 4, 8, 8, 8)` 的全 1 测试张量，在 `p=1.0` 条件下：

- 8 个样本均恰好置零一个通道；
- 被置零通道覆盖 0、1、2、3；
- 原始输入张量未被修改。


---

# 实验 C1：Modality Dropout 模型的完整模态输入评估

## 模型

- Trainer：`nnUNetTrainerModalityDropout`
- Fold：0
- 训练规则：
  - 50% 概率保留完整四模态；
  - 50% 概率随机置零一个模态；
- 训练完成：1000 epochs；
- 验证病例数：251；
- 评估预测：nnU-Net fold 0 validation 输出。

## 结果

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-only Full-Best | 0.9326 | 0.9106 | 0.8669 | 0.9034 |
| ModDrop Full-Best | 0.9360 | 0.9133 | 0.8723 | 0.9072 |
| Full-only − ModDrop | -0.0034 | -0.0027 | -0.0054 | -0.0038 |

## 初步结论

在当前 fold 0 的完整模态评估下，Modality Dropout 未观察到明显性能下降；相对于 Full-only baseline，WT、TC、ET 和 Mean Dice 均略高。

该结论属于单折初步结果，不代表统计显著提升，后续需要在多折验证中确认。


---

# 实验 C2：Modality Dropout 模型在 Missing T1c 下的评估

## 推理设置

- 模型：`nnUNetTrainerModalityDropout`
- Fold：0
- Checkpoint：`checkpoint_best.pth`
- 输入：T1n、T2w、FLAIR 保留；T1c（`_0001`）置零
- 验证病例数：251
- 评估区域：WT、TC、ET

## 主结果

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-only + Missing T1c | 0.9019 | 0.2648 | 0.0599 | 0.4089 |
| ModDrop + Missing T1c | 0.9272 | 0.8095 | 0.6540 | 0.7969 |
| ModDrop 相对 Full-only 提升 | +0.0253 | +0.5447 | +0.5941 | +0.3880 |

## ModDrop 自身完整输入与 Missing T1c 的对比

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| ModDrop + Full Input | 0.9360 | 0.9133 | 0.8723 | 0.9072 |
| ModDrop + Missing T1c | 0.9272 | 0.8095 | 0.6540 | 0.7969 |
| Dice Drop | 0.0088 | 0.1038 | 0.2183 | 0.1103 |

## 初步结论

训练阶段引入随机单模态 Dropout 后，模型在 T1c 缺失条件下的 WT、TC、ET 均显著优于 Full-only 模型。尤其是 TC 和 ET 从严重退化状态得到大幅恢复。

然而，ET 在 ModDrop 模型中仍存在明显性能下降，说明简单 Modality Dropout 不能完全消除高风险缺失模式下的区域特异性不确定性。这为后续模态—区域风险校准方法提供了动机。


---

# 实验 C3：Modality Dropout 模型在 Missing FLAIR 下的评估

## 推理设置

- 模型：`nnUNetTrainerModalityDropout`
- Fold：0
- Checkpoint：`checkpoint_best.pth`
- 输入：T1n、T1c、T2w 保留；FLAIR（`_0003`）置零
- 验证病例数：251

## 主结果

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-only + Missing FLAIR | 0.7070 | 0.8625 | 0.8308 | 0.8001 |
| ModDrop + Missing FLAIR | 0.9016 | 0.9024 | 0.8626 | 0.8889 |
| ModDrop 相对 Full-only 提升 | +0.1946 | +0.0399 | +0.0318 | +0.0888 |

## ModDrop 自身完整输入与 Missing FLAIR 的对比

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| ModDrop + Full Input | 0.9360 | 0.9133 | 0.8723 | 0.9072 |
| ModDrop + Missing FLAIR | 0.9016 | 0.9024 | 0.8626 | 0.8889 |
| Dice Drop | 0.0344 | 0.0109 | 0.0097 | 0.0183 |

## 初步结论

在 FLAIR 缺失条件下，Modality Dropout 显著缓解了 Full-only 模型的 WT 性能退化。TC 和 ET 在当前 fold 0 设置下接近完整输入表现。


---

# 实验 C4：Modality Dropout 模型在 Missing T2w 下的评估

## 推理设置

- 模型：`nnUNetTrainerModalityDropout`
- Fold：0
- Checkpoint：`checkpoint_best.pth`
- 输入：T1n、T1c、FLAIR 保留；T2w（`_0002`）置零
- 验证病例数：251

## 主结果

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full-only + Missing T2w | 0.8334 | 0.8578 | 0.8391 | 0.8434 |
| ModDrop + Missing T2w | 0.9290 | 0.9049 | 0.8619 | 0.8986 |
| ModDrop 相对 Full-only 提升 | +0.0956 | +0.0471 | +0.0228 | +0.0552 |

## ModDrop 自身完整输入与 Missing T2w 的对比

| Setting | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| ModDrop + Full Input | 0.9360 | 0.9133 | 0.8723 | 0.9072 |
| ModDrop + Missing T2w | 0.9290 | 0.9049 | 0.8619 | 0.8986 |
| Dice Drop | 0.0070 | 0.0084 | 0.0104 | 0.0086 |

## 初步结论

在 T2w 缺失条件下，Modality Dropout 显著优于 Full-only 模型，并使 WT、TC、ET 的性能保持接近完整输入水平。当前 fold 0 结果表明，随机单模态缺失训练可有效降低 T2w 缺失带来的性能退化。

