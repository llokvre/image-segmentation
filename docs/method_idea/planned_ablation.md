# 计划中的消融实验

> 状态：实验计划，尚未执行。

## 基线组

| 编号 | 方案 | 目的 |
|---|---|---|
| A0 | Full-only | 测量未做缺失模态训练时的退化 |
| A1 | Modality Dropout | strong robustness baseline |
| A2 | Teacher-student + uniform threshold | 区分 teacher-student 本身的作用 |

## 风险感知组

| 编号 | 方案 | 保留组件 |
|---|---|---|
| B1 | risk-aware threshold | 只加入 modality-region threshold |
| B2 | uncertainty filtering | 只加入不确定性过滤 |
| B3 | B1 + B2 | 阈值与不确定性联合 |
| B4 | B3 + consistency weighting | 增加缺失模式一致性 |
| B5 | B4 + reliability weighting | 增加模态/区域可靠性加权 |

## 必须固定的条件

- 相同的数据划分和预处理。
- 相同的 backbone、训练预算和 checkpoint 选择规则。
- 相同的 Full、Missing T1c、Missing FLAIR、Missing T2w、Missing T1n 输入协议。
- 相同的 WT/TC/ET 指标实现。
- 风险矩阵和阈值只从训练内部开发数据估计。

## 主要评价问题

1. Missing T1c × ET/TC 是否改善？
2. Missing FLAIR × WT 是否改善？
3. 是否保持完整输入性能？
4. 是否对低风险 Missing T1n 产生不必要损害？
5. 跨 fold 的提升方向是否一致？
6. 伪标签覆盖率和错误率是否发生不利变化？

## 失败判据

如果风险感知组件只提高 Mean Dice，却使 ET 召回、伪标签精度或完整输入性能明显下降，则不能直接作为成功方法。应报告风险矩阵稳定性和负面结果，而不是只保留最有利的指标。

## 后续扩展

在单模态缺失稳定后，再考虑多模态同时缺失、低标注比例、不同 zero-fill/归一化策略和外部验证。扩展实验不能与当前单模态压力测试混为一组结论。
