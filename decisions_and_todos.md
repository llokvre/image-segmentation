# BraTS 项目研究决策与待办事项

> 作用：记录“为什么这样设计”“哪些结论不能过度解释”“当前最优先做什么”。  
> 每当研究方向、实验方案或下一步计划发生变化时，更新此文件。

---

## 1. 当前研究问题

研究任务：

> BraTS 2023 多模态 MRI 脑肿瘤分割在 MRI 模态缺失时的鲁棒性问题。

当前核心观察：

- 缺失 T1c 时，TC 和 ET 分割出现严重退化；
- 缺失 FLAIR 时，WT 分割明显退化；
- 缺失 T2w 时，WT 有中等程度退化；
- 缺失 T1n 时，整体影响很小。

因此，当前研究假设是：

> 缺失 MRI 模态导致的分割风险具有明显的“模态—区域特异性”。  
> 不同缺失模式和不同肿瘤区域，不应该共用同一个固定的伪标签筛选阈值或训练策略。

---

## 2. 已完成实验的正确定位

目前完成的是：

```text
完整四模态训练
+
推理阶段将一个模态替换为全零图像
+
直接推理压力测试

<!-- AUTO_UNIFIED_EVAL_DECISIONS_START -->
# 统一逐病例评估阶段：决策与任务状态

## 已确认的研究决策

### D1. 统一逐病例评估成为后续正式评估入口

Full-only 与 Modality Dropout 的 10 组结果已经从真实 NIfTI 重算并通过核对。后续统计检验、病例筛选、图表和新方法比较必须读取统一评估输出，不再使用人工 fallback 数值。

### D2. Modality Dropout 定位为 strong baseline

Modality Dropout 在完整输入下没有明显性能代价，并显著提升缺失模态鲁棒性；但它只能作为 strong baseline，不能作为最终方法创新。

### D3. Missing T1c 是第一高风险条件

- Full-only Missing T1c 对 TC 和 ET 的破坏最严重；
- ModDrop 大幅恢复 TC 和 ET；
- ModDrop 后 ET 仍存在明显残余下降；
- Risk-aware V1 第一轮优先针对 Missing T1c 的 TC/ET。

### D4. 每完成一个实验阶段，固定更新三份 Markdown

以后阶段结束顺序固定为：

1. 实验运行完成；
2. 指标和文件验收通过；
3. 更新 `CURRENT_NEXT_STEP.md`；
4. 更新 `decisions_and_todos.md`；
5. 更新 `experiments_record.md`；
6. 创建独立 Git commit；
7. 推送 GitHub；
8. 再进入下一实验阶段。

## 已完成

- [x] 找齐 10 组真实预测目录；
- [x] 固定 `experiment_paths.json`；
- [x] 验证每组 251 个病例；
- [x] 验证十组病例集合完全一致；
- [x] 验证预测与标签一一匹配；
- [x] 从真实 NIfTI 重算 WT、TC、ET Dice；
- [x] 保存十份 per-case CSV；
- [x] 保存 2510 行合并逐病例结果；
- [x] 自动汇总均值和标准差；
- [x] 10/10 组参考结果核对通过；
- [x] 解决 fallback values 问题。

## 当前唯一待办

- [ ] 按固定规则筛选 5 个 Missing T1c 定性病例。

## 后续待办，当前暂不执行

- [ ] 生成 MRI、GT、Full-only、ModDrop 定性对比图；
- [ ] 形成 Risk-aware V1 工程设计文档；
- [ ] 实现 modality availability mask；
- [ ] 实现 modality-region risk-weighted region loss；
- [ ] 实现 HeMIS-style baseline；
- [ ] 选择现代缺失模态强基线；
- [ ] 补充 HD95；
- [ ] 配对统计检验和效应量；
- [ ] 进入 5-fold；
- [ ] 少标注与半监督实验。

## 当前限制

- 当前仅为 fold 0 preliminary benchmark；
- 当前为 zero-filled missing-modality stress test；
- 尚无 HD95；
- 尚无统计检验；
- 尚无五折；
- 尚无现代专用强基线；
- 尚未验证 Risk-aware V1；
- 不能宣称 SOTA、统计显著或临床验证。

更新时间：2026-07-15 18:43:59
<!-- AUTO_UNIFIED_EVAL_DECISIONS_END -->

<!-- AUTO_T1C_CASE_SELECTION_DECISIONS_START -->
# Missing T1c 定性病例筛选：研究决策与任务状态

## 已确认的研究决策

- 定性病例必须基于统一逐病例指标和固定规则自动筛选，不能人工挑选。
- Modality Dropout 是 strong baseline，不是最终创新。
- 五个病例分别覆盖恢复成功、TC 恢复、残余失败、中位代表和崩溃后挽救：
  - `BraTS_0277` — `strongest_et_recovery`（恢复成功）；
  - `BraTS_0501` — `strongest_tc_recovery`（TC 恢复）；
  - `BraTS_0647` — `largest_residual_et_gap`（残余失败）；
  - `BraTS_0302` — `representative_median_recovery`（中位代表）；
  - `BraTS_1007` — `collapse_then_robust_rescue`（崩溃后挽救）。
- `BraTS_0647` 是重要的 ModDrop 残余失败病例。
- 当前先完成五病例定性图，之后才进入 Risk-aware V1。
- 当前仍只是 fold 0 preliminary benchmark。
- 当前是 zero-filled missing-modality stress test。
- 不得宣称 SOTA、统计显著或临床验证。
- 确定性选择签名：`3533a582bdc6bf8b8ddf1f3e6ae9e06e17373eb96f6ab4fa3c7a52c4103f708a`。

## 任务状态

- [x] 筛选五个 Missing T1c 病例。
- [ ] **当前唯一待办：生成五病例 Missing T1c 定性对比图。**

更新时间：2026-07-27 13:03:04 +0800
<!-- AUTO_T1C_CASE_SELECTION_DECISIONS_END -->
