# 当前下一步

> 最后更新：2026-07-09  
> 当前阶段：Full-only 与 Modality Dropout 基线结果已整理成论文级图表。

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
