# Risk-aware V1 工程设计 V2

日期：2026-07-27
状态：**DESIGN V2 ONLY — 实施尚未开始**
项目：BraTS 2023 GLI / Dataset501_BraTS2023 / 3d_fullres / fold 0

## 1. V2 修订原因

V1 导师审查发现 5 个设计冲突、9 个 UNKNOWN 和 6 个导师决策项。V2 依据服务器当前安装源码、真实 A1 checkpoint/benchmark 元数据及本轮导师锁定值，修正接口和协议。V2 不修改 V1、审查材料、训练代码、数据、checkpoint 或项目 Markdown。

## 2. V1 审查中的 5 个冲突

1. `build_network_architecture` 签名写错：V1 多写 `dataset_json`、遗漏 `num_output_channels`。
2. calibration checkpoint 未精确锁定。
3. risk matrix CSV 精确 schema 未锁定。
4. `m/s/w/w_norm/w_final` 样本风险权重公式未完整写入。
5. alpha、clamp、lambda 初始值未锁定。

V2 全部修正，逐项证据见 `BLOCKING_DECISIONS_RESOLVED.md`。

## 3. V1 审查中的 9 个 UNKNOWN

1. 历史 Missing T1c zero-fill 创建脚本：仍为 `STILL_UNKNOWN`，不影响 V2 新 wrapper。
2. 历史完整 inference CLI：仍为 `STILL_UNKNOWN`，不影响 V2 新协议。
3. alpha 初始值：已锁定 1.0。
4. alpha 搜索范围：已锁定 `{0.5,1.0,2.0}`。
5. clamp：已锁定两阶段归一化与 `[0.5,1.5]`。
6. lambda 初始值：已锁定 0.2。
7. calibration checkpoint：已由四类证据唯一确认。
8. risk matrix CSV schema/version：V2 已锁定。
9. V1 实测峰值显存和统一推理耗时：仍为 `STILL_UNKNOWN`；实施后 smoke/benchmark 实测，不把理论值冒充实测。

剩余 3 项均为非关键历史/运行测量信息，不阻塞代码实现。

## 4. 6 个导师决策

1. 按真实父类签名修正自定义 Trainer。
2. calibration 使用产生 A1 正式 benchmark 的冻结 `checkpoint_best.pth`。
3. risk matrix 使用 V2 固定 schema/version。
4. alpha 首轮 1.0，候选 `{0.5,1.0,2.0}`。
5. `w_norm` clamp 到 `[0.5,1.5]` 后再次均值归一化。
6. lambda_region 首轮 0.2，候选 `{0.1,0.2,0.5}`。

六项均在 V2 锁定。

## 5. 真实代码接口

真实父类：

`/root/miniconda3/envs/nnunet/lib/python3.10/site-packages/nnunetv2/training/nnUNetTrainer/nnUNetTrainer.py`

```python
class nnUNetTrainer(...):
    def initialize(self)

    @staticmethod
    def build_network_architecture(
        plans_manager: PlansManager,
        configuration_manager: ConfigurationManager,
        num_input_channels: int,
        num_output_channels: int,
        enable_deep_supervision: bool = True,
    ) -> nn.Module

    def _build_loss(self)
    def train_step(self, batch: dict) -> dict
    def validation_step(self, batch: dict) -> dict
```

真实 ModDrop：

```python
class nnUNetTrainerModalityDropout(nnUNetTrainer):
    @staticmethod
    def apply_modality_dropout(
        data: torch.Tensor, probability: float
    ) -> torch.Tensor

    def train_step(self, batch: dict) -> dict
```

真实 predictor：

```python
class nnUNetPredictor:
    def initialize_from_trained_model_folder(
        self, model_training_output_dir: str,
        use_folds: Optional[Tuple[Union[int, str]]],
        checkpoint_name: str = "checkpoint_final.pth"
    )
    def predict_logits_from_preprocessed_data(
        self, data: torch.Tensor
    ) -> torch.Tensor
    def predict_sliding_window_return_logits(
        self, input_image: torch.Tensor
    ) -> Union[np.ndarray, torch.Tensor]
    def _internal_predict_sliding_window_return_logits(
        self, data: torch.Tensor, slicers,
        do_on_device: bool = True
    )
    def _internal_maybe_mirror_and_predict(
        self, x: torch.Tensor
    ) -> torch.Tensor
```

