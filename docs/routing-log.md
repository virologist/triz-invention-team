# 路由决策日志（R-20260930-001+）

> 2026-09-18 落地路由决策协议；2026-09-30 首批真实记录（含补记：协议上线当日派单未落盘，教训已入 learned_rule）。append-only，每次派单一行。
> 字段：decision_id / timestamp / task_type / target_agent / confidence / **结果** / 理由 / rationale_class
>
> **列数契约（S-E48 · 2026-11-09 补正）**：本表为 SOP `RoutingDecision`（8 字段）的**精简落盘投影**——
> SOP「强制落盘规则」只要求「decision_id + target + confidence + 简述」，故落盘表按本行
> 声明的 8 列书写，**表头列数必须 == 头部「字段：」声明字段数 == 每条数据行列数**。
> `rationale_class` 取值：`rule_match` / `context_embedding` / `socratic_followup`。
> 此前表头只声明 7 列而数据行写 8 列（R-20261108-001 已入库即如此）→ Markdown 渲染错位，
> 第 6 列「结果」被挤出表头，**本表唯一可复盘字段失效**。已由 preflight 第 14 项机械校验兜底。
>
> **旧行补列说明**：R-20260930-001 ~ R-20261015-013 共 26 条历史行为**旧 7 列格式**
> （SOP 落盘规则落地前书写，无 `rationale_class` 字段）。为保持 append-only 不改写历史行，
> 历史行末列补 `—（旧格式无此字段）`，并在 preflight 第 14 项中按「同表列数须一致」处理。
>
> **「结果」列填写规范（2026-10-14 新增，P1-4）**：派单时该列填 `待回填`；
> 主理人 VERIFY 后回填实际结果。取值限于：`success` / `partial` / `failed` / `blocked` /
> `门禁违规(Gn)` / `平台错误(429)`，并附关键量化事实（如 conf=78、摘要371字、19件威胁）。
> **无证据可查的补记行一律填 `—（无据未补）`，禁止凭印象回填**——
> 本列的价值在于可复盘，编造的结果比缺失更危险（见 failure-006 自评失真教训）。
> **resume 事件行（R5 · 2026-11-07 新增）**：会话中断后经 `state_store.py resume` 续接时，
> 必须补一条 `task_type=resume` 的决策行（decision_id 照常递增，理由注明"中断恢复·续接自 Phase N"）——
> 否则审计链缺"为什么从这里继续"的路由依据（D10-1）。
>
> **编号完整性说明（R3 · 2026-11-07 补登）**：R-20260930-004 缺号——9-30 当日第 4 次派单
> 未落盘且无任何产出/回传证据可考，按「无据不编造」原则不补记内容，仅在此登记缺号事实。
> 另：本表曾被「复盘笔记」章节截断为两段（S-C3 修复归位不全），2026-11-07 R3 已合并为单表；
> R-20261015 系列原缺「结果」列，按 _VERIFY.md 与 a01 产出证据补齐。

| decision_id | timestamp | task_type | target_agent | confidence | 结果 | 理由 | rationale_class |
|---|---|---|---|---|---|---|
| R-20260930-001 | 2026-09-30T06:24+08:00 | workflow_select | workflow:A | 0.95 | success（Workflow A 全流程执行） | 用户明确"发明想法→专利草稿"全流程意图，信号明确命中Workflow A触发条件 |—（旧格式无此字段）|
| R-20260930-002 | 2026-09-30T06:25+08:00 | stage_transition | contradiction-analyst | 0.92 | success（Phase 1-2 矛盾建模完成，进入 Phase 3） | Phase 0需求卡已锁定（肉鸡舍地暖·农业×机械交叉），SOP规定Phase 1-2由解其纷执行 |—（旧格式无此字段）|
| R-20260930-003 | 2026-09-30T06:33+08:00 | stage_transition | patent-search-scout | 0.90 | 平台错误(429)（配额耗尽，零产出，6m23s 后判定） | Phase 1-2回传success，SOP进入Phase 3三轮查新；**结果：429失败**（平台级，非路由错误；教训→H4已补平台级错误类） |—（旧格式无此字段）|

