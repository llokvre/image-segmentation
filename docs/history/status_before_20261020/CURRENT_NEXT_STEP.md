# 当前下一步

> 最后更新：2026-09-08
> 当前阶段：A2（ModDrop + Explicit Availability）fold 0 已完成最终审计并冻结为 **WEAK**；下一阶段为 Teacher Qualification。

## 已完成

- Full-only nnU-Net：Full + Missing T1c / FLAIR / T2w / T1n
- Modality Dropout nnU-Net：Full + Missing T1c / FLAIR / T2w / T1n
- 已生成论文级 CSV、Excel、PNG 图和 README

## 结果文件目录

/root/autodl-tmp/nnunet_brats/missing_modality_benchmark/paper_assets_moddrop

## 当前核心结论

- Full-only 模型在缺模态下存在明显模态—区域特异性退化。
- T1c 缺失主要损害 TC 和 ET。
- FLAIR 缺失主要损害 WT。
- Modality Dropout 显著缓解缺模态退化。
- Missing T1c 下 ET 仍存在残余下降，是后续风险校准方法的重点目标。

## 下一步

1. 人工检查生成的 PNG 图是否清晰、是否适合论文/PPT。
2. 检查 Excel 表格数值是否与实验记录一致。
3. 修复脚本的 JSON 读取路径，让 validation_log 不再全部显示 fallback。
4. 选择典型病例做定性可视化。
5. 开始设计下一阶段：模态—区域风险校准方法。

<!-- AUTO_CURRENT_NEXT_STEP_START -->
# 当前状态与唯一下一步

## 刚完成：Missing T1c 定性病例自动筛选

- Complete T1c cases: 251/251
- Selected cases: 5/5
- Unique selected cases: 5/5
- Derived metric missing values: 0
- Selected table missing values: 0
- Selection reasons complete: PASS
- 筛选过程不使用随机抽样，也不进行人工挑选。
- 两次运行的确定性 SHA256 完全一致：`3533a582bdc6bf8b8ddf1f3e6ae9e06e17373eb96f6ab4fa3c7a52c4103f708a`
- Overall status: PASS

固定病例及筛选原因：

| Case ID | selection_reason |
|---|---|
| BraTS_0277 | strongest_et_recovery |
| BraTS_0501 | strongest_tc_recovery |
| BraTS_0647 | largest_residual_et_gap |
| BraTS_0302 | representative_median_recovery |
| BraTS_1007 | collapse_then_robust_rescue |

## 当前唯一下一步

**为上述五个固定病例生成第一版 Missing T1c 定性对比图。**

第一版只比较：

1. MRI 背景切片；
2. Ground Truth；
3. Full-only + Missing T1c；
4. ModDrop + Missing T1c。

病例 ID 和切片位置必须由脚本确定并固定，禁止人工挑选最好看的结果。当前收尾阶段不实际生成定性图。

## 下一阶段验收标准

- Cases rendered: 5/5
- Case IDs identical to selection CSV: PASS
- Missing MRI files: 0
- Missing label files: 0
- Missing prediction files: 0
- Shape mismatches: 0
- Output PNG files: 6/6
- Overall status: PASS

更新时间：2026-07-27 13:03:04 +0800
<!-- AUTO_CURRENT_NEXT_STEP_END -->

<!-- AUTO_T1C_QUALITATIVE_CURRENT_START -->

## Missing T1c 确定性定性可视化里程碑

状态：**已完成并通过自动验收**。

- 固定病例与确定性轴向切片：

  | Case ID | z | Slice basis |
  |---|---:|---|
  | BraTS_0277 | 55 | GT_ET_max_area |
  | BraTS_0501 | 59 | GT_ET_max_area |
  | BraTS_0647 | 91 | GT_ET_max_area |
  | BraTS_0302 | 36 | GT_ET_max_area |
  | BraTS_1007 | 96 | GT_ET_max_area |

- 所有切片均完全依据 Ground Truth 中 ET 面积最大的轴向切片自动选择；并列时使用最小 z 索引，未进行人工选片。
- 已生成 5 张独立病例 PNG 和 1 张五病例汇总 PNG。
- `qualitative_visualization_manifest.csv` 为 5 行、5 个唯一病例且无缺失值。
- 两次独立运行得到完全一致的 Manifest SHA256：
  `56c1f2ef4ef06896bd7acc18ca613351d97a6ab40b6ce8ed387dcd9bee638c6f`