完整文件和 inspect 行号见 `source_code_evidence.txt`。

## 6. 修正后的 availability mask 注入路径

固定顺序：

`a=[a_T1n,a_T1c,a_T2w,a_FLAIR]`

- Full `[1,1,1,1]`
- Missing T1c `[1,0,1,1]`

训练真实调用链：

```text
dataset
→ nnUNetDataLoader + existing augmentation
→ batch {"data","target"}
→ custom train_step
→ data.to(device)
→ apply_modality_dropout_with_availability
→ (zero-filled MRI, availability)
→ broadcast_and_concatenate_availability
→ network(8-channel tensor)
```

当前 ModDrop 已在 `train_step` 中、GPU 上、augmentation 后执行。V2 仅在新 Trainer 中最小覆写 `train_step`；公共函数一次返回 MRI 与 availability，禁止独立二次采样。

断言：

- MRI `[B,4,D,H,W]`，availability `[B,4]`，拼接后 `[B,8,D,H,W]`；
- availability 只含 0/1，首轮每行 sum 为 3 或 4；
- 每个 `a[b,k]==0` 的 MRI channel 必须全零；
- dropout 返回的 channel index 与 availability=0 一一相同；
- 不从 MRI 是否全零反推 availability。

mask 在 augmentation 后创建，不经过 normalization、noise、brightness、gamma、contrast、blur。它不进入现有 augmentation pipeline；常量值在 crop/rotation/mirror 下理论不变。

## 7. Train / validation / inference 协议

### Train

随机 ModDrop：每 sample 以 0.5 概率触发，触发后均匀缺一个 modality；未触发为 Full。A2/A4 拼接 mask；A3 只把 availability 交给 loss。

### Internal validation

新 Trainer 的 `validation_step(self,batch:dict)->dict` 使用 Full input：

`availability=[1,1,1,1]`

不执行随机 dropout。在线 validation 只用于相同 full-input checkpoint 选择规则。Full 与四种 single-missing 正式结果在训练后由独立 benchmark 生成。

### Inference

新建 `RiskAwareNNUNetPredictor(nnUNetPredictor)` 和 prediction wrapper：

```text
4 MRI modalities
→ existing Dataset501 preprocessing
→ wrapper 根据显式 condition 在预处理 tensor 中置零缺失 channel
→ set_availability_vector(condition)
→ predict_sliding_window_return_logits([4,x,y,z])
→ pad 4-channel MRI
→ 在 padded spatial shape 广播 4 mask channels
→ concatenate to [8,xp,yp,zp]
→ generate slicers
→ inherited internal sliding-window + TTA
→ crop logits back
```

准确覆写入口：

`RiskAwareNNUNetPredictor.predict_sliding_window_return_logits(self,input_image)`

它保留父类签名；availability 由 wrapper 在调用前通过 `set_availability_vector` 显式设置。拼接发生在 sliding-window 切 patch 前，所以每个 patch 自动获得对应 4 个常量 mask channel；TTA mirror 不改变常量值；network 实际收到 `[B,8,D,H,W]`。

禁止写 mask NIfTI、重跑 preprocessing、让 mask 进入 normalization、从零值自动猜 condition。

## 8. A3 特殊数据流

A3 是 `ModDrop + Risk-weighted Region Loss`，但 network 始终 4 channel：

```text
augmented MRI
→ apply_modality_dropout_with_availability
→ zero-filled MRI [B,4,...] → 4-channel network
→ availability [B,4] → sample risk weights → auxiliary loss
```

availability 来自同一个 ModDrop sampler，只用于 loss，不拼接。A3 推理没有训练 loss，使用现有 zero-filled 4-channel missing protocol 和标准 `nnUNetPredictor`，不需要 availability vector。