| R-20260930-005 | 2026-09-30T15:20+08:00 | stage_transition | patent-examiner-sim | 0.93 | partial（严三性裁决🟡黄，附修复清单；据 R-007 文本推得） | Phase 4 严三性三性对抗·基于R-004 19件威胁·G1/G2门禁校验·落盘R1+严三性串联审查 |—（旧格式无此字段）|
| R-20260930-006 | 2026-09-30T15:21+08:00 | stage_transition | second-opinion-reviewer | 0.90 | —（无据未补） | Phase 4 二审·严三性落盘后自动接棒·H4冲突仲裁（L3 tie-break） |—（旧格式无此字段）|
| R-20260930-007 | 2026-09-30T15:27+08:00 | stage_transition | second-opinion-reviewer | 0.88 | partial（二审结论⚠附条件 + 7盲区 + 附加条件C1-C4） | Phase 4 二审·严三性🟡黄+修复清单已落盘·执行L3元审查+盲区发现+表决 |—（旧格式无此字段）|
| R-20260930-008 | 2026-09-30T15:30+08:00 | stage_transition | disclosure-architect | 0.95 | —（无据未补） | Phase 5a 交底书·基于二审⚠附条件+7盲区+4附加条件C1-C4兑现·G3门禁校验准备 |—（旧格式无此字段）|
| R-20260930-009 | 2026-09-30T15:35+08:00 | stage_transition | patent-search-scout | 0.90 | —（无据未补） | Phase 3 R2·基于R1 19件反推IPC主类·补E/P类·关闭G1门禁前置 |—（旧格式无此字段）|
| R-20260930-010 | 2026-09-30T15:42+08:00 | stage_transition | patent-search-scout | 0.88 | success（🟢绿，G1 门禁关闭；据 R-011 文本推得） | Phase 3 R3差异化验证+复验R1/R2 X/Y级·三要素核验协议·关闭G1门禁·三步法终评 |—（旧格式无此字段）|
| R-20260930-011 | 2026-09-30T15:50+08:00 | stage_transition | patent-attorney-writer | 0.93 | 门禁违规(G5)（摘要实测 371 字符 > 300） | Phase 5b 权项+说明书+摘要·G1门禁已通过（scout R3🟢绿）·兑现严三性6修复+审外审C1-C4 |—（旧格式无此字段）|
| R-20260930-012 | 2026-09-30T15:55+08:00 | stage_transition | patent-attorney-writer | 0.95 | success（摘要重写 ≤300 通过） | Phase 5b修复·G5门禁违规：摘要实测371字符>300·重写≤300·仅限摘要段不超范围 |—（旧格式无此字段）|
| R-20261014-013 | 2026-10-14T22:40+08:00 | stage_transition | contradiction-analyst | 0.92 | success（conf=78，6方向，22组查询·1组如实登记无推荐，落盘34591字符） | P0-2 定向回归验证·与9-30基线同域（肉鸡舍地暖·农业×机械）·验证 shared-core 下沉后装配链 + 双轨制指标 + 门禁四要素校验 |—（旧格式无此字段）|
| R-20261015-001 | 2026-10-15T07:53+08:00 | single_dispatch | contradiction-analyst | 0.94 | success（B01 落盘 20,018 字符） | L1回归 workflow-b-01（冷链保温层矛盾建模·固定用例）；装配链含P2-12失败记忆注入；预装配流水线首次实战 |—（旧格式无此字段）|
| R-20261015-002 | 2026-10-15T08:07+08:00 | single_dispatch | contradiction-analyst | 0.94 | success（合规ID·7/8断言PASS·1INFO） | L1回归重跑 workflow-b-01（合规ID T-20261015-B01）·**并行批次：b01+a01独立回归**（无数据依赖·W1模式首次实战） |—（旧格式无此字段）|
| R-20261015-003 | 2026-10-15T08:07+08:00 | stage_transition | contradiction-analyst | 0.95 | success（23矛盾+1物理·5方向 D1-D5） | L2回归 Phase1-2 workflow-a-01（T-20261015-A01·刮粪板耐磨）·同一并行批次 |—（旧格式无此字段）|
| R-20261015-004 | 2026-10-15T08:16+08:00 | stage_transition | patent-search-scout | 0.93 | success（三轮14检索式·综合红·4条X级） | L2回归 Phase3 查新·**紧凑模式：三轮合并单次派单**（a-01用例约定单成员单文件；区别特征已由Phase2锚定）·依赖Phase2产出 |—（旧格式无此字段）|
| R-20261015-005 | 2026-10-15T08:21+08:00 | stage_transition | contradiction-analyst | 0.91 | success（退回执行·A02 派单） | **查新裁决=红（4条X级）→ 按SOP强制退回Phase2二次迭代**（不得进Phase4）；输入=scout 6.5节4条差异化路径；迭代2任务ID T-20261015-A02 |—（旧格式无此字段）|
| R-20261015-006 | 2026-10-15T08:52+08:00 | retry_loop | contradiction-analyst | 0.90 | success（重试#1·2m40s落盘·4路径全回应） | 迭代2首次派单超时30m18s未落盘（读59KB原报告+过度打磨嫌疑）→ TaskStop取消 + **重试#1**（紧凑brief版·禁读原报告·限时）·Loop预算≤3 |—（旧格式无此字段）|
| R-20261015-007 | 2026-10-15T08:56+08:00 | stage_transition | patent-search-scout | 0.92 | success（30格比对·红→黄） | 迭代2落盘（success·4路径全回应）→ Phase3定向复检（T-20261015-A03·限时10min·紧凑输入）；复检通过则进入Phase4 |—（旧格式无此字段）|
| R-20261015-008 | 2026-10-15T08:59+08:00 | stage_transition | patent-examiner-sim | 0.93 | success（8条攻击·黄·M1-M7） | 复检评级红→黄（中风险·N1+N2+N3绑定前提）→ 按SOP放行Phase4a 对抗式三性确认（T-20261015-A04）；scout建议的N2/N1定向补检因时效约束列入_VERIFY待办 |—（旧格式无此字段）|
| R-20261015-009 | 2026-10-15T09:03+08:00 | stage_transition | second-opinion-reviewer | 0.92 | partial（⚠附条件同意·K1-K7） | 一审裁决黄（黄区上界4/5·M1-M7强制修复）→ Phase4b独立二审（T-20261015-A05·限时8min）；二审通过后进Phase5a |—（旧格式无此字段）|
| R-20261015-010 | 2026-10-15T09:07+08:00 | stage_transition | disclosure-architect | 0.91 | success（交底书·M1-M6兑现·M7待办） | 二审⚠附条件同意（K1-K7）→ Phase5a交底书（T-20261015-A06）；K4已由主理人补记（C3_CONFIRMATION.md）；K1-K3/K6/K7按「兑现或登记待办」逐项处置 |—（旧格式无此字段）|
| R-20261015-011 | 2026-10-15T09:11+08:00 | stage_transition | patent-attorney-writer | 0.93 | success（草稿落盘） | Phase5a完成（M1-M6兑现/K表齐备/附录D提示M7需增补2辅助式）→ Phase5b申请文件草稿（T-20261015-A07·**摘要须机械计量**·failure-006重点防复发） |—（旧格式无此字段）|
| R-20261015-012 | 2026-10-15T09:14+08:00 | retry_loop | patent-attorney-writer | 0.90 | success（重试#1落盘） | A07首次派单**平台级500错误**（5s即失败·非成员错误）→ 按H4重试#1（同任务包·平台级错误不消耗Loop预算的成员侧额度，但记入本任务retry_count） |—（旧格式无此字段）|
| R-20261015-013 | 2026-10-15T10:08+08:00 | stage_transition | patent-attorney-writer | 0.94 | success（摘要258字符·零禁用词） | **L2全链路收官**：A07r落盘（重试#1·摘要258字符python3实测·零禁用词）→ 8阶段全部完成 → 主理人VERIFY：7 PASS / 1 partial → **🟡黄（黄区上界）**结论性条件性通过 |—（旧格式无此字段）|

