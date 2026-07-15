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

## 刚完成的阶段

**BraTS 2023 GLI fold 0 十组统一逐病例评估流水线已完成，并通过导师验收。**

完成内容：

- Full-only nnU-Net：Full 与四种单模态缺失；
- Modality Dropout nnU-Net：Full 与四种单模态缺失；
- 共 10 组实验；
- 每组使用相同的 251 个验证病例；
- 从真实 prediction NIfTI 和 ground-truth NIfTI 重算 WT、TC、ET Dice；
- 生成 10 份逐病例 CSV；
- 生成 2510 行合并逐病例表；
- 取消 fallback values；
- 10/10 组历史参考指标核对通过。

## 当前唯一任务

**基于逐病例指标，按照固定规则筛选 5 个 Missing T1c 定性病例。**

必须覆盖：

1. ET 恢复量最大病例；
2. TC 恢复量最大病例；
3. ModDrop 后仍有最大 ET 残余差距病例；
4. 接近总体中位恢复量的代表性病例；
5. Full-only 几乎崩溃、ModDrop 恢复良好的病例。

## 为什么它是当前最高优先级

现有结果已经证明 Missing T1c 对 TC 和 ET 的风险最大。Modality Dropout 虽然大幅恢复性能，但 Missing T1c 下 ET 仍从完整输入的 0.8723 降至 0.6540。

在训练 Risk-aware V1 前，先建立客观的病例级证据，可以：

- 避免人工挑选最好看的病例；
- 展示 ModDrop 的恢复能力和残余失败；
- 为后续 Risk-aware 方法设计提供具体病例依据；
- 为论文定性图和失败病例分析准备输入。

## 导师验收标准

必须生成：

- `t1c_case_metrics_all_251.csv`
- `qualitative_case_candidates_t1c.csv`
- `qualitative_case_selection_log.txt`

必须满足：

- Complete T1c cases: 251/251
- Selected cases: 5/5
- Unique selected cases: 5/5
- Derived metric missing values: 0
- Selected table missing values: 0
- Overall status: PASS

## 当前暂时不要做

- 不启动 5-fold；
- 不开始 HD95；
- 不同时复现多个新模型；
- 不修改 backbone；
- 不直接训练 Risk-aware V1；
- 不手工挑选定性病例。

更新时间：2026-07-15 18:43:59
<!-- AUTO_CURRENT_NEXT_STEP_END -->