## 9. 8 通道网络构建方式

A2/A4 的新 Trainer 覆写：

```python
@staticmethod
def build_network_architecture(
    plans_manager: PlansManager,
    configuration_manager: ConfigurationManager,
    num_input_channels: int,
    num_output_channels: int,
    enable_deep_supervision: bool = True,
) -> nn.Module:
    assert num_input_channels == 4
    return nnUNetTrainer.build_network_architecture(
        plans_manager,
        configuration_manager,
        8,
        num_output_channels,
        enable_deep_supervision,
    )
```

真实 `initialize` 先由 Dataset501 得到 `num_input_channels=4`，再调用上述方法。backbone、output heads、初始化协议、patch、batch 均不变。

真实首层为 Conv3d `[out=32,in=4,k=3³]`；8-channel 新增：

`(8-4)×32×3×3×3 = 3,456` 参数。

## 10. Checkpoint 兼容性

- A2/A4 从新的随机初始化 8-channel network 训练；
- 不加载 A1 的 4-channel network weights；
- 不忽略 shape mismatch；
- 不做第一层权重迁移；
- 保存到各自独立 Trainer 目录；
- predictor 从新 checkpoint 的 `trainer_name` 找到相同 8-channel build override，并 strict load。

A1 calibration checkpoint 只用于离线生成 R，不作为 A2/A4 初始化：

`/root/autodl-tmp/nnunet_brats/nnUNet_results/Dataset501_BraTS2023/nnUNetTrainerModalityDropout__nnUNetPlans__3d_fullres/fold_0/checkpoint_best.pth`

SHA256：

`77a3257fe0e75ac4256843ea9aced954a2db11f4ce2d18e07efafcaf29fa184b`

元数据：Trainer=`nnUNetTrainerModalityDropout`，configuration=`3d_fullres`，fold=0，current_epoch=955，首个 5D 权重 shape=`[32,4,3,3,3]`。

## 11. Region loss 最终公式

`L_total = L_base + lambda_region × L_region`

`L_base` 保持 nnU-Net `DC_and_CE_loss`（CE 1、Dice 1、smooth `1e-5`、`batch_dice=false`、`do_bg=false`）。

softmax 沿 class channel `dim=1`：

- `P_WT=P1+P2+P3`
- `P_TC=P1+P3`
- `P_ET=P3`
- `Y_WT=1[y∈{1,2,3}]`
- `Y_TC=1[y∈{1,3}]`
- `Y_ET=1[y=3]`

逐样本、逐区域：

`D_br=(2ΣP_brY_br+ε)/(ΣP_br+ΣY_br+ε)`，`ε=1e-5`

`L_br=1-D_br`

不平方、不含 background、不先 batch 聚合。

`L_region,b=(w_final_b,WT L_b,WT + w_final_b,TC L_b,TC + w_final_b,ET L_b,ET)/3`

`L_region=mean_b(L_region,b)`

第一轮 `lambda_region=0.2`；后续候选 `{0.1,0.2,0.5}`，不得在第一轮混用。

每 batch rank 0 记录 JSONL：epoch、iteration、`L_base/L_WT/L_TC/L_ET/L_region/L_total/w_WT/w_TC/w_ET`、availability pattern、finite flags。NaN/Inf 立即抛错停止。如果一个完整 epoch 都满足 `lambda_region×L_region > max(abs(L_base),1e-6)`，停止并按固定回退检查，不继续训练。

## 12. 空区域最终行为

唯一方案：

- GT 非空：正常 soft Dice。
- GT 空且 `ΣP=0`：`D=ε/ε=1`，loss=0。
- GT 空但预测非空：`D=ε/(ΣP+ε)<1`，loss 为有限正数。
- GT 空、预测概率和接近 0：loss 接近 0。
- ET-empty patch 不跳过，不用 valid-region mask。
- 每个样本先得到 WT/TC/ET loss，再用该样本权重，最后 batch mean。
- denominator 使用 `clamp_min(1e-8)`，所有中间量和最终 loss 用 `isfinite` 断言。