- 本阶段没有执行模型推理、模型训练、预测后处理或人工切片替换。
- Original T1c 仅作为可视化参考背景，不是 Missing T1c 模型的输入。

### 当前唯一下一步

**编写 Risk-aware V1 工程设计文档。**

设计文档只需明确：

1. modality availability mask 的表示方式；
2. mask 在网络中的注入位置；
3. Missing T1c 对 TC/ET 的区域风险如何进入损失；
4. region-weighted loss 的数学定义；
5. 训练和推理协议；
6. 第一轮消融实验；
7. 与 ModDrop strong baseline 的公平比较；
8. 失败回退条件。

**当前只设计，不实现、不训练。**

本区块是当前任务状态的唯一权威说明；此前指向“生成五个固定病例定性图”的下一步已经完成，不再是当前任务。

<!-- AUTO_T1C_QUALITATIVE_CURRENT_END -->

<!-- AUTO_A2_AVAILABILITY_FREEZE_START -->
## A2 Availability 最终审计与阶段冻结（当前权威状态）

> 本节覆盖文档中更早的“当前阶段 / 下一步”描述。A2 已结束，不再继续训练、推理或扩展实验。

### 已完成与已核验

- A2 fold 0 完成 1000 epochs；最佳 epoch 为 977。
- 最佳 checkpoint SHA-256：`070250c3ddcba723b1279c7ba77e27e9bc59c7107feaff919dc1a20890fe2689`。
- Stage 2C smoke test：PASS。
- 最终 benchmark：251 个验证病例 × 5 种输入条件，共 1255 个预测，独立只读审计 PASS。
- 1255/1255 文件可读、非空、shape/affine 与 GT 一致、标签合法且数值有限。
- 独立 Dice 复算与病例级 CSV 最大绝对差为 `4.999047065190609e-09`（阈值 `<1e-6`）。

### A2 fold 0 最终结果

| Condition | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full | 0.93461020 | 0.91254931 | 0.87157229 | 0.90624393 |
| Missing T1n | 0.93498348 | 0.91039477 | 0.86396869 | 0.90311564 |
| Missing T1c | 0.92922966 | 0.81458839 | 0.65283265 | 0.79888357 |
| Missing T2w | 0.93035692 | 0.91093994 | 0.86898677 | 0.90342788 |
| Missing FLAIR | 0.90415494 | 0.90822155 | 0.86379868 | 0.89205839 |

### 相对 A1（ModDrop）的关键配对差值

- Full Mean：`-0.00093919`
- Missing T1c TC：`+0.00506348`
- Missing T1c ET：`-0.00119277`
- Missing T1c Mean：`+0.00196931`
- Missing FLAIR WT：`+0.00258751`

### 冻结结论

**A2 结论：WEAK。** Explicit Availability 带来少量正向信号，Missing T1c 的 TC 和 Mean 略有提升，Missing FLAIR 的 WT 略有提升；但 Missing T1c 的 ET 没有改善，Full 基本维持。现有证据不足以把 availability 作为论文核心创新，只保留为可用的 conditioning variable。A2 相关表述不得使用“显著提升”“稳健提升”或“SOTA”。

小体积 padding 修复的科学语义审计通过：MRI padding、patch size、滑窗几何、Gaussian 聚合、mirroring/TTA 和模型权重均未改变；仅在进入网络前把 availability 通道的 padding 区恢复为对应常量。

**Padding fix changes inference semantics: NO**

### 接下来

当前已完成路线：**A0 Full-only complete → A1 ModDrop complete → A2 Availability complete**。

1. 进入 **Teacher Qualification**，先判断 teacher 是否具备足够、可复现的特权信息优势。
2. 旧的 **Risk-aware Region Loss** 主线暂停。
3. 当前主研究假设为 **Missingness-conditioned selective privileged distillation**，但目前尚未验证。
4. Teacher、KD、Vulnerability、Reliability 均尚未实现，不得写成已完成或正在运行。

<!-- AUTO_A2_AVAILABILITY_FREEZE_END -->
