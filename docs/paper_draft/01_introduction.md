# 1. 引言草稿

> 文档性质：中文工作草稿。引用位置先用占位符，后续需要根据真实文献补充。

多模态 MRI 为脑肿瘤分割提供互补的组织对比信息，但在实际采集、转诊和检查流程中，某些模态可能缺失或不可用。缺失模态不仅会降低模型输入的信息量，也可能改变不同肿瘤区域的可辨识性。对于 WT、TC 和 ET 这类具有不同边界和组织特征的区域，统一描述“缺失模态导致整体性能下降”可能掩盖更重要的区域级风险。

现有缺失模态研究通常关注以下方向：使用模态合成恢复缺失图像、设计能够适应可变输入的网络、在训练期间随机丢弃模态，或通过教师—学生和一致性学习利用未标注样本。[待补充代表性文献] 这些方法能够改善输入缺失下的平均分割性能，但仍需要回答一个更细的问题：某一个模态的缺失，究竟会优先损害哪个分割区域，以及这种风险是否能够指导训练过程中的伪标签筛选和可靠性加权。

本项目首先建立两个可复现的基线。第一个是只使用完整四模态训练的 Full-only nnU-Net；第二个是训练阶段以 50% 概率随机置零一个模态的 Modality Dropout nnU-Net。两者均在四通道输入下评估，并通过将一个通道置零实现 zero-filled missing-modality direct-inference stress test。当前结果使用 BraTS 2023 GLI、nnU-Net v2 `3d_fullres`、fold 0 和 251 个验证病例。

在当前 preliminary benchmark 中，Full-only 模型表现出明显的模态—区域差异：Missing T1c 时 TC 和 ET 的 Dice 明显下降，而 Missing FLAIR 时 WT 的下降更突出。Modality Dropout 在四种单模态缺失条件下均缓解了这种退化，且完整输入下没有观察到明显代价。然而，Missing T1c 下 ET 仍低于 Modality Dropout 的完整输入结果，提示随机 dropout 虽然是有效的鲁棒性 baseline，但未必能针对高风险模态—区域对进行精细校准。

因此，本文阶段性目标不是宣称一个已经完成的新方法，而是用基线实验建立下一阶段方法动机。后续计划围绕 modality-region risk matrix、uncertainty-aware pseudo-label filtering、region-adaptive threshold、missing-modality-aware consistency 和 modality-specific reliability weighting 展开。该方法方向仍需要独立实现、消融和多折验证。

本文的当前贡献边界可以暂时写为：

1. 建立一个明确记录的 zero-filled missing-modality direct-inference 压力测试协议；
2. 在 fold 0 上比较 Full-only 与 Modality Dropout 的区域级性能变化；
3. 观察并整理模态—区域风险模式；
4. 提出一个由风险矩阵驱动的后续方法设计，而不是把设计阶段结果包装为已完成创新。

需要在最终版本中补充真实文献、数据许可说明、训练细节、源指标文件和多折统计结果。