因此不会把“空 GT 但错误预测”当 perfect Dice，且 smooth 消除 0/0。

## 13. Deep supervision 最终方案

真实 target 在 deep supervision 开启时是 5 元素 list，尺度：

`[1,1/2,1/4,1/8,1/16]`

现有 `DownsampleSegForDSTransform` 已以 `nearest-exact` 生成对应尺度 label map。V2：

- 直接使用 `target[j]`，不重复下采样；
- 每尺度计算 `L_base[j]`；
- 每个有效尺度从 `target[j]` 构造 region targets 并算 `L_region[j]`；
- 沿用真实非 DDP权重 `[0.533333,0.266667,0.133333,0.066667,0]`；
- 最低尺度权重 0，不产生有效 region contribution；
- `L_total=Σ_j q_j L_base[j] + lambda×Σ_j q_j L_region[j]`。

组合类 `RiskAwareDeepSupervisionLoss.forward(outputs,targets,availability)` 统一完成，不把已下采样 target 再插值。

## 14. Risk matrix calibration

数据仅为 fold 0 的 1000 training cases；禁止 251 validation cases。冻结 A1 checkpoint 如第 10 节。

对 Full、Missing T1n/T1c/T2w/FLAIR：

`risk_raw(m,r)=mean_i max(0,Dice_full(i,r)-Dice_missing_m(i,r))`

`risk_norm(m,r)=risk_raw(m,r)/max_r risk_raw(m,r)`

若一行最大值为 0，则该行全部 0 并记录。

固定 CSV schema `risk-matrix-v2.0`，每行一个 modality-region：

```text
schema_version,fold,modality_index,modality,region,
risk_raw,risk_norm,n_cases,source_scope,
checkpoint_path,checkpoint_sha256,
split_sha256,case_manifest_sha256,created_at_utc
```

固定 4×3=12 行；`source_scope=fold0_training_only`；另存 case manifest 和 provenance JSON。加载器断言 fold=0、n_cases=1000、12行、hash 一致、无 validation case、`risk_norm∈[0,1]`。

R 训练前固定为 buffer：`requires_grad=False`、detach、不更新、不按 validation 重算。训练过这些病例的 baseline 可能使风险绝对值偏乐观、动态范围压缩或改变相对排序，这是 V1 限制，不改用 validation。

## 15. Alpha、lambda、clamp 固定值

对每 sample：

`m_k=1-a_k`

`s_r=Σ_k m_kR[k,r]`

`w_r=1+alpha×s_r`

`w_norm_r=3w_r/Σ_rw_r`

`w_clip_r=clamp(w_norm_r,0.5,1.5)`

`w_final_r=3w_clip_r/Σ_rw_clip_r`

Full 时 `m=0`，严格得到 `[1,1,1]`。Missing T1c 使用 R 的 T1c 行。R、m 和权重均 detach，不参与反向传播。

- 第一轮 alpha=`1.0`；后续候选 `{0.5,1.0,2.0}`。
- 第一轮 lambda_region=`0.2`；后续候选 `{0.1,0.2,0.5}`。
- clamp 固定 `[0.5,1.5]`，clamp 后再次均值归一化。

## 16. A0–A4 消融

| ID | 输入 | ModDrop | mask入网 | region loss/R | Trainer | 首轮是否训练 | 推理 |
|---|---:|---|---|---|---|---|---|
| A0 Full-only | 4 | 否 | 否 | 否 | `nnUNetTrainer` | 复用正式 baseline | 标准 predictor |
| A1 ModDrop | 4 | 是 | 否 | 否 | `nnUNetTrainerModalityDropout` | 复用正式 baseline | 标准 predictor |
| A2 ModDrop+Mask | 8 | 是 | 是 | 否 | `nnUNetTrainerModDropAvailabilityMask` | 新训练 | risk-aware predictor |
| A3 ModDrop+Risk | 4 | 是 | 否 | 是 | `nnUNetTrainerModDropRiskRegion` | 新训练 | 标准 predictor |
| A4 Full V1 | 8 | 是 | 是 | 是 | `nnUNetTrainerRiskAwareV1` | 新训练 | risk-aware predictor |

