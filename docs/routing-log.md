# 路由决策日志（R-20260930-001+）

> 2026-09-18 落地路由决策协议；2026-09-30 首批真实记录（含补记：协议上线当日派单未落盘，教训已入 learned_rule）。append-only，每次派单一行。
> 字段：decision_id / timestamp / task_type / target_agent / confidence / **结果** / 理由
>
> **「结果」列填写规范（2026-10-14 新增，P1-4）**：派单时该列填 `待回填`；
> 主理人 VERIFY 后回填实际结果。取值限于：`success` / `partial` / `failed` / `blocked` /
> `门禁违规(Gn)` / `平台错误(429)`，并附关键量化事实（如 conf=78、摘要371字、19件威胁）。
> **无证据可查的补记行一律填 `—（无据未补）`，禁止凭印象回填**——
> 本列的价值在于可复盘，编造的结果比缺失更危险（见 failure-006 自评失真教训）。
>
> **编号完整性说明（R3 · 2026-11-07 补登）**：R-20260930-004 缺号——9-30 当日第 4 次派单
> 未落盘且无任何产出/回传证据可考，按「无据不编造」原则不补记内容，仅在此登记缺号事实。
> 另：本表曾被「复盘笔记」章节截断为两段（S-C3 修复归位不全），2026-11-07 R3 已合并为单表；
> R-20261015 系列原缺「结果」列，按 _VERIFY.md 与 a01 产出证据补齐。

| decision_id | timestamp | task_type | target_agent | confidence | 结果 | 理由 |
|---|---|---|---|---|---|
| R-20260930-001 | 2026-09-30T06:24+08:00 | workflow_select | workflow:A | 0.95 | success（Workflow A 全流程执行） | 用户明确"发明想法→专利草稿"全流程意图，信号明确命中Workflow A触发条件 |
| R-20260930-002 | 2026-09-30T06:25+08:00 | stage_transition | contradiction-analyst | 0.92 | success（Phase 1-2 矛盾建模完成，进入 Phase 3） | Phase 0需求卡已锁定（肉鸡舍地暖·农业×机械交叉），SOP规定Phase 1-2由解其纷执行 |
| R-20260930-003 | 2026-09-30T06:33+08:00 | stage_transition | patent-search-scout | 0.90 | 平台错误(429)（配额耗尽，零产出，6m23s 后判定） | Phase 1-2回传success，SOP进入Phase 3三轮查新；**结果：429失败**（平台级，非路由错误；教训→H4已补平台级错误类） |

