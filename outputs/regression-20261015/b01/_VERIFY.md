# 主理人 VERIFY 记录 · workflow-b-01（L1回归 · T-20261015-B01）

## 结论：✅ PASS（7/8 断言通过，1 INFO）

## 运行事实（可机械复核）

| 项 | 值 | 证据 |
|---|---|---|
| 派单时刻（装配完成） | 08:07:50 | spawn 文件 mtime |
| 落盘时刻 | 08:13:16 | 产出文件 mtime |
| 墙钟（lead_measured） | 321,000 ms | 已回填信封 metrics.duration_ms_wall |
| 产出规模（机械计量·终态） | 20,018 字符 / ≈11.9k out-tokens | token_budget_check.py --meter --ledger（最新一行） |
| 成员自评 | status=success, confidence=88 | 信封 |
| 矩阵查询 | 全部实跑（见产出§8） | required_regex「query_triz_matrix」「退出码」命中 |

## 断言明细（run_regression.py --case workflow-b-01）

| ID | 断言 | 结果 |
|---|---|---|
| A1 | 任务包四要素 | ✅ |
| A2 | 信封 6 必填齐全 | ✅ |
| A3 | agent_id 正确 | ✅ |
| A4 | directions ≥3 | ✅（命中 70 处） |
| A5 | 模糊词零命中 | ✅ |
| A6 | 必需串（查询器+退出码） | ✅ |
| A7 | 产出 ≥3000 字符 | ✅（16,029） |
| A8 | 诚实降级标记（信息性） | ℹ️ 3 处 |

## 本轮发现并修复的基建缺陷（3处 · failure-008）

1. **scaffold 生成违约 task_id**：首跑用 `T-20261015-REG-B01`（第三段含连字符），违反 envelope schema → 无法被 meter 计量。**修复**：scaffold 改为合规 ID + 读 schema 自校验，违约 exit 2。
2. **agent_ci_gate.py 重复 `extract_envelopes` 定义**（死代码 1505 字符）。**修复**：删除死代码，保留版加来源注释；`--self-test` 复验通过。
3. **token_budget_check.py FILENAME_RE 过窄**（仅 `\d{3}`，比 schema 契约更窄 → B01 式 ID 静默跳过）。**修复**：放宽为与 schema 对齐的 `[A-Za-z0-9]{1,8}`。

首跑产物归档于 `../_pre-fix-b01/`（含说明 NOTE.md）。

## 过程说明（透明性登记）

- 成员在报告后对其产出做了一次**终态合并重写**（08:14:35）。主理人首次复验（08:14:0x）恰好读到重写中的中间态，
  输出 2 处假 FAIL（信封字段缺失）——文件稳定后（cksum 两次一致）复验为 7/8 PASS。**非真实回归。**
- 墙钟口径：spawn 发出 → 产出文件落地（321s）。与平台计时（spawn→完成通知 6m29s）的差异在于
  成员落地文件后仍需生成回传报告；本表采用前者（口径已在 metrics.duration_source=lead_measured 标注）。