保持相同 fold、backbone、patch、batch、epochs、optimizer、LR、augmentation、checkpoint 选择、missing protocol 和逐病例评估。输出目录由 Trainer 名隔离。

## 17. 预注册成功标准

A4 相对 A1，fold 0 第一轮：

- Missing T1c ET：至少 `+0.020` absolute Dice。
- Missing T1c TC：下降不超过 `0.005`。
- Missing T1c Mean：至少 `+0.010`。
- Full Mean：下降不超过 `0.005`。
- Missing T1n/T2w/FLAIR：每一种 Mean 下降均不超过 `0.010`。
- 无 NaN/Inf；checkpoint save/load 正常；sliding-window 正常；mask 与缺失一致。
- 报告均值与逐病例分布/差值，不能只挑病例。

仅为 fold 0 工程成功信号，不宣称显著性、SOTA 或最终论文结论。

## 18. 文件实施计划

未来新建：

- `risk_aware_v1_impl/risk_aware/availability.py`
- `risk_aware_v1_impl/risk_aware/region_loss.py`
- `risk_aware_v1_impl/risk_aware/risk_matrix.py`
- `risk_aware_v1_impl/risk_aware/predictor.py`
- `risk_aware_v1_impl/nnunetv2_ext/training/nnUNetTrainer/nnUNetTrainerModDropAvailabilityMask.py`
- `risk_aware_v1_impl/nnunetv2_ext/training/nnUNetTrainer/nnUNetTrainerModDropRiskRegion.py`
- `risk_aware_v1_impl/nnunetv2_ext/training/nnUNetTrainer/nnUNetTrainerRiskAwareV1.py`
- `risk_aware_v1_impl/scripts/calibrate_training_only_risk.py`
- `risk_aware_v1_impl/scripts/train_ablation_fold0.sh`
- `risk_aware_v1_impl/scripts/predict_ablation_fold0.py`
- `risk_aware_v1_impl/tests/test_availability.py`
- `risk_aware_v1_impl/tests/test_region_loss.py`
- `risk_aware_v1_impl/tests/test_deep_supervision.py`
- `risk_aware_v1_impl/tests/test_checkpoint_and_predictor.py`
- `risk_aware_v1_impl/tests/smoke_gpu_batch.py`
- `risk_aware_v1_impl/tests/smoke_inference_case.py`

不修改现有 ModDrop、site-packages、Dataset501、checkpoint、项目 Markdown。使用 `nnUNet_extTrainer` 与 `PYTHONPATH` 外部发现。

## 19. 单元测试顺序

1. availability 顺序/Full/T1c。
2. 同一 sampler 的置零-mask一致性。
3. batch 内独立 pattern。
4. 4→8 shape。
5. augmentation 后 mask 常量性。
6. WT/TC/ET target。
7. empty region 数学测试。
8. risk matrix schema/hash/leakage guards。
9. Full/Missing T1c weight 与 clamp/再归一化。
10. alpha/lambda 锁定值。
11. 5尺度 target list 与权重。
12. finite forward。
13. backward；R 无梯度。
14. 4/8-channel checkpoint incompatibility guard。
15. A2/A4 8-channel save/strict load。
16. sliding-window pad-before-mask。
17. mirror/TTA 常量 mask。
18. 单 GPU batch smoke；异常立即停止。
19. 单 validation case inference smoke；禁止批量扩展。

测试 1–17 全 PASS 后才能执行 18，18 PASS 后才能执行 19；本阶段均未执行。

## 20. 当前仍不实施代码

V2 设计和关键接口已达到实施准备条件，第 25 项可标记 PASS。但“准备就绪”不授权实现：本阶段没有创建 Trainer、没有修改 Python、没有训练、推理或 calibration。下一阶段须由用户单独授权。