| R-20260930-005 | 2026-09-30T15:20+08:00 | stage_transition | patent-examiner-sim | 0.93 | partial（严三性裁决🟡黄，附修复清单；据 R-007 文本推得） | Phase 4 严三性三性对抗·基于R-004 19件威胁·G1/G2门禁校验·落盘R1+严三性串联审查 |
| R-20260930-006 | 2026-09-30T15:21+08:00 | stage_transition | second-opinion-reviewer | 0.90 | —（无据未补） | Phase 4 二审·严三性落盘后自动接棒·H4冲突仲裁（L3 tie-break） |
| R-20260930-007 | 2026-09-30T15:27+08:00 | stage_transition | second-opinion-reviewer | 0.88 | partial（二审结论⚠附条件 + 7盲区 + 附加条件C1-C4） | Phase 4 二审·严三性🟡黄+修复清单已落盘·执行L3元审查+盲区发现+表决 |
| R-20260930-008 | 2026-09-30T15:30+08:00 | stage_transition | disclosure-architect | 0.95 | —（无据未补） | Phase 5a 交底书·基于二审⚠附条件+7盲区+4附加条件C1-C4兑现·G3门禁校验准备 |
| R-20260930-009 | 2026-09-30T15:35+08:00 | stage_transition | patent-search-scout | 0.90 | —（无据未补） | Phase 3 R2·基于R1 19件反推IPC主类·补E/P类·关闭G1门禁前置 |
| R-20260930-010 | 2026-09-30T15:42+08:00 | stage_transition | patent-search-scout | 0.88 | success（🟢绿，G1 门禁关闭；据 R-011 文本推得） | Phase 3 R3差异化验证+复验R1/R2 X/Y级·三要素核验协议·关闭G1门禁·三步法终评 |
| R-20260930-011 | 2026-09-30T15:50+08:00 | stage_transition | patent-attorney-writer | 0.93 | 门禁违规(G5)（摘要实测 371 字符 > 300） | Phase 5b 权项+说明书+摘要·G1门禁已通过（scout R3🟢绿）·兑现严三性6修复+审外审C1-C4 |
| R-20260930-012 | 2026-09-30T15:55+08:00 | stage_transition | patent-attorney-writer | 0.95 | success（摘要重写 ≤300 通过） | Phase 5b修复·G5门禁违规：摘要实测371字符>300·重写≤300·仅限摘要段不超范围 |
| R-20261014-013 | 2026-10-14T22:40+08:00 | stage_transition | contradiction-analyst | 0.92 | success（conf=78，6方向，22组查询·1组如实登记无推荐，落盘34591字符） | P0-2 定向回归验证·与9-30基线同域（肉鸡舍地暖·农业×机械）·验证 shared-core 下沉后装配链 + 双轨制指标 + 门禁四要素校验 |
| R-20261015-001 | 2026-10-15T07:53+08:00 | single_dispatch | contradiction-analyst | 0.94 | success（B01 落盘 20,018 字符） | L1回归 workflow-b-01（冷链保温层矛盾建模·固定用例）；装配链含P2-12失败记忆注入；预装配流水线首次实战 |
| R-20261015-002 | 2026-10-15T08:07+08:00 | single_dispatch | contradiction-analyst | 0.94 | success（合规ID·7/8断言PASS·1INFO） | L1回归重跑 workflow-b-01（合规ID T-20261015-B01）·**并行批次：b01+a01独立回归**（无数据依赖·W1模式首次实战） |
| R-20261015-003 | 2026-10-15T08:07+08:00 | stage_transition | contradiction-analyst | 0.95 | success（23矛盾+1物理·5方向 D1-D5） | L2回归 Phase1-2 workflow-a-01（T-20261015-A01·刮粪板耐磨）·同一并行批次 |
| R-20261015-004 | 2026-10-15T08:16+08:00 | stage_transition | patent-search-scout | 0.93 | success（三轮14检索式·综合红·4条X级） | L2回归 Phase3 查新·**紧凑模式：三轮合并单次派单**（a-01用例约定单成员单文件；区别特征已由Phase2锚定）·依赖Phase2产出 |
| R-20261015-005 | 2026-10-15T08:21+08:00 | stage_transition | contradiction-analyst | 0.91 | success（退回执行·A02 派单） | **查新裁决=红（4条X级）→ 按SOP强制退回Phase2二次迭代**（不得进Phase4）；输入=scout 6.5节4条差异化路径；迭代2任务ID T-20261015-A02 |
| R-20261015-006 | 2026-10-15T08:52+08:00 | retry_loop | contradiction-analyst | 0.90 | success（重试#1·2m40s落盘·4路径全回应） | 迭代2首次派单超时30m18s未落盘（读59KB原报告+过度打磨嫌疑）→ TaskStop取消 + **重试#1**（紧凑brief版·禁读原报告·限时）·Loop预算≤3 |
| R-20261015-007 | 2026-10-15T08:56+08:00 | stage_transition | patent-search-scout | 0.92 | success（30格比对·红→黄） | 迭代2落盘（success·4路径全回应）→ Phase3定向复检（T-20261015-A03·限时10min·紧凑输入）；复检通过则进入Phase4 |
| R-20261015-008 | 2026-10-15T08:59+08:00 | stage_transition | patent-examiner-sim | 0.93 | success（8条攻击·黄·M1-M7） | 复检评级红→黄（中风险·N1+N2+N3绑定前提）→ 按SOP放行Phase4a 对抗式三性确认（T-20261015-A04）；scout建议的N2/N1定向补检因时效约束列入_VERIFY待办 |
| R-20261015-009 | 2026-10-15T09:03+08:00 | stage_transition | second-opinion-reviewer | 0.92 | partial（⚠附条件同意·K1-K7） | 一审裁决黄（黄区上界4/5·M1-M7强制修复）→ Phase4b独立二审（T-20261015-A05·限时8min）；二审通过后进Phase5a |
| R-20261015-010 | 2026-10-15T09:07+08:00 | stage_transition | disclosure-architect | 0.91 | success（交底书·M1-M6兑现·M7待办） | 二审⚠附条件同意（K1-K7）→ Phase5a交底书（T-20261015-A06）；K4已由主理人补记（C3_CONFIRMATION.md）；K1-K3/K6/K7按「兑现或登记待办」逐项处置 |
| R-20261015-011 | 2026-10-15T09:11+08:00 | stage_transition | patent-attorney-writer | 0.93 | success（草稿落盘） | Phase5a完成（M1-M6兑现/K表齐备/附录D提示M7需增补2辅助式）→ Phase5b申请文件草稿（T-20261015-A07·**摘要须机械计量**·failure-006重点防复发） |
| R-20261015-012 | 2026-10-15T09:14+08:00 | retry_loop | patent-attorney-writer | 0.90 | success（重试#1落盘） | A07首次派单**平台级500错误**（5s即失败·非成员错误）→ 按H4重试#1（同任务包·平台级错误不消耗Loop预算的成员侧额度，但记入本任务retry_count） |
| R-20261015-013 | 2026-10-15T10:08+08:00 | stage_transition | patent-attorney-writer | 0.94 | success（摘要258字符·零禁用词） | **L2全链路收官**：A07r落盘（重试#1·摘要258字符python3实测·零禁用词）→ 8阶段全部完成 → 主理人VERIFY：7 PASS / 1 partial → **🟡黄（黄区上界）**结论性条件性通过 |

## 复盘笔记

- **2026-09-30**：首批3条为补记——协议上线（9-18）当日派单未落盘，暴露"协议写了但执行链无强制点"。修复：任务分配策略表嵌入强制落盘提醒；v2.3装配脚本串联后派单必经脚本，脚本运行时打印RoutingDecision提醒。
- **2026-09-30**：R-003的429失败推动H4新增平台级错误类（等待重置/主理人代执行/上报用户三选一）。
- **2026-09-30**：9-18"同阶段handoff有限放开"与9-29"横直连禁止"冲突，按v2.3证据（跨团队串台实证）统一为：同阶段接力也经主理人中转，用装配脚本确定性交接。
- **2026-11-07（R3）**：表格断裂合并修复 + R-004 缺号登记（见头部说明）；R-20261015-001~013 结果列按 _VERIFY.md 与 a01 产出证据回填。
