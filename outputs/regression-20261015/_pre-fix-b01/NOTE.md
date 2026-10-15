# 预修复归档 · b-01 首跑（2026-10-15 08:0x）

本目录是 workflow-b-01 的首次 L1 运行产物，**task_id 使用违约束格式**
`T-20261015-REG-B01`（第三段含连字符），违反 result_envelope.schema.json 的
`^T-[0-9]{8}-[A-Za-z0-9]{1,8}$` 契约 → 该次产出无法被 `token_budget_check.py --meter`
机械计量（静默跳过）。

## 该次运行的价值（非白跑）
成员自身发现并上报了 2 个真实基建缺陷（见其产出 issues 段）：
1. task_id 格式与 schema 冲突（本归档的根因）
2. `agent_ci_gate.py` 存在重复 `extract_envelopes` 定义（死代码）

叠加主理人验证时发现的第 3 个缺陷：
3. `token_budget_check.py` 的 FILENAME_RE 只接受 `\d{3}` 数字后缀，比 schema 更窄
   （合法 B01 式 ID 会被静默跳过）

三处均已修复（见 v2.5.1 CHANGELOG），并用合规 ID（T-20261015-B01）重跑，产出在 `b01/`。
