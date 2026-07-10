# 8. 下一阶段工作草稿

## 8.1 近期工程任务

- 在原始实验环境找到真实 metric JSON/CSV，并记录文件路径、哈希和 schema。
- 重新生成 CSV/XLSX/PNG，确认 `used_fallback=False` 的来源日志。
- 解决旧版 Full-only 完整输入数值与当前 canonical 表格的差异。
- 检查图表在论文目标尺寸、灰度打印和投影展示下的可读性。
- 选择代表性病例建立定性可视化流程。

## 8.2 方法原型

第一版方法建议只实现一个最小变量：根据缺失模态和区域设置伪标签筛选阈值，同时保持网络结构与 Modality Dropout baseline 不变。这样可以先回答风险条件化是否带来可测增益，再逐步加入不确定性、consistency 和 reliability weighting。

## 8.3 评估与消融

计划至少比较：

1. Full-only；
2. Modality Dropout；
3. 统一伪标签阈值；
4. modality-region risk-aware 阈值；
5. risk-aware + uncertainty filtering；
6. 去掉 consistency 或 reliability weighting 的消融。

所有方案需要在相同 fold、相同缺失协议和相同 checkpoint 选择规则下比较。

## 8.4 远期实验

- 五折交叉验证。
- 不同缺失模式组合，包括多模态同时缺失。
- 低标注 setting 和半监督 teacher-student 学习。
- HD95、表面距离和病例级风险校准。
- 跨数据集或外部验证，前提是数据许可和实验资源允许。

## 8.5 论文写作顺序

先完成真实数据源核对和实验记录，再补相关工作引用；方法实现和消融稳定后，再将当前中文草稿改写为英文论文，而不是提前把设计假设写成最终结论。
