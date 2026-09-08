# Implementation Readiness Checklist V2

状态枚举：PASS / FAIL / UNKNOWN / MENTOR_DECISION_REQUIRED

| # | 检查项 | 状态 | V2 证据 |
|---:|---|---|---|
| 1 | ModDrop dropout 顺序已确认 | PASS | GPU、augmentation后、forward前 |
| 2 | ModDrop 粒度已确认 | PASS | batch内逐sample独立 |
| 3 | availability vector 来源已确认 | PASS | 同一sampler返回MRI与availability |
| 4 | 8通道注入位置已确认 | PASS | 新train/validation step中forward前 |
| 5 | augmentation 不污染 mask | PASS | augmentation后创建，不进intensity transforms |
| 6 | validation mask 路径已确认 | PASS | Full `[1,1,1,1]`，无随机dropout |
| 7 | inference mask 路径已确认 | PASS | custom predictor在MRI padding后、切patch前拼接 |
| 8 | sliding-window兼容 | PASS | slicer包含全部8通道 |
| 9 | mirroring/TTA兼容 | PASS | 常量mask flip后值不变 |
| 10 | checkpoint save/load明确 | PASS | A2/A4新初始化、独立目录、8通道strict load |
| 11 | base loss调用位置已确认 | PASS | composite loss保留真实DC_and_CE |
| 12 | deep supervision输出结构已确认 | PASS | 5尺度target/output list |
| 13 | region target方案明确 | PASS | 直接使用nearest-exact现有target[j] |
| 14 | 空ET行为明确 | PASS | 不跳过；空/空0，空/错预测正惩罚 |
| 15 | region loss reduction明确 | PASS | per-sample→risk weight→batch mean→DS sum |
| 16 | risk matrix无validation泄漏 | PASS | fold0 1000 train only + ID/hash guards |
| 17 | training-only calibration明确 | PASS | checkpoint路径/SHA/schema/provenance锁定 |
| 18 | A0–A4公平条件明确 | PASS | 训练与推理协议统一 |
| 19 | 成功阈值已预注册 | PASS | 本轮导师新阈值全部写入 |
| 20 | OOM回退明确 | PASS | 真实OOM后所有公平组统一batch |
| 21 | 新文件不覆盖baseline | PASS | 独立Trainer名和目录 |
| 22 | 单元测试顺序明确 | PASS | 19步依赖顺序 |
| 23 | GPU smoke终止条件明确 | PASS | 前置测试全PASS；任一异常停止 |
| 24 | 无需先修改原始数据 | PASS | 不重预处理、不写mask NIfTI |
| 25 | 当前可以进入代码实现 | PASS | 所有关键接口/参数/checkpoint/隔离项均已解决；仍需下一阶段单独授权 |

## 第 25 项结论

PASS

剩余 3 个非关键 UNKNOWN（历史 zero-fill 脚本、历史完整 CLI、尚未实施的实测资源数据）不影响实现接口、安全或实验预注册。PASS 仅表示设计准备完成，不表示本阶段已授权或已开始实现。
