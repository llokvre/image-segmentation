# 7. 局限性草稿

1. **单折评估**：当前结果只来自 fold 0 和 251 个验证病例，无法估计跨 fold 波动或稳定性。
2. **缺失机制简化**：实验用 zero-filled channel 模拟缺失模态，属于 direct-inference stress test，不覆盖模态合成失败、部分采集或不同强度归一化等情况。
3. **数据不可随仓库分发**：BraTS 数据、标签、预测和 checkpoint 未包含在 GitHub 中，当前仓库不能独立重跑训练。
4. **指标范围有限**：目前主要使用 WT/TC/ET Dice，尚未加入 HD95、病例级置信区间、校准和失败病例分析。
5. **fallback 数值**：当前论文资产脚本因缺少真实 metric JSON/CSV 路径而使用人工确认的 fallback；这降低了自动化 provenance 的完整性。
6. **历史数值不一致**：旧版实验记录有另一组 Full-only 完整输入结果，需要从源文件核对，不应混用。
7. **Modality Dropout 不是最终创新**：它是 strong baseline，尚未证明风险感知方法的增益。
8. **未进行统计检验**：当前结果不能写成 statistically significant，也不能作临床性能结论。
9. **定性证据不足**：还没有系统呈现 GT、预测、错误区域和不确定性图。
10. **方法尚未实现**：risk-aware pseudo-labeling、region-adaptive threshold 和 teacher-student training 仍是计划，尚无结果。

最终论文必须在方法、实验和结论中重复说明这些边界，避免读者把 preliminary benchmark 误解为临床验证或最终模型。
