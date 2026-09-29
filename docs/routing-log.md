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
| R-20260930-004 | 2026-09-30T15:45+08:00 | stage_transition | patent-search-scout | 0.92 | 重构后重跑Phase 3 R1：429已重置；本次走v2.3装配脚本（assemble_spawn_prompt.py）+落盘验收完整派单链 |
| R-20260930-005 | 2026-09-30T15:20+08:00 | stage_transition | patent-examiner-sim | 0.93 | Phase 4 严三性三性对抗·基于R-004 19件威胁·G1/G2门禁校验·落盘R1+严三性串联审查 |
| R-20260930-006 | 2026-09-30T15:21+08:00 | stage_transition | second-opinion-reviewer | 0.90 | Phase 4 二审·严三性落盘后自动接棒·H4冲突仲裁（L3 tie-break） |
| R-20260930-007 | 2026-09-30T15:27+08:00 | stage_transition | second-opinion-reviewer | 0.88 | Phase 4 二审·严三性🟡黄+修复清单已落盘·执行L3元审查+盲区发现+表决 |
| R-20260930-008 | 2026-09-30T15:30+08:00 | stage_transition | disclosure-architect | 0.95 | Phase 5a 交底书·基于二审⚠附条件+7盲区+4附加条件C1-C4兑现·G3门禁校验准备 |
| R-20260930-009 | 2026-09-30T15:35+08:00 | stage_transition | patent-search-scout | 0.90 | Phase 3 R2·基于R1 19件反推IPC主类·补E/P类·关闭G1门禁前置 |
| R-20260930-010 | 2026-09-30T15:42+08:00 | stage_transition | patent-search-scout | 0.88 | Phase 3 R3差异化验证+复验R1/R2 X/Y级·三要素核验协议·关闭G1门禁·三步法终评 |
| R-20260930-011 | 2026-09-30T15:50+08:00 | stage_transition | patent-attorney-writer | 0.93 | Phase 5b 权项+说明书+摘要·G1门禁已通过（scout R3🟢绿）·兑现严三性6修复+审外审C1-C4 |
| R-20260930-012 | 2026-09-30T15:55+08:00 | stage_transition | patent-attorney-writer | 0.95 | Phase 5b修复·G5门禁违规：摘要实测371字符>300·重写≤300·仅限摘要段不超范围 |
