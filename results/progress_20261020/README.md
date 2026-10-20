# 2026-10-20 进度证据包

本目录来自只读云审计快照，不是新实验。B1–B4 summary、teacher qualification summary、projector summary/freeze 为源 JSON 的结构化副本；重新序列化后字节不保证相同。provenance.json 同时记录源 SHA256 和本地导出 SHA256。

- `B1_B4_all_conditions.csv`：4 模型×5 条件完整指标；空的 B0 差值表示无对应归档，不补零。
- `csv_structure_checks.json`：逐病例文件的行数、唯一性及数值检查；不包含原始逐病例 CSV。
- `cloud_audit_summary.json`：云文件审计范围及冻结引用检查汇总。
- `b*_inner_calibration_summary.json`：checkpoint、内部 epoch、指标及归档配对区间。
- `projector_summary.json` / `projector_freeze.json`：投影审计结果及冻结信息。
- `teacher_qualification_summary.json`：B0/教师候选的原归档统计。

完整医学数据、checkpoint 和逐病例 CSV 仍在云端；路径在 provenance 与核验文件中。这里未重新复算 Dice/bootstrap，不能冒充逐病例完整归档。
