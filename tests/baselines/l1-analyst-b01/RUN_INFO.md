# 回归运行 · workflow-b-01

- 用例：`tests/cases/workflow-b-01.task.md`（L1 级 · 目标 contradiction-analyst）
- 建议任务 ID：`T-20261015-B01`
- 运行目录：`outputs/regression-20261015/b01`

## 派单步骤（主理人执行）

1. 装配 spawn 文案：
   ```bash
   python3 scripts/assemble_spawn_prompt.py --member contradiction-analyst \
     --phase 2 --task-id T-20261015-B01 --task-file tests/cases/workflow-b-01.task.md \
     --run-dir outputs/regression-20261015/b01 --check-task-package \
     --out outputs/regression-20261015/b01/spawn.md
   ```
2. spawn 成员并等待落盘（产出写入 `outputs/regression-20261015/b01/`）
3. 计量：`python3 scripts/token_budget_check.py --meter outputs/regression-20261015/b01 --ledger`
4. 验证：`python3 scripts/run_regression.py --case workflow-b-01 --dir outputs/regression-20261015/b01`

## 断言清单

- [A1] task_package_elements：{"expect": ["objective", "output_format", "constraints", "task_boundary"]}
- [A2] envelope_required_fields：{"expect": ["agent_id", "task_id", "phase", "status", "confidence", "deliverable_summary"]}
- [A3] envelope_agent_id：{"expect": "contradiction-analyst"}
- [A4] min_count：{"field": "directions", "pattern": "原理|IP #|#\\\\d+", "min": 3}
- [A5] forbidden_regex：{"patterns": ["大约", "左右", "之类的", "等等", "最好", "优选", "若干", "高效", "快速", "大幅", "显著提高"], "allow_note": true}
- [A6] required_regex：{"patterns": ["query_triz_matrix", "退出码"], "note": "必须出现查询器命令与退出码，证明原理编号来自实跑而非记忆"}
- [A7] min_chars：{"min": 3000}
- [A8] no_fabrication_marker：{"forbidden": ["矩阵无推荐"], "note": "A8反向：若出现「矩阵无推荐」属诚实降级，不算失败；此处仅登记"}
