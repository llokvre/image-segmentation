# 下一阶段方法动机

## 从 baseline 到方法问题

Full-only baseline 在完整输入下平均 Dice 为 0.9034，但 Missing T1c 后 Mean 降至 0.4089；更重要的是 WT、TC、ET 的下降幅度并不一致。Modality Dropout 将 Missing T1c 的 Mean 恢复到 0.7969，说明训练时暴露于缺失模式很重要，但 ET 仍从其完整输入 0.8723 降至 0.6540。

这给出两个层次的结论：

1. 缺失模态鲁棒性可以通过训练分布匹配得到明显改善；
2. 仅使用随机单模态 dropout 仍然没有显式表达“哪种缺失会伤害哪个区域”。

## 方法假设

如果某个 modality-region pair 在多个开发 fold 或训练内部验证中稳定地呈现高风险，那么该 pair 的伪标签质量、预测不确定性和一致性损失权重可能需要单独处理。换句话说，风险矩阵不是最终答案，而是用于把全局训练目标拆成条件化区域目标的中间表示。

## 计划的技术组件

- modality-region risk matrix：描述条件风险；
- uncertainty-aware pseudo-label filtering：过滤高不确定性候选；
- region-adaptive threshold：为 WT/TC/ET 设置条件阈值；
- missing-modality-aware consistency：在缺失模式之间约束稳定预测；
- modality-specific reliability weighting：让不同模态缺失下的区域损失具有不同权重；
- teacher-student semi-supervised learning：在低标注场景利用未标注数据。

## 为什么不能直接宣称创新完成

当前只有一个 fold 的 baseline 结果，且资产部分使用 fallback 数值。风险矩阵的稳定性、阈值是否会造成偏置、teacher 是否可靠、方法是否在完整输入下付出代价，都还没有实验支持。因此现在应把它写为方法动机和 planned design，而不是已完成方法或最终贡献。

## 第一性验证问题

后续最先需要回答：在固定网络和固定数据划分下，仅把统一伪标签阈值改为 modality-region 条件阈值，是否能在 Missing T1c × ET/TC 上稳定改善，同时不损害 WT 和完整输入性能？
