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

<!-- AUTO_UNIFIED_EVAL_EXPERIMENT_START -->
# 实验记录：BraTS 十组统一逐病例评估

## 实验状态

**完成，导师验收通过。**

记录更新时间：2026-07-15 18:43:59

## 实验目的

解决此前论文图表工程依赖 fallback values 的问题，为 Full-only 和 Modality Dropout 建立统一、真实、可追溯的逐病例评估证据链。

## 数据与协议

- Dataset: BraTS 2023 GLI
- Dataset ID: 501
- Configuration: nnU-Net v2 3d_fullres
- Fold: 0
- Validation cases: 251
- Experiment groups: 10
- Prediction and label format: NIfTI `.nii.gz`
- Empty-empty Dice convention: 1.0

BraTS 2023 标签：

- 0 = Background
- 1 = NCR/NET
- 2 = Edema
- 3 = Enhancing Tumor

区域定义：

- WT = labels 1 + 2 + 3
- TC = labels 1 + 3
- ET = label 3

## 实验组

Full-only nnU-Net：

1. Full
2. Missing T1c
3. Missing FLAIR
4. Missing T2w
5. Missing T1n

Modality Dropout nnU-Net：

1. Full
2. Missing T1c
3. Missing FLAIR
4. Missing T2w
5. Missing T1n

缺失模态输入仍保持四通道，对目标模态整体置零。

## 服务器路径

统一评估目录：

`/root/autodl-tmp/nnunet_brats/missing_modality_benchmark/unified_evaluation`

核心文件：

- `01_inventory_paths.sh`
- `02_build_experiment_paths.py`
- `03_evaluate_per_case.py`
- `experiment_paths.json`
- `path_validation_log.txt`
- `evaluation_validation_log.txt`
- `results_summary.csv`
- `all_results_per_case.csv`
- `per_case/*.csv`

## 结果

| Model | Input | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---|---:|---:|---:|---:|
| Full-only | Full | 0.9326 ± 0.0839 | 0.9106 ± 0.1645 | 0.8669 ± 0.1943 | 0.9034 |
| Full-only | Missing T1c | 0.9019 ± 0.1116 | 0.2648 ± 0.2955 | 0.0599 ± 0.1643 | 0.4089 |
| Full-only | Missing FLAIR | 0.7070 ± 0.2335 | 0.8625 ± 0.2317 | 0.8308 ± 0.2296 | 0.8001 |
| Full-only | Missing T2w | 0.8334 ± 0.2183 | 0.8578 ± 0.2462 | 0.8391 ± 0.2106 | 0.8434 |
| Full-only | Missing T1n | 0.9287 ± 0.0613 | 0.9057 ± 0.1547 | 0.8585 ± 0.1837 | 0.8976 |
| ModDrop | Full | 0.9360 ± 0.0835 | 0.9133 ± 0.1558 | 0.8723 ± 0.1833 | 0.9072 |
| ModDrop | Missing T1c | 0.9272 ± 0.0887 | 0.8095 ± 0.1782 | 0.6540 ± 0.2179 | 0.7969 |
| ModDrop | Missing FLAIR | 0.9016 ± 0.1027 | 0.9024 ± 0.1763 | 0.8626 ± 0.1956 | 0.8889 |
| ModDrop | Missing T2w | 0.9290 ± 0.0855 | 0.9049 ± 0.1689 | 0.8619 ± 0.1967 | 0.8986 |
| ModDrop | Missing T1n | 0.9338 ± 0.0839 | 0.9059 ± 0.1657 | 0.8660 ± 0.1868 | 0.9019 |

## 自动验收

- Experiments evaluated: 10/10
- Expected cases per experiment: 251
- Case sets identical: PASS
- Missing labels: 0
- Shape mismatches: 0
- Affine mismatches: 0
- Invalid label files: 0
- Fallback values used: False
- Reference metric check: 10/10 PASS
- Per-case CSV files: 10
- Combined per-case rows: 2510/2510
- Overall status: PASS

重新计算值与此前四位小数参考值的最大绝对误差小于 0.0001。

## 主要结论

