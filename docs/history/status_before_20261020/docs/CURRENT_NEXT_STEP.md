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