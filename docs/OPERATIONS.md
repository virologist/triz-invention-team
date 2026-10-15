# Expert Package Operations Playbook

> 跨会话/平台时序问题的可观测性补全 + 日常运维速查。
> 恢复playbook 直接解决 FAIL-005「silent file loss」模式；工具清单随 v2.5.x 更新。

## 一、症状→处置速查

| 症状 | 处置 |
|---|---|
| `validate_expert.py` 报 `Team type must have settings.json` | 见下方「恢复playbook」 |
| `assemble_spawn_prompt.py --list-members` 退出码 3 | shared-core 不可达 → 检查 `vendor/shared-core/` 兜底是否存在（`tests/test_vendor_core.py` 可自检） |
| `token_budget_check.py --meter` 输出 0 行 | 落盘文件 task_id 不符合 `T-YYYYMMDD-{NNN或字母数字}` 契约 → 见 failure-008 |
| 回归断言 FAIL 但成员自评 success | 先核对文件是否仍在写入（cksum 两次一致性），再查 `regression_report__*.json` 明细 |

## 二、恢复playbook（settings.json 跨会话丢失 · 30秒）

```bash
cd ~/.workbuddy/plugins/marketplaces/my-experts/plugins/triz-invention-team
# 1) 重建 settings.json（内容固定不变）
printf '{\n  "agent": "triz-invention-team-team-lead"\n}\n' > settings.json
# 2) 恢复 .created-by-session（用最近一次的 session-id）
echo "<session-id>" > .created-by-session
# 3) 验证 + 注册
python3 ~/.workbuddy/plugins/cache/workbuddy-builtin/skill-expert-manager/0.1.0/scripts/validate_expert.py .
python3 ~/.workbuddy/plugins/cache/workbuddy-builtin/skill-expert-manager/0.1.0/scripts/register_expert.py . --session-id <session-id>
```

## 三、工具清单（v2.5.1 · 8 个脚本）

| 脚本 | 用途 | 何时跑 |
|---|---|---|
| `scripts/preflight_check.py` | 建队前 7 项检查（失败索引/路由可写/预算/Phase0五参数/权威数据/装配器/skills路径） | **每次建队前（强制）** |
| `scripts/assemble_spawn_prompt.py` | spawn 文案装配（shared-core shim + vendor 兜底） | 每次派单（强制） |
| `scripts/failure_memory.py` | 失败记忆摘要注入（按成员/关键词筛 expert-failures） | 每次派单第2步（强制） |
| `scripts/token_budget_check.py` | 预算估算（默认）/ 产出机械计量（`--meter --ledger`） | 建队前 + 每次交付后 |
| `scripts/query_triz_matrix.py` | 矛盾矩阵确定性查询（1521 交叉点） | 成员按需（analyst/examiner/reviewer） |
| `scripts/verify_triz_data.py` | 权威数据自检（A/B/C/D 四类不变量） | preflight 内自动 + 改数据后 |
| `scripts/run_regression.py` | 回归测试集执行（--list/--scaffold/--case X --dir） | L1：日常改动后；L2：发布前 |
| `scripts/agent_ci_gate.py` | 信封 schema 门禁（`--strict` / `--self-test`） | pre-commit 钩子内自动 + push 门禁 |

## 四、Git 钩子（双层门禁）

`~/.workbuddy/git-hooks/` 经 `core.hooksPath` 挂载到 6 个自建包：

| 钩子 | 时机 | 内容 |
|---|---|---|
| `pre-commit` | commit 前 | ①`agent_ci_gate --strict` ②`scripts/*.py` 语法 ③装配链冒烟 ④契约门禁（touches 成员产物→`contract_enforce`，P0-S1-1）；失败阻断（`--no-verify` 可绕过） |
| `post-commit` | commit 后 | 领先 origin 时提示 `release-sync.sh`（不阻断） |
| （push级） | `release-sync.sh --confirm` 前 | `run_gates` 三闸：agent_ci_gate / verify_triz_data / preflight；`RELEASE_SYNC_SKIP_GATE=1` 逃生阀（留痕） |

## 五、回归测试（v2.5.0+）

- 用例：`tests/cases/`（workflow-a-01 L2 全链路 / b-01 analyst L1 / c-01 scout L1）
- 用法与断言表：`tests/README.md`
- 运行产物落 `outputs/regression-<date>/<case>/`（含 `_VERIFY.md` + `metrics.jsonl` + `regression_report__*.json`）

## 六、验证清单（5条全过才算系统可加载）

1. `python3 scripts/agent_ci_gate.py --results-dir outputs/ --self-test` → 合规样本通过
2. `python3 scripts/verify_triz_data.py --strict` → 全通过
3. `python3 tests/test_vendor_core.py` → V1-V6 全 PASS
4. `git status` → working tree clean
5. `validate_expert.py` + `register_expert.py` → 通过

## 七、相关 failure 索引

- failure-005（settings.json 跨会话丢失）
- failure-006（自评失真→机械计量）、failure-007（权威数据错位）、failure-008（task_id 契约漂移）
- 完整索引：`~/.workbuddy/expert-failures/index.md`