1. Full-only 在 Missing T1c 下发生 TC/ET 区域特异性崩溃；
2. Missing FLAIR 主要损害 WT；
3. Missing T2w 产生中等退化；
4. Missing T1n 影响较小；
5. Modality Dropout 显著缓解单模态缺失退化；
6. ModDrop Missing T1c 下 ET 仍从 0.8723 降至 0.6540；
7. 该残余风险支持继续研究 modality-region risk-aware learning。

## 对论文的作用

本阶段不是最终方法创新，但完成了论文实验可靠性的基础设施：

- 结果来源可追溯；
- 同病例公平比较；
- 支持配对统计检验；
- 支持效应量和置信区间；
- 支持客观定性病例选择；
- 支持失败病例分析；
- 支持 Risk-aware V1 与基线的统一评估。

## 表述限制

当前可表述为：

- fold 0 preliminary benchmark；
- zero-filled missing-modality stress test；
- Modality Dropout strong baseline；
- modality-region-specific degradation evidence。

当前不可表述为：

- 最终五折结果；
- 统计显著；
- SOTA；
- 临床验证；
- 最终缺失模态性能；
- 最终论文创新。

## 下一步

基于逐病例结果，按固定规则筛选 5 个 Missing T1c 定性病例。
<!-- AUTO_UNIFIED_EVAL_EXPERIMENT_END -->

<!-- AUTO_T1C_CASE_SELECTION_EXPERIMENT_START -->
# 实验 D1：Missing T1c 定性病例自动筛选

## 实验状态

**完成，自动验收通过。**

记录更新时间：2026-07-27 13:03:04 +0800

## 实验目的

基于统一逐病例 WT、TC、ET Dice，使用可复现的固定规则选择 Missing T1c 定性病例，避免人工挑选最好看的结果，并同时覆盖恢复成功、代表性表现和残余失败。

## 输入与输出

输入：

- `all_results_per_case.csv`
- 四组实验：`fullonly_full`、`fullonly_missing_t1c`、`moddrop_full`、`moddrop_missing_t1c`
- fold 0 验证病例：251

输出：

- `04_select_t1c_cases.py`
- `t1c_case_metrics_all_251.csv`
- `qualitative_case_candidates_t1c.csv`
- `qualitative_case_selection_log.txt`
- `qualitative_case_candidates_t1c.sha256`

## 五类确定性筛选规则

1. `strongest_et_recovery`：ET 恢复量最大；
2. `strongest_tc_recovery`：TC 恢复量最大；
3. `largest_residual_et_gap`：ModDrop 后 ET 残余差距最大；
4. `representative_median_recovery`：接近总体中位恢复量；
5. `collapse_then_robust_rescue`：Full-only 崩溃后被 ModDrop 稳健挽救。

筛选过程无随机抽样。

## 入选病例与关键指标

| Case ID | selection_reason | TC recovery | ET recovery | ET residual gap |
|---|---|---:|---:|---:|
| BraTS_0277 | strongest_et_recovery | 0.9224 | 0.8812 | 0.0301 |
| BraTS_0501 | strongest_tc_recovery | 0.9560 | 0.8436 | 0.0935 |
| BraTS_0647 | largest_residual_et_gap | 0.1217 | 0.0000 | 0.9323 |
| BraTS_0302 | representative_median_recovery | 0.6653 | 0.6877 | 0.2057 |
| BraTS_1007 | collapse_then_robust_rescue | 0.7449 | 0.8222 | 0.0995 |

## 首次运行问题与修复

第一次运行的验收结果：

- Selected table missing values: 4
- Overall status: FAIL

原因不是 Dice 缺失，而是临时辅助列 `distance_to_median_et_recovery` 只存在于中位病例候选表，合并选中病例时导致另外四个病例该列为 NaN。

删除该辅助列后：

- Selected table missing values: 0
- Overall status: PASS

## 确定性与最终验收

- Complete T1c cases: 251/251
- Selected cases: 5/5
- Unique selected cases: 5/5
- Derived metric missing values: 0
- Selected table missing values: 0
- Selection reasons complete: PASS
- 两次运行 SHA256 完全一致：`3533a582bdc6bf8b8ddf1f3e6ae9e06e17373eb96f6ab4fa3c7a52c4103f708a`
- Overall status: PASS
<!-- AUTO_T1C_CASE_SELECTION_EXPERIMENT_END -->
