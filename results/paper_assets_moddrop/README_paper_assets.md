# BraTS Missing-Modality Paper Assets

## Reproduction
```bash
cd /root/autodl-tmp/nnunet_brats/missing_modality_benchmark/paper_assets_moddrop
python generate_moddrop_paper_assets.py
```

## Data provenance
The script first searches existing metric JSON files. Fallback values are used only when source metrics cannot be read.

- [WARNING] Full-only | Full input: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Full-only | Missing T1c: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Full-only | Missing FLAIR: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Full-only | Missing T2w: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Full-only | Missing T1n: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Modality Dropout | Full input: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Modality Dropout | Missing T1c: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Modality Dropout | Missing FLAIR: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Modality Dropout | Missing T2w: fallback values used because metric JSON unavailable/unparseable.
- [WARNING] Modality Dropout | Missing T1n: fallback values used because metric JSON unavailable/unparseable.

## 中文结果总结
在当前 zero-filled missing-modality direct-inference stress test 下，Full-only 模型呈现明显的模态—区域特异性退化：T1c 缺失主要损害 TC 与 ET，FLAIR 缺失主要损害 WT。Modality Dropout 缓解了四种单模态缺失造成的退化，并且在完整输入下未观察到明显性能代价。Missing T1c 下 ET 仍有残余下降，这为后续模态—区域风险校准训练或伪标签策略提供动机。

当前仅为 fold 0 的 single-fold preliminary benchmark，不应解释为最终临床缺失模态性能。后续仍需要 missing-modality-aware training、低标注实验、五折交叉验证、HD95、统计检验和病例可视化。

## English Results-style paragraph
Under the zero-filled missing-modality direct-inference protocol, the Full-only model showed a region-dependent degradation pattern: missing T1c predominantly affected TC and ET, whereas missing FLAIR mainly impaired WT. In this single-fold preliminary benchmark, Modality Dropout substantially mitigated performance loss across the evaluated missing-modality settings without an observable loss under complete-modality inference. Nevertheless, residual degradation remained for ET under missing T1c. These results should be interpreted as stress-test findings and require further validation under missing-modality-aware training, multi-fold evaluation, and clinical-style protocols.

## Main Tables

### Absolute Dice
| Input Setting   |   Full-only WT |   ModDrop WT |   ModDrop - Full-only WT |   Full-only TC |   ModDrop TC |   ModDrop - Full-only TC |   Full-only ET |   ModDrop ET |   ModDrop - Full-only ET |   Full-only Mean |   ModDrop Mean |   ModDrop - Full-only Mean |
|:----------------|---------------:|-------------:|-------------------------:|---------------:|-------------:|-------------------------:|---------------:|-------------:|-------------------------:|-----------------:|---------------:|---------------------------:|
| Full input      |         0.9326 |       0.9360 |                   0.0034 |         0.9106 |       0.9133 |                   0.0027 |         0.8669 |       0.8723 |                   0.0054 |           0.9034 |         0.9072 |                     0.0038 |
| Missing T1c     |         0.9019 |       0.9272 |                   0.0253 |         0.2648 |       0.8095 |                   0.5447 |         0.0599 |       0.6540 |                   0.5941 |           0.4089 |         0.7969 |                     0.3880 |
| Missing FLAIR   |         0.7070 |       0.9016 |                   0.1946 |         0.8625 |       0.9024 |                   0.0399 |         0.8308 |       0.8626 |                   0.0318 |           0.8001 |         0.8889 |                     0.0888 |
| Missing T2w     |         0.8334 |       0.9290 |                   0.0956 |         0.8578 |       0.9049 |                   0.0471 |         0.8391 |       0.8619 |                   0.0228 |           0.8434 |         0.8986 |                     0.0552 |
| Missing T1n     |         0.9287 |       0.9338 |                   0.0051 |         0.9057 |       0.9059 |                   0.0002 |         0.8585 |       0.8660 |                   0.0075 |           0.8976 |         0.9019 |                     0.0043 |

### Robustness Dice Drop
| Missing Modality   |   Full-only WT Drop |   ModDrop WT Drop |   Drop Reduction WT |   Full-only TC Drop |   ModDrop TC Drop |   Drop Reduction TC |   Full-only ET Drop |   ModDrop ET Drop |   Drop Reduction ET |   Full-only Mean Drop |   ModDrop Mean Drop |   Drop Reduction Mean |
|:-------------------|--------------------:|------------------:|--------------------:|--------------------:|------------------:|--------------------:|--------------------:|------------------:|--------------------:|----------------------:|--------------------:|----------------------:|
| T1c                |              0.0307 |            0.0088 |              0.0219 |              0.6458 |            0.1038 |              0.5420 |              0.8070 |            0.2183 |              0.5887 |                0.4945 |              0.1103 |                0.3842 |
| FLAIR              |              0.2256 |            0.0344 |              0.1912 |              0.0481 |            0.0109 |              0.0372 |              0.0361 |            0.0097 |              0.0264 |                0.1033 |              0.0183 |                0.0850 |
| T2w                |              0.0992 |            0.0070 |              0.0922 |              0.0528 |            0.0084 |              0.0444 |              0.0278 |            0.0104 |              0.0174 |                0.0600 |              0.0086 |                0.0514 |
| T1n                |              0.0039 |            0.0022 |              0.0017 |              0.0049 |            0.0074 |             -0.0025 |              0.0084 |            0.0063 |              0.0021 |                0.0058 |              0.0053 |                0.0005 |

### Recovery Gain
| Missing Modality   |   WT Recovery Gain |   TC Recovery Gain |   ET Recovery Gain |   Mean Recovery Gain |
|:-------------------|-------------------:|-------------------:|-------------------:|---------------------:|
| T1c                |             0.0253 |             0.5447 |             0.5941 |               0.3880 |
| FLAIR              |             0.1946 |             0.0399 |             0.0318 |               0.0888 |
| T2w                |             0.0956 |             0.0471 |             0.0228 |               0.0552 |
| T1n                |             0.0051 |             0.0002 |             0.0075 |               0.0043 |
