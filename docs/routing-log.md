# 路由决策日志（R-20260930-001+）

> 2026-09-18 落地路由决策协议；2026-09-30 首批真实记录（含补记：协议上线当日派单未落盘，教训已入 learned_rule）。append-only，每次派单一行。
> 字段：decision_id / timestamp / task_type / target_agent / confidence / 理由

| decision_id | timestamp | task_type | target_agent | confidence | 理由 |
|---|---|---|---|---|---|
| R-20260930-001 | 2026-09-30T06:24+08:00 | workflow_select | workflow:A | 0.95 | 用户明确"发明想法→专利草稿"全流程意图，信号明确命中Workflow A触发条件 |
| R-20260930-002 | 2026-09-30T06:25+08:00 | stage_transition | contradiction-analyst | 0.92 | Phase 0需求卡已锁定（肉鸡舍地暖·农业×机械交叉），SOP规定Phase 1-2由解其纷执行 |
| R-20260930-003 | 2026-09-30T06:33+08:00 | stage_transition | patent-search-scout | 0.90 | Phase 1-2回传success，SOP进入Phase 3三轮查新；**结果：429失败**（平台级，非路由错误；教训→H4已补平台级错误类） |

## 复盘笔记

- **2026-09-30**：首批3条为补记——协议上线（9-18）当日派单未落盘，暴露"协议写了但执行链无强制点"。修复：任务分配策略表嵌入强制落盘提醒；v2.3装配脚本串联后派单必经脚本，脚本运行时打印RoutingDecision提醒。
- **2026-09-30**：R-003的429失败推动H4新增平台级错误类（等待重置/主理人代执行/上报用户三选一）。
- **2026-09-30**：9-18"同阶段handoff有限放开"与9-29"横直连禁止"冲突，按v2.3证据（跨团队串台实证）统一为：同阶段接力也经主理人中转，用装配脚本确定性交接。
