# 路由决策日志（R-20260918-001+）

> 2026-09-18 落地路由决策协议后启用。append-only，每次派单一行。
> 字段：decision_id / timestamp / task_type / target_agent / confidence / 一句话理由

| decision_id | timestamp | task_type | target_agent | confidence | 理由 |
|---|---|---|---|---|---|

<!--
模板:
| R-20260918-001 | 2026-09-18T12:00 | stage_transition | patent-examiner-sim | 0.92 | Phase 3 查新R3完成verdict=绿，按SOP路由至Phase 4三性裁决 |

复盘笔记:
- (空格，待第一条决策产生时由主理人按路由协议自动append)
-->