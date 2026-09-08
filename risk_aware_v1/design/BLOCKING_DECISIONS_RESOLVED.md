# Blocking Decisions Resolved

状态枚举：RESOLVED / STILL_UNKNOWN / BLOCKED

| 类别/编号 | 原问题 | 来源文件 | 原状态 | 真实代码证据 | 导师决定 | V2 解决方案 | 最终状态 |
|---|---|---|---|---|---|---|---|
| Conflict 1 | build signature 错误 | V1:118；review DC-01 | DESIGN_CONFLICT | `nnUNetTrainer.py:349-354` + inspect | 使用真实父类签名 | 移除 dataset_json，加入 num_output_channels，静态覆写完全兼容 | RESOLVED |
| Conflict 2 | calibration checkpoint 未锁定 | V1:189；review DC-02 | DESIGN_CONFLICT | experiment_paths、A1预测目录、训练日志、checkpoint metadata | 使用 A1正式benchmark同一 best | 锁定完整路径与 SHA `77a325...184b` | RESOLVED |
| Conflict 3 | risk CSV schema 未锁定 | review DC-03 | DESIGN_CONFLICT | 真实 split/checkpoint/provenance 需求 | 锁定 V2 schema | `risk-matrix-v2.0`，12行与14列固定 | RESOLVED |
| Conflict 4 | 样本风险公式缺失 | review DC-04 | DESIGN_CONFLICT | A3/A4需要 sample availability | 使用导师给定 m/s/w/normalize/clamp/re-normalize | V2 第15节完整写入 | RESOLVED |
| Conflict 5 | alpha/clamp/lambda 初值缺失 | review DC-05 | DESIGN_CONFLICT | 原设计仅有部分候选/回退描述 | alpha=1.0，clamp=[.5,1.5]，lambda=.2 | 值和候选全部锁定 | RESOLVED |
| Unknown 1 | 历史 zero-fill 脚本 | V1:76；review U1 | UNKNOWN | 项目搜索未找到 | 不猜测 | V2 wrapper 不依赖历史脚本 | STILL_UNKNOWN |
| Unknown 2 | 历史完整 inference CLI | V1:76；review U2 | UNKNOWN | args JSON不含完整模型命令 | 不猜测 | V2 定义新可审计 wrapper/命令协议 | STILL_UNKNOWN |
| Unknown 3 | alpha 初始值 | review U3 | UNKNOWN | 本轮导师锁定 | 1.0 | 首轮只用1.0 | RESOLVED |
| Unknown 4 | alpha 搜索范围 | review U4 | UNKNOWN | 本轮导师锁定 | `{0.5,1.0,2.0}` | 后续候选，不混入首轮 | RESOLVED |
| Unknown 5 | clamp | review U5 | UNKNOWN | 本轮导师锁定 | `[0.5,1.5]` 后再归一化 | 精确公式写入 | RESOLVED |
| Unknown 6 | lambda 初始值 | review U6 | UNKNOWN | 本轮导师锁定 | 0.2 | 首轮只用0.2 | RESOLVED |
| Unknown 7 | calibration checkpoint | review U7 | UNKNOWN | 四类服务器证据相互一致 | A1 checkpoint_best | 完整路径、SHA、metadata 锁定 | RESOLVED |
| Unknown 8 | risk CSV schema/version | review U8 | UNKNOWN | fold/provenance/hash guards已确认 | 采用 tidy 4×3 schema | `risk-matrix-v2.0` 14列 | RESOLVED |
| Unknown 9 | V1峰值显存/统一推理耗时 | review U9 | UNKNOWN | 项目无准确实测记录 | 不伪造 | 实施后 smoke/benchmark 实测 | STILL_UNKNOWN |
| Mentor 1 | 批准真实 signature 修正 | review M1 | MENTOR_DECISION_REQUIRED | inspect 真实签名 | 批准按真实接口 | V2 方法签名已修正 | RESOLVED |
| Mentor 2 | calibration checkpoint | review M2 | MENTOR_DECISION_REQUIRED | A1 benchmark全链证据 | 使用同一 best checkpoint | 完整路径/SHA锁定 | RESOLVED |
| Mentor 3 | risk CSV schema | review M3 | MENTOR_DECISION_REQUIRED | 必须支持fold/hash/leakage guards | 锁定V2 schema | 12行14列+provenance JSON | RESOLVED |
| Mentor 4 | alpha | review M4 | MENTOR_DECISION_REQUIRED | 本轮明确值 | 1.0；候选集合固定 | 写入loss配置和测试 | RESOLVED |
| Mentor 5 | clamp | review M5 | MENTOR_DECISION_REQUIRED | 本轮明确公式 | `[0.5,1.5]` + 再归一化 | 写入权重函数和测试 | RESOLVED |
| Mentor 6 | lambda | review M6 | MENTOR_DECISION_REQUIRED | 本轮明确值 | 0.2；候选集合固定 | 写入组合loss和测试 | RESOLVED |

## 计数

- Original design conflicts: 5
- Original UNKNOWN items: 9
- Original mentor decisions: 6
- RESOLVED: 17
- STILL_UNKNOWN: 3
- BLOCKED: 0

剩余 UNKNOWN 为历史 provenance 两项及尚未实施所以不存在的实测资源数据，均不是关键接口/超参数/泄漏/兼容性阻塞项。
