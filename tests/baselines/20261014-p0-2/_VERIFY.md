# 主理人 VERIFY 记录 · T-20261014-013（P0-2 定向回归）

## 结论：✅ PASS（无回归）

## 验证项与实测结果

| 验证项 | 方法 | 结果 |
|---|---|---|
| 装配链可用（shared-core 下沉后） | `assemble_spawn_prompt.py --check-task-package` | ✅ 四要素齐全，装配 10397 字符，skills=['triz-matrix'] |
| 任务包门禁 | 故意缺 output_format/task_boundary 先跑一次 | ✅ exit 4 正确拦截（门禁未失效） |
| 成员人设注入 | 6 成员 `--member` md5 新旧逐一比对 | ✅ 6/6 完全一致（6920–9157 chars） |
| 实际派单执行 | spawn contradiction-analyst，肉鸡舍地暖同域任务 | ✅ success / confidence 78 |
| 落盘通道 | outputs/regression-20261014/T-...-013__contradiction-analyst.md | ✅ 34591 chars |
| 信封完整性 | 正则提取首个 json 块 + JSON 解析 | ✅ 可解析，6 必填字段齐全 |
| 双轨制新字段 | metrics 实际内容 | ✅ `{"duration_ms": 0, "retry_count": 1}`；issues 含「耗时无法自估」 |
| 输出契约 | directions ≥3 且标注原理编号 | ✅ 6 个方向全部标注 |
| 防幻觉 | 矩阵查询实跑 | ✅ 22 组查询，21 组 exit 0，1 组（#17↔#17）exit 1 如实登记「矩阵无推荐」未编造 |
| 路由落盘 | docs/routing-log.md | ✅ R-20261014-013 已 append |

## 耗时双轨回填（H5 新规）

```json
{
  "agent_id": "contradiction-analyst",
  "task_id": "T-20261014-013",
  "metrics": {
    "duration_ms": 0,
    "duration_ms_wall": 1077000,
    "duration_source": "self_report"
  }
}
```

- **自报 0 + issues 注明「耗时无法自估」→ 判为「未自报」**（非失真，走豁免分支）
- 汇总指标取 `duration_ms_wall` = 1077s
- ⚠️ 测量口径说明：本次墙钟由主理人手工打点（`date +%s`），含主理人侧读文件与组装开销，
  并非纯 spawn→回传。后续应脚本化打点（见 P1 待办）。

## 回归实测顺带发现并已修复的两个真实缺陷

1. **failure-007（权威数据表错位）**：39 参数中文表 #34/#35 译名错填为 #36/#37 的译名，
   且 `query_triz_matrix.py` 会把译名拼进输出 → 错误直接注入成员上下文。
   已修正译名 + 新增 `scripts/verify_triz_data.py`（A/B/C/D 四类不变量，实测全通过）+ 入失败索引。
2. **失真规则假阳性**：原规则把「自报 0 + 注明无法自估」判为失真（|0−wall|/wall = 1.0）。
   惩罚诚实行为会逼出编造数字 → 已在 H5 增加豁免分支，判定前先做豁免检查。

## 与 2026-09-30 基线的差异

- 链路侧：装配脚本由包内 369 行实现改为 shared-core shim，输出等价（6/6 md5 一致）
- 协议侧：新增 duration_ms_wall / duration_source 两个可选字段，向后兼容
- 质量侧：本次成员 confidence 78（success），未触发门禁违规，无需 retry
