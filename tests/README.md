# 回归测试集（tests/）

> P2-9 建立（2026-10-15）。定位：把「改完不敢用」变成「数据说话」——
> 每次改动后复跑固定用例，断言通过率、成本、耗时三项可对比。

## 结构

```
tests/
└── cases/
    ├── workflow-a-01.task.md      # L2 全链路用例（发明想法→申请文件草稿）
    ├── workflow-a-01.expected.json
    ├── workflow-b-01.task.md      # L1 单成员用例（analyst·TRIZ矛盾建模）
    ├── workflow-b-01.expected.json
    ├── workflow-c-01.task.md      # L1 单成员用例（scout·三轮查新）
    └── workflow-c-01.expected.json
```

- `*.task.md`：固定任务包（作为 spawn 的 `--task-file`，四要素齐全）
- `*.expected.json`：断言清单（`assertions[]`，逐条由 `scripts/run_regression.py` 求值）

## 分级与触发时机

| 级别 | 用例 | 覆盖 | 成本 | 何时跑 |
|---|---|---|---|---|
| **L1** | workflow-b-01 / workflow-c-01 | 单成员（analyst / scout） | 分钟级 | 日常改动后 |
| **L2** | workflow-a-01 | 全链路 6 成员 + G1-G5 门禁 | ~45min | **版本发布前**（人工触发） |

## 三步使用

```bash
# 1. 准备运行目录（生成 RUN_INFO.md，含派单指令与断言清单）
python3 scripts/run_regression.py --case workflow-b-01 --scaffold
#    同日多用例请各自 --out 子目录（防不同用例的成员落盘文件互相干扰）
python3 scripts/run_regression.py --case workflow-a-01 --scaffold --out outputs/regression-<date>/a01

# 2. 按 RUN_INFO.md 派单（主理人手工 spawn 成员，产出落盘到运行目录）

# 3. 验证 + 计量
python3 scripts/token_budget_check.py --meter outputs/regression-<date> --ledger
python3 scripts/run_regression.py --case workflow-b-01 --dir outputs/regression-<date>
```

退出码：`0`=全过 · `1`=有 FAIL · `2`=用法错误。报告自动落盘
`outputs/<run>/regression_report__<case>.json`（可跨轮对比）。

## 断言类型速查

| type | 检查内容 |
|---|---|
| `task_package_elements` | 任务包四要素（objective/output_format/constraints/task_boundary）齐全 |
| `envelope_required_fields` | 产出首个 JSON 信封含 6 必填（栈平衡提取，防嵌套误判） |
| `envelope_agent_id` | 信封 agent_id 与成员一致 |
| `min_count` | 某字段计数下限（如 directions ≥3、search_rounds ≥3） |
| `forbidden_regex` | 模糊词零命中（自动剔除围栏代码块与自检清单行，防 failure-006 假阳性） |
| `required_regex` | 必现串（如 `query_triz_matrix` + `退出码`，证明原理编号来自实跑） |
| `min_chars` | 产出规模下限 |
| `all_members_landed` | L2：6 成员全部落盘 |
| `gates` | L2：`_VERIFY.md` 登记 G1-G5 |
| `abstract_max_chars` | 撰写员摘要机械计量 ≤300 字（不得自评） |
| `budget` | 汇总 metrics.jsonl：token ≤120K、墙钟 ≤45min |
| `no_fabrication_marker` | 信息性：统计「矩阵无推荐」等诚实降级标记（不判失败） |
| `conditions_closed` | J2（v2.6.0）：二审条件清单逐条兑现对账——state.json conditions 键优先，回退为二审产出提取 K*/M* 编号扫下游命中 |

## 已知边界

- **禁用词表含「快速/高效」**：意图是逼出量化表述。若确需标准件名（如"快速接头"），
  改写为结构性名称（如"卡扣式接头"）保持产出干净——这是刻意设计，非缺陷。
- **runner 不 spawn**：断言引擎只做确定性校验；派单仍是主理人职责。
- **L2 默认不进 CI**：成本高，仅版本发布前人工触发。
- **metrics 缺省**：未跑 `--meter` 时 `budget` 断言记 SKIP（不判失败），其余照常。

## 历史基线（已归档）

- **2026-09-11 · T1-T7 生产就绪测试**（v2.2.0）：兼容性/边界角色/异常路径/并发/幂等/资源限制/恢复性 7 维全 PASS。
  记录原文见 git 历史 `docs/test-matrix.md`（已于 v2.5.1 合并归档，不再独立维护）。
- **2026-10-14 · P0-2 定向回归**：装配链（shared-core 下沉后）+ 双轨制指标 + 门禁四要素校验全通过（产出见
  `outputs/regression-20261014/`）。
- **2026-10-15 · L1 首跑（b-01）**：7/8 PASS；发现 3 处契约一致性缺陷（failure-008）已修复。
  **2026-10-15 · L1 重跑（b-01）**：7/8 PASS（1 INFO），机械计量 20,018 字符 / ≈10.8k tokens / 321s。
