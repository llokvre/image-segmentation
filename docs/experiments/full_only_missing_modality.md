# Full-only 缺失模态压力测试

## 目的

测量只在完整四模态上训练的 nnU-Net 在推理阶段直接遇到单模态 zero-fill 时的区域级性能退化。

## 输入与模型

- Model: nnU-Net v2。
- Configuration: `3d_fullres`。
- Fold: 0。
- Checkpoint: `checkpoint_best.pth`。
- Training input: complete T1n + T1c + T2w + FLAIR only。
- Validation: 251 cases。

## 推理条件

保持四通道形状不变，每次只将一个通道替换为全零：

| Setting | Zero-filled channel |
|---|---|
| Missing T1c | `_0001` |
| Missing FLAIR | `_0003` |
| Missing T2w | `_0002` |
| Missing T1n | `_0000` |

## 结果

| Input | WT Dice | TC Dice | ET Dice | Mean Dice |
|---|---:|---:|---:|---:|
| Full input | 0.9326 +/- 0.0839 | 0.9106 +/- 0.1645 | 0.8669 +/- 0.1943 | 0.9034 |
| Missing T1c | 0.9019 +/- 0.1116 | 0.2648 +/- 0.2955 | 0.0599 +/- 0.1643 | 0.4089 |
| Missing FLAIR | 0.7070 +/- 0.2335 | 0.8625 +/- 0.2317 | 0.8308 +/- 0.2296 | 0.8001 |
| Missing T2w | 0.8334 +/- 0.2183 | 0.8578 +/- 0.2462 | 0.8391 +/- 0.2106 | 0.8434 |
| Missing T1n | 0.9287 +/- 0.0613 | 0.9057 +/- 0.1547 | 0.8585 +/- 0.1837 | 0.8976 |

## 主要结论

当前结果支持 region-dependent degradation pattern：Missing T1c 主要破坏 TC/ET，Missing FLAIR 主要影响 WT，Missing T1n 影响最小。该结论只适用于当前 fold 和 zero-fill stress test。

## 注意事项

- 该实验不代表模型已经学会缺失模态鲁棒性。
- zero-fill 不是唯一真实缺失模态机制。
- 当前资产读取不到原始 metric JSON/CSV，因此生成脚本记录了 fallback 来源。
- 旧版实验记录中有一组不同的 Full-only 完整输入数值，需在源环境核对。
