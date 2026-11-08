# 回归运行 · workflow-a-01

- 用例：`tests/cases/workflow-a-01.task.md`（L2 级 · 目标 full-team）
- 建议任务 ID：`T-20261015-A01`
- 运行目录：`outputs/regression-20261015/a01`

## 派单步骤（主理人执行）

1. 装配 spawn 文案：
   ```bash
   python3 scripts/assemble_spawn_prompt.py --member <成员> \
     --phase 2 --task-id T-20261015-A01 --task-file tests/cases/workflow-a-01.task.md \
     --run-dir outputs/regression-20261015/a01 --check-task-package \
     --out outputs/regression-20261015/a01/spawn.md
   ```
2. spawn 成员并等待落盘（产出写入 `outputs/regression-20261015/a01/`）
3. 计量：`python3 scripts/token_budget_check.py --meter outputs/regression-20261015/a01 --ledger`
4. 验证：`python3 scripts/run_regression.py --case workflow-a-01 --dir outputs/regression-20261015/a01`

## 断言清单

- [A1] task_package_elements：{"expect": ["objective", "output_format", "constraints", "task_boundary"]}
- [A2] all_members_landed：{"expect": ["contradiction-analyst", "patent-search-scout", "patent-examiner-sim", "second-opinion-reviewer", "disclosure-architect", "patent-attorney-writer"]}
- [A3] gates：{"expect": ["G1", "G2", "G3", "G4", "G5"]}
- [A4] abstract_max_chars：{"max": 300, "note": "机械计量，不得自评"}
- [A5] forbidden_regex：{"patterns": ["大约", "左右", "之类的", "最好", "优选", "若干", "大幅", "显著提高"], "scope": "claims"}
- [A6] budget：{"max_tokens": 120000, "max_wall_min": 45}