## 复盘笔记

- **2026-09-30**：首批3条为补记——协议上线（9-18）当日派单未落盘，暴露"协议写了但执行链无强制点"。修复：任务分配策略表嵌入强制落盘提醒；v2.3装配脚本串联后派单必经脚本，脚本运行时打印RoutingDecision提醒。
- **2026-09-30**：R-003的429失败推动H4新增平台级错误类（等待重置/主理人代执行/上报用户三选一）。
- **2026-09-30**：9-18"同阶段handoff有限放开"与9-29"横直连禁止"冲突，按v2.3证据（跨团队串台实证）统一为：同阶段接力也经主理人中转，用装配脚本确定性交接。
- **2026-11-07（R3）**：表格断裂合并修复 + R-004 缺号登记（见头部说明）；R-20261015-001~013 结果列按 _VERIFY.md 与 a01 产出证据回填。
| R-20261108-001 | 2026-11-08T15:06:00+08:00 | workflow_select | workflow:B+定制(Phase0→1-2∥Phase3→Fan-in评分) | 0.90 | 用户单轮给出完整五维需求与评分体系，产出为方向矩阵而非申请文件；方向生成与查新无数据依赖，符合W1白名单并行条件 | workflow:A(0.55,用户明示只要方向矩阵不写申请文件)；单agent直调analyst(0.4,需查新校准空白区) | rule_match |
| R-20261108-002 | 2026-11-08T15:50:00+08:00 | stage_transition | lead:Phase2.5-Fan-in校准+主理人抽查核验 | 0.95 | 双成员产出交叉印证（Once族/US11071285/UV闭环红海一致），主理人抽查未推翻K1/K2空白；校准属主理人法定职责不派成员 | 派审外审复核(0.5,本轮无终审裁决对象,校准≠裁决) | rule_match |
| R-20261110-001 | 2026-11-10T17:05:00+08:00 | workflow_select | workflow:C+(方向梳理+增量查新+可专利性结论) | 0.88 | 用户要三大场景方向梳理+查重+可专利性结论，非申请文件；20261108资产可复用病原防控场景与免疫空白区，检验检疫/疫苗冷链为增量焦点 | workflow:A(0.4,明示不写申请文件)；workflow:C原版(0.6,无方向生成环节,用户要求梳理创新方向故需analyst) | rule_match |
| R-20261110-002 | 2026-11-10T17:05:00+08:00 | single_dispatch | contradiction-analyst ∥ patent-search-scout(仅R1) | 0.90 | W1独立咨询白名单+S-E14约束：scout预热仅R1，Phase2.5校准后续R2R3；analyst方向生成与scout R1无数据依赖 | analyst先行单独(0.5,scout R1可并行预热增量焦点,无依赖) | rule_match |
| R-20261110-003 | 2026-11-10T17:48:00+08:00 | stage_transition | lead:Phase2.5校准(基于R1+20261108矩阵) | 0.85 | 分析基线=前次方向矩阵(D1-D4+K1-K5)+R1增量：K3降黄(锚点收紧四要素)、场景①POCT判红、场景②新增两绿缝(车间光制度/冷链主动光保护)、K1b大动物扩展零占位——校准对象齐备，analyst重试与scout R2R3可并行 | 等analyst重写后再校准(0.4,平台502已耗26min,墙钟超预算线,紧凑抢救优先) | context_embedding |
| R-20261110-004 | 2026-11-10T17:48:00+08:00 | single_dispatch | contradiction-analyst重试(紧凑brief) ∥ patent-search-scout R2+R3紧凑模式 | 0.85 | H4平台错误单次重试；R2+R3合并单spawn=紧凑模式(条件:区别特征已由R1锚定+墙钟压力)；并行理由:校准已完成,R2查询池(WO2023186741A1权项/疫苗车间IPC/K1b大动物/成像窄缝)不依赖analyst重写文档 | 串行等待analyst(0.5,墙钟超预算不可接受) | rule_match |
| R-20261110-005 | 2026-11-10T17:48:00+08:00 | stage_transition | lead:Fan-in终校准(三场景矩阵定稿) | 0.90 | analyst 8方向×scout三轮合并评级交叉：D4冷链被CN116853666A收窄→并入D3外围权项；D7 K3四重夹击→并入D6家族第二优先；D2成像黄偏红→绑定禽特异荧光特征库才可写 | 保持D4独立申请(0.4,证据优先,L2原则机械执行) | rule_match |
