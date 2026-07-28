# 实验总览

## 研究问题

在四模态 BraTS 2023 GLI MRI 分割中，单一模态缺失是否会对不同肿瘤区域造成不同程度的退化？训练阶段随机模拟缺失模态能否提高 direct-inference 鲁棒性？

## 统一配置

| 项目 | 设置 |
|---|---|
| Dataset | BraTS 2023 GLI |
| Framework | nnU-Net v2 |
| Configuration | `3d_fullres` |
| Fold | 0 |
| Validation cases | 251 |
| Checkpoint | `checkpoint_best.pth` |
| Regions | WT / TC / ET |
| Missing protocol | one channel zero-filled, four-channel input retained |

## 实验矩阵

| Experiment | Training policy | Inference conditions | Status |
|---|---|---|---|
| Full-only | complete four modalities only | Full + four single-modality missing settings | Completed preliminary benchmark |
| Modality Dropout | 50% full, 50% one randomly zeroed modality | Same five fixed settings, no random inference dropout | Completed preliminary benchmark |
| Risk-aware method | To be implemented | Same protocol plus planned ablations | Not started |

## 总体观察

- Full-only 的 Missing T1c × TC/ET 风险最高。
- Full-only 的 Missing FLAIR × WT 风险最突出。
- Modality Dropout 对四种缺失模式均有恢复效果。
- Modality Dropout 完整输入下未观察到明显代价，但当前只有单折证据。
- Missing T1c × ET/TC 仍是下一阶段的 high-risk modality-region pair。

## 结论边界

当前结果属于 single-fold preliminary benchmark 和 zero-filled missing-modality direct-inference stress test。没有统计显著性、临床验证或 SOTA 结论。
