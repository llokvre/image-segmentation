# 5. 结果草稿

> 当前结果为 fold 0 single-fold preliminary benchmark。表中数值来自人工确认的 fallback 记录，直到真实 JSON/CSV 路径修复前，不应写成完全自动化复现结果。

## 5.1 完整输入

Full-only 的完整输入 Dice 为 WT 0.9326 +/- 0.0839、TC 0.9106 +/- 0.1645、ET 0.8669 +/- 0.1943，Mean 为 0.9034。Modality Dropout 的对应结果为 WT 0.9360 +/- 0.0835、TC 0.9133 +/- 0.1558、ET 0.8723 +/- 0.1833，Mean 为 0.9072。

当前单折结果中，Modality Dropout 的完整输入均值略高，但该差异不能解释为统计显著提升，也不能排除训练随机性、checkpoint 或评估实现差异。

## 5.2 Full-only 的缺失模态压力测试

| Missing modality | WT | TC | ET | Mean |
|---|---:|---:|---:|---:|
| T1c | 0.9019 | 0.2648 | 0.0599 | 0.4089 |
| FLAIR | 0.7070 | 0.8625 | 0.8308 | 0.8001 |
| T2w | 0.8334 | 0.8578 | 0.8391 | 0.8434 |
| T1n | 0.9287 | 0.9057 | 0.8585 | 0.8976 |

相对于 Full-only 完整输入，T1c 缺失时 TC 和 ET 的下降分别为 0.6458 和 0.8070；FLAIR 缺失时 WT 的下降为 0.2256；T2w 缺失造成中等幅度下降；T1n 缺失的下降最小。

## 5.3 Modality Dropout 的缺失模态压力测试

| Missing modality | WT | TC | ET | Mean |
|---|---:|---:|---:|---:|
| T1c | 0.9272 | 0.8095 | 0.6540 | 0.7969 |
| FLAIR | 0.9016 | 0.9024 | 0.8626 | 0.8889 |
| T2w | 0.9290 | 0.9049 | 0.8619 | 0.8986 |
| T1n | 0.9338 | 0.9059 | 0.8660 | 0.9019 |

相对于 Modality Dropout 自身的完整输入，Missing T1c 下 ET 的下降为 0.2183，仍然是当前最需要处理的风险区域；FLAIR、T2w 和 T1n 的区域级下降相对较小。

## 5.4 结果解释

结果支持两个阶段性观察：第一，缺失模态的影响具有 region-dependent pattern；第二，训练时模拟缺失模态可以显著缓解 direct-inference 退化。结果还显示，Modality Dropout 不能完全消除高风险模态—区域组合，因此为后续 risk-aware 方法提供了经验动机。

## 5.5 表述边界

当前结果不支持 SOTA、statistically significant 或 clinically validated 等表述。最终结果章节需要加入多折、真实源指标、统计分析、HD95 和定性病例图后再重写。
