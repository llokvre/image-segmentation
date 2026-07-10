# 3. 方法草稿

> 本节同时记录已完成 baseline 和计划中的方法。计划内容均使用“拟”“计划”“待实现”，不表示已经完成。

## 3.1 输入和区域定义

输入为四通道 MRI，通道顺序为 T1n、T1c、T2w、FLAIR。BraTS 标签为 0 背景、1 NCR/NET、2 Edema、3 Enhancing Tumor。评估区域定义为 WT = 1+2+3、TC = 1+3、ET = 3。

## 3.2 Full-only baseline

Full-only 使用 nnU-Net v2 `3d_fullres` 配置，在训练阶段输入完整四模态。推理时将一个模态通道替换为全零，但保留四通道张量形状。这一设计用于测量模型在未进行缺失模态训练时的直接推理退化。

## 3.3 Modality Dropout baseline

`nnUNetTrainerModalityDropout` 在训练样本级别执行随机输入扰动：50% 概率保持完整输入，50% 概率随机选择一个通道置零。验证和推理不执行随机 dropout，而是按照固定的 Full、Missing T1c、Missing FLAIR、Missing T2w、Missing T1n 条件评估。

该 baseline 的作用是检验“在训练阶段见过缺失模式”是否足以提升鲁棒性。当前结果表明它能显著缓解单模态缺失造成的下降，但 Missing T1c × ET/TC 仍存在残余风险。

## 3.4 计划中的风险感知方法

后续拟定义一个模态—区域风险矩阵 `R(m, r)`，其中 `m` 表示缺失模态，`r` 表示 WT/TC/ET。初始版本可以由 Full-only 和 Modality Dropout 在验证集上的 Dice drop 或 recovery gain 构造，但正式方法需要在训练集划分、验证集和多折结果上严格估计，避免把测试信息泄漏到训练过程。

对于一个缺失模式 `m` 和区域 `r`，计划使用：

- 区域自适应伪标签阈值 `tau(m, r)`；
- 不确定性筛选 `u(x, r) < kappa(m, r)`；
- 缺失模态感知的一致性权重 `w(m, r)`；
- 模态/区域可靠性加权的监督或伪监督损失。

一个待验证的概念形式为：

```text
L = L_supervised + lambda_consistency * sum_r w(m, r) * L_consistency(r)
```

其中 `w(m, r)` 不能直接由当前测试结果手工指定。需要定义训练内估计方式、归一化方式和不确定性校准策略，并通过消融验证每个组件的作用。

## 3.5 教师—学生方向

计划构建完整模态或 EMA teacher 与缺失模态 student。teacher 预测可作为候选伪标签，student 在不同缺失模式下学习区域级一致性。伪标签只有在满足置信度、不确定性和区域风险条件时才参与损失。该设计仍是研究假设，尚未实现或验证。

## 3.6 防止数据泄漏的原则

- 风险矩阵不能直接使用测试病例标签估计。
- 阈值选择应只使用训练内部验证或交叉验证结果。
- teacher 的伪标签过滤规则要在固定开发集上确定。
- 最终结果必须在未参与风险估计的 fold 上报告。
