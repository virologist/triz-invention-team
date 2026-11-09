# 诊断—增补—优化 协议（v2.6.0 Batch3 · 修 S-X1）

> 本协议把此前两次靠用户手动触发的独立诊断（2026-10-15 两轮）固化为**可复现、可按需触发**的
> 团队自有流程。定位与 G1-G5 门禁同级：门禁守产出质量，本协议守**架构质量**。

## 一、触发条件（满足任一即执行一次诊断）

> **CYCLE-1 · S-E04 脚本化**：T1/T2/T3 已有机械判定 `scripts/diagnosis_trigger.py`，
> 由 `preflight_check.py` 第9项建队前自动执行（warn 级，不阻断）；T4 为用户手动，无需脚本。
> 「是否真的执行诊断」的语义裁决仍归管家节点（三件事分工宪法）。

| 触发器 | 阈值 | 说明 |
|---|---|---|
| T1 同类失败复发 | `~/.workbuddy/expert-failures/` 30 天内同 fail_type ≥2 条新记录 | 失败索引复利路径的主动形态 |
| T2 周期性 | 主会话每累计 ~10 轮重大迭代后（或自然月 1 次） | 定期熵减 |
| T3 重大架构变更 | 任何涉及 shared-core 联邦 / schema 演进 / 成员增删的改动合入后 | 变更后验收 |
| T4 用户手动 | 用户明示"诊断/审查专家团" | 最高优先级，从零执行 |

## 二、诊断维度清单（10+1 维，逐维给证据）

1. **领域坍缩匹配度**：成员知识深度 × 领域/子领域/交叉覆盖（对照 SOP 领域坍缩协议 7 视角）
2. **协作机制**：分工边界 / 信息同步 / 并行串行衔接（对照 P2-10 白名单与横直连禁令）
3. **决策流程**：依据链完整性 / L1-L4 仲裁可执行性 / 分歧解决时效
4. **资源配置**：工具与子代理分配 / 预算优先级 / 重复与无效投入（对照 H3.5）
5. **沟通效率**：冗余控制 / 消息格式 / 响应可执行性（对照 H1 压缩规则与信封契约）
6. **诊断-增补-优化主链路自身**：本协议的触发器是否真实生效（防"协议上墙但无人跑"）
7. **优化与质量控制**：整体校验点覆盖 / 错误修复流程 / 多轮收敛终止标准——**须满足耦合 skill 要求**：
   A-Evolve（gate+egl 收敛判据）、self-improving-agent（.learnings 回灌）、prompt-engineering-expert
   （C-item 准则清单+有界修改）
8. **Agent 设计**：loop 收敛 / 上下文裁剪 / 工具失败重试 / 权限边界 / 状态持久化 / 异常处理
9. **工具动态编排**：优先/次优先链路 / 冗余编排规避单点故障
10. **意外中断恢复与进度续接**：state.json 是否真实可续接（跑一次 resume 冒烟）
11. **宏观-中观-微观重构评估**：是否需从头重构 / 各颗粒度功能补充 / 升维方向

## 三、证据要求（每条短板强制）

- **可观察证据**：文件:行号 / 脚本实测输出 / 历史产出引用 / routing-log 行——禁止"感觉上""可能存在"
- **影响范围**：哪个成员/阶段/门禁受影响
- **严重度**：高（契约/数据/可运行性）· 中（质量/效率）· 低（文档/整洁）
- **改进方向可验证**：写明验证方式（哪个脚本/断言）与判定标准（exit 0 / 计数 / diff=0）

## 四、修复执行纪律

1. **批次化**：按 P0/P1/P2 分批，每批独立 commit（信息含批次号+涉及 S 编号），可独立 revert
2. **有界修改**（prompt-engineering-expert 门）：只改诊断命中的项，不借机重构未受质疑的部分
3. **每批验收**：全套门禁（verify_triz_data / agent_ci_gate --self-test / contract_enforce 全量
   回归 / test_vendor_core / skill_test_runner）零回退后才能 commit
4. **交叉验证**：全部批次完成后跑 2 轮（脚本互检 + 从零视角复读文档找自相矛盾），残留问题登记

## 五、诊断产出归档

- 诊断报告：写工作区 `outputs/triz-team-diagnosis-independent-<date>.md`（不入包，包只收修复）
  - 报告实际存放位置 = 会话工作区 `<workspace>/outputs/`（非包内 outputs/ 回归产物目录）；
    示例：triz-team-diagnosis-independent-20261107-r3.md 存于 2026-11-07 会话工作区 outputs/ 下
- 修复后：本文件 §六登记表追加一行（诊断日期/触发器/短板块数/已修复/残留）

## 六、诊断登记表

| 日期 | 触发器 | 短板 | 已修复 | 回检（48h 内独立复检：是否引入新缺陷） | 残留 |
|---|---|---|---|---|---|
| 2026-10-15 | T4 手动 | 24 项（S1-1…S5-4） | P0 三项 + P1+P2 九项（v2.5.x） | —（本列 2026-11-07 R4 增设，历史批次未回检；其中 v2.4.0 联邦下沉事后被证实丢失路由提醒——正是缺回检的代价） | V6 设计缺陷（联邦层）· spawn_watchdog |
| 2026-11-07 | T4 手动 | 17 项（S-Q1…S-D1） | Batch1-5 全部（v2.6.0+2.7.0） | Batch5A 联邦修复引入 D2-1（路由提醒丢失）——已由第三轮诊断捕获并修复（R2） | 见下方"已知残留" |
| 2026-11-07（第三轮） | T4 手动 | 14 项（D2-1…D10-1 + U1-U3 升维） | R1-R5 全部 + U1-U3（v2.8.0） | **回检完成（2026-11-08）**：窗口内多轮全套门禁复跑全绿（vendor V1-V6 / 契约自测 / 三用例回归），唯一新发现=benchmark 目录级传参混扫（示例修正 7d9742d，非修复引入）；D4-2 himmpat 登录态探测评估：**不实施**（运行时状态不可预判，scout L2→L3 降档规则已覆盖，preflight 加探测反造假信号） | 残留 8 项已全部清偿（见 2026-11-08 行） |
| 2026-11-08（残留清偿） | T1 同类失败复发（member_files 覆盖误判同型） | C01 法25 / U3 outdated / D3-1+D1 / OPERATIONS 订正 / vendor 核验 / spawn_watchdog / D4-2 / 回检登记 | 8 项全部清偿（d4bee57→e47a525） | 48h 后复检 | 无遗留 |
| 2026-11-08（CYCLE-1 · 墨衡） | T4 手动 + T3 架构变更（门禁状态机改动） | 19 项（S-E01…S-E19） | P0-1（3812043）+ P1-1（a8633ba）+ P1-2（1a747b5）+ P1-3（3a51ce1）+ P2-1（ad96ee9）+ P1-4（764b1dd）+ P1-5/P1-6（b871989）+ C4-🔴（fdf1a95） | 见下方「CYCLE-1 已知残留」 | 见下方「CYCLE-1 已知残留」 |
| 2026-11-09（CYCLE-1 · 第2轮交叉验证 + C4 再诊断） | T3 架构变更 + 第2轮交叉验证 + C4 独立子智能体审计 | 19 条（第2轮交叉验证确证问题）+ 14 条（C4 再诊断新增：🔴4·🟡6·🟢4） | 第2轮 19 条 → b871989；C4 4 条🔴 → fdf1a95；C4 剩余 10 条🟡/🟢 → C5 批次 commit | 48h 后复检 | `marketplace.json` source 指向单仓 GitHub 安装路径失效（评估后不实施，见 CHANGELOG 2.9.0 Evaluated） |
| 2026-11-09（CYCLE-1 · 第3轮全面排查） | T4 手动（用户授权推送 GitHub 后的全量复检） | 9 项（S-E44…S-E52：死代码 3 · 契约漂移 3 · 幽灵契约 1 · 安装路径 1 · 崩溃 1） | 全部清偿（v2.10.0） | 48h 后复检 | 无遗留（本轮 9 项全部落地并有变异测试证明判别力） |

**已知残留（2026-11-07 第三轮交接）**：
- ~~spawn_watchdog（P2-15）~~ → **简版已落地**（2026-11-08，e47a525+）：scripts/spawn_watchdog.py 四态判定（OK/WATCH/STALL/TIMEOUT）+ H4 处置建议；桌面通知通道仍未建（等待窗口手动调用够用）
- ~~workflow-c-01「法25」断言 FAIL~~ → **已修复**（2026-11-08 `d4bee57`）：根因实为 member_files 最后文件覆盖，新增 any_member 断言模式；实测 8/8 PASS
- ~~联邦 3 包 vendor 未提交~~ → **已核验清偿**（2026-11-08）：viral-evo-lab / research-orchestration-team 工作树干净（活跃会话已提交），smart-textbook-team vendor 已在 HEAD `20c6f5a` 内；vet-med-ppt-team 有活跃改动，留权不动

**CYCLE-1 已知残留（2026-11-08 · 墨衡第三轮诊断 S-E01…S-E19）**：
- **本轮已清偿（P0-1 + P1-1 + P1-2 + P1-3 + P2-1 + P1-4）**：S-E01 门禁键名双轨（GATE_ALIASES 归一 + G2 落点 + check_gates 精确读取 + `reset_for_rework`）· S-E02 Workflow D 前置闸（**P1-4 落地为 preflight 第12项机械校验**）· S-E03 H4 代执行例外边界 · S-E04 T1-T3 触发器脚本化（`diagnosis_trigger.py`）· S-E05 登记表断表 · S-E06/S-E17 三源自测兑现 · S-E07 frontmatter 契约字段完整性 · S-E08 台账单源化（`evolution_log.py`）· **S-E09 README 结构图/失效引用**（P1-3）· **S-E11 forbidden_boundary 契约字段**（P1-3）· **S-E12 墙钟 WARN**（P2-1）· **S-E13 成员数口径**（P2-1）· **S-E14 W1 前提**（P2-1）· S-E10 loopback_count 机械终止 · S-E15 契约 fail-open 修复 · S-E16 preflight 假绿修复 · S-E18 退回 Phase2 强制重跑 R1-R3 · S-E19 Phase 2.5 状态节点 · S-E20 单字禁词误伤修复 · **S-E21 幽灵验证项清偿**（P1-4：DRIFT_PROBE 探针落地 + --strict 死参数修复）· **S-E22 幽灵门禁清偿**（P1-4：agent_ci_gate fallback 扫基线 markdown 信封）· **S-E23 结构校验对齐 git 入库口径**（P1-4）· **S-E24 state 模板补全**（P1-5：architecture §3.2 对齐 5 gates + 4 metrics）· **S-E25 墙钟双轨制**（P1-5：architecture §3.5）· **S-E26 L3 仲裁口径同步**（P1-5：D3-1 订正同步至架构文档）· **S-E27 task_payload 示例补 forbidden_boundary**（P1-5）
- **待清偿（截至 2026-11-09 · P1-4/P1-5 收口后）**：原 5 项（S-E09/S-E11/S-E12/S-E13/S-E14）已于 P1-3 与 P2-1 批次清偿完毕，**本清单已空**；新增增量项（S-E21…S-E27）亦已在 P1-4/P1-5 落地。
- **C4 再诊断新增 14 条（S-E28…S-E41）· 全部清偿**：
  - **🔴 4 条（fdf1a95）**：S-E28 自测4 自指模拟 → 抽出 `check_three_source_drift()` 单一真源 + 变异测试证明探针有判别力 ·
    S-E29 `verify_triz_data` 的 `warn()` 零调用 → `--strict` 语义空转 → 新增 `check_soft_invariants()` 落地 3 个真实 warn 产出点 ·
    S-E30 `agent_ci_gate` fallback 路径 `sender = agent_id` → `agent_mismatch` 恒 False（假绿）→ sender 改由**文件名**推导 ·
    S-E31 主理人 MD「phase=3 进 R2」与 `state_store.PHASE_NEXT[3]` 双语义 → 订正为「phase 是阶段号不是轮次号」。
  - **🟡 6 条**：S-E32 版本收口（README.zh 三处 + plugin.json → v2.9）· S-E33 OPERATIONS 行号引用 294-296 → 351-353 + fallback 描述订正 ·
    S-E34 preflight docstring 7 项 → 12 项 · S-E35 零覆盖 `--strict` 假绿 → strict 零覆盖阻断（exit 1）·
    S-E36 本登记表 commit hash 补全（本行）· S-E37 `docs/evolution-log.tsv` 补录本轮 7 个批次 commit。
  - **🟢 4 条**：S-E38 README.zh 报告名 `agent_ci_gate_report.json` → `ci_gate_report.json` ·
    S-E39 装配器白名单口径显式化（6 执行成员 vs 全仓 7）· S-E40 `LEGACY_CUTOFF` 死代码 → 抽出 `_is_legacy_name()` 单一真源 ·
    S-E41 CHANGELOG `[Unreleased]` 去日期 + 2.9.0 段补录本轮全部变更。
- **C4 闭环复查新发现 2 条（S-E42/S-E43）· 已清偿**：
  - **S-E42 [P1]** 主理人 MD 两处 state 口径漂移（MD:98 快照字段列表遗漏 `evidence`/`conditions`/
    `trinity_verdict_pass`/墙钟字段；MD:576 状态块模板 `metrics` 漏 `duration_ms_wall`/`duration_source`
    → S-E25 墙钟双轨制未下沉到 SOP）→ 两处按 `architecture.md` §3.2 补全 + 标注字段层级口径。
  - **S-E43 [P1]** 根因整治：state 模板三处手抄（代码/文档/SOP）且无机械校验 → 落地
    **preflight 第 13 项**「state 模板三处真源一致性」校验（双向差集为空才放行，漂移即 BLOCK），
    变异测试证明有判别力（删字段必检出）。preflight 项数 12 → **13**。
- **C4 再诊断闭环判据**（实测满足）：新增 🔴 = 0 且新增 🟡 = 0 → 准予进入 C5 登记收敛。
- **C4 再诊断新增待登记**：`marketplace.json` 的 `source` 字段指向 `./plugins/triz-invention-team`，但本仓 git 根为**平铺布局**（无 `plugins/` 嵌套层）——本地安装（`my-experts` 市场根含 `plugins/`）正常，但**单仓 GitHub 安装**（`/plugin marketplace add virologist/triz-invention-team`）会指向不存在的目录
- **本轮新增待登记（实测发现）**：~~`marketplace.json` 的 `source` 指向 `./plugins/triz-invention-team`~~ → **已评估并登记于 CHANGELOG 2.9.0 Evaluated 段**（单仓 GitHub 安装路径失效；本仓 git 根为平铺布局，本地安装正常）。C5 收口时以「评估后不实施」结案，**不擅自改动发布路径语义**。

- **第3轮全面排查新增 9 条（S-E44…S-E52）· 全部清偿（v2.10.0）**：
  - **死代码（3 条）**：**S-E44** `agent_ci_gate` 的两个 schema 路径常量定义后从未引用、`main()` 二次手抄
    （`run_regression` 另有全仓第三处手抄）→ 三处统一消费唯一真源常量 ·
    **S-E45** `patent_knowledge.GRADE_SEC_RE` 死常量 + 76 行另有独立正则（两条可各自漂移）→
    切分实现下沉到常量，解析处直接消费（等价性实测 6/6 一致）·
    **S-E46/S-E50** `skill_test_runner.RESULTS` / `state_store.PKG` / `state_store.HERE` 三个死变量移除。
  - **契约漂移（3 条 · 根因整治）**：**S-E48** routing-log 落盘表三处手抄无校验 → 表头 7 列 vs 数据行 8 列
    （**已入库于 7b6ffb8** 的 R-20261108-001 即是）→ 第 6 列「结果」被挤出表头，**唯一可复盘字段失效**
    → 落地 **preflight 第 14 项**（表头列数 == 全部数据行列数 == 头部「字段：」声明数，逐位对齐）·
    **S-E49** `task_id` 三处手抄无校验 → 信封 schema 允许字母后缀、任务包 schema 只允许纯数字、
    文档示例写纯数字，而**实测基线全部用字母后缀**（`T-20261015-A01`…`A07`，7 信封 + 9 spawn）
    → 主理人按实测形态派单时下游按任务包 schema 校验**必被拒**；且任务包 schema **零代码消费**（幽灵契约）
    → 落地 **preflight 第 15 项**（pattern 字面统一 + 基线样本全匹配 + 反幽灵契约且**排除本项自身**避免自证）·
    **S-E51** `run_regression` 保底字面量是 schema pattern 的**第二份真源** → 改 fail loud（不静默降级）。
  - **安装路径（1 条）**：**S-E47** `.claude-plugin/` 整目录被 gitignore → GitHub 上**完全没有** Claude marketplace
    定义（官方要求必须入库）→ 单仓 `/plugin marketplace add` 根本读不到插件清单；且双 `marketplace.json` 的
    `source` 指向不存在目录 → 改为 `source: "./"` + gitignore 改为「排除内容但保留 marketplace.json」。
    依据三重权威证据：官方文档 + 本地 6 个已工作的同类单仓 marketplace + `git clone` 端到端实测。
  - **崩溃（1 条）**：**S-E52** `--scaffold` 全线 `KeyError: 'expect'`（层级误读，`expect` 是断言层字段）
    → **用 HEAD 版本复现确认预先存在**，非本轮引入 → 改按断言 `all_members_landed` 读取成员清单。
  - **判别力验收**：本轮新增的 2 个 preflight 检查项均做变异测试（**第 14 项 3 例 + 第 15 项 4 例 + S-E51 1 例 = 8 例**），
    破坏必检出、还原必 PASS；其中第 15 项判据 3 曾因「自证」漏检（preflight 自己算消费方）→ **已自查修正**。
  - **本轮登记**：preflight 项数 13 → **15**；版本 2.9.0 → **2.10.0**（三处版本号 + README 三处 + OPERATIONS 一处）。

- **第4轮全面排查新增 9 条（S-E53…S-E61）· 全部清偿（v2.11.0 · 2026-11-09）**（角色 = AI agent 开发/测试工程师；用户要求「修复和测试与 debug 后再次全面排查」）：
  - **契约双源漂移（根因整治）**：**S-E53** X 级计数两套判据（preflight 宽松正则 `X\s*[\W_]*\s*(\d+)`
    对 7 真实场景误判 4 例 · patent_knowledge 结构化判据）→ 新增 `scripts/threat_grade.py` **唯一真源**
    （结构载体 + 专利号正则 + 否定值过滤 + 跨载体按专利号去重 + C3 触发「X 或 E」语义），preflight 第 8 项与
    patent_knowledge 均改消费 ·
    **S-E54** task_id pattern 全仓**第三份手抄**（`token_budget_check.FILENAME_RE`）→ 从 schema 派生，
    读不到 fail loud · **S-E55** `agent-protocol/SKILL.md` 文档真源漂移（旧 pattern 漏实测字母后缀形态）
    → 同步 + preflight 第 15 项扩为**五处判据**（含全仓零手抄扫描）。
  - **死参数/恒绿退出码**：**S-E56** `triz_benchmark` 恒 `return 0`（有 FAIL 也绿）→ 语义化退出码；
    变异 Q1 首轮未捕获 → 补「实跑 main()」用例（自测只验函数不验退出码 = 判别力缺口）·
    **S-E57** `split` 参数定义后从未读取（训练/评测集划分形同虚设 → 数据泄漏风险）→ 二值校验 + holdout 只留 L2；
    用例基线分离（b-01 不再共用 l2 求值目录，L1 综合分 0.750 → 1.000）·
    **S-E58a** 回归报告 run_dir 原样写入（换机不可复现）→ 包内相对化 + `--no-report-write` 求值不污染基线。
  - **零门禁覆盖**：**S-E58b** 6 脚本补 `--self-test`（check_claim_scope 13 / cost_profile 18 / failure_memory 18 /
    patent_knowledge 17 / spawn_watchdog 15 / triz_benchmark 19）——自测过程**暴露两个真缺陷**：
    cost_profile P90 非标准 nearest-rank（系统性高估一位）；spawn_watchdog 判定逻辑双份。变异 R1-R5 全捕获。
  - **验收侧红线缺失**：**S-E59** `forbidden_boundary` 只在下发侧（S-E11 半截工程），验收侧零机械校验
    → 新增 `scripts/boundary_guard.py`（5 信号 × 角色矩阵，判据基于产出结构，verdict 四态，
    **不可判定 ≠ 放过**）；收尾审计又修 3 处判据缺陷（假绿用例 / 前置窗口漏后置引用线索 / 分支重叠）。
    变异 **19/19** 全捕获。
  - **假放行防线**：**S-E60** threat_grade 只看最新一份产出——查新多轮迭代时复检轮只引用首轮结论，
    首轮 X 级**完全不被计数** → C3 不触发 → **假放行**（比假阻断危险）→ `scan_member_grades()` 聚合全部产出
    + 跨文件去重（真实基线实测：只看最新 X=0，聚合 X=5 正确触发 C3）·
    **S-E61** `PAT_NO_RE` 只支持字母尾码 → 申请号形态 `CN202311321256.8` 全漏计（真实基线 13 处）
    → 尾码与校验码**二者必居其一**，纯数字号段不计；patent_knowledge 显式化消费方过滤义务（申请号不入族谱库）。
  - **判别力验收**：boundary_guard 变异 19/19 + threat_grade 变异 12/12 全捕获（首轮 3 项逃逸 →
    补强用例后重测通过——「引用上游评级」用例系假绿：文本形态不匹配评级正则，从未经过引用排除分支）。
  - **本轮登记**：版本 2.10.0 → **2.11.0**；preflight 第 8 项判据升级（宽松正则 → 唯一真源聚合）。

- **第5轮全面排查新增 8 条（S-E62…S-E69）· 全部清偿（v2.11.1 · 2026-11-09）**
  （历史结论一律作废，全部从代码与实测重新取证；两路子智能体审计超时失效 → 主线程独立取证）：
  - **P0 幽灵执行点**：**S-E62** 全仓 grep `boundary_guard` 仅命中文档与脚本自身，
    pre-commit 四层门禁 / release-sync 三 gate 均未调用；10 个 `--self-test` 脚本
    仅 `agent_ci_gate` 被覆盖 → 新增 `scripts/self_gate.py` 汇总 14 项门禁，
    宿主 hook 与 release-sync 条件式接入（其余 5 包零影响）。端到端实测改坏
    `c3_should_trigger` → 门禁 1/4 未通过 → 禁止推送。
  - **P0 fail-open**：**S-E63** `boundary_guard` 空集（产出命名不符 glob）与
    全 `unknown_role` 均 RC=0，与脚本第 18 行「无法判定 ≠ 放过」矛盾 →
    抽 `judge_exit_code()` 真源、默认 fail-closed（RC=2），
    显式逃生阀 `--allow-undetermined`；顺带消除「越界→return 1」逻辑双份。
  - **P0 自测假绿**：**S-E64** `evolution_log.py self-test` 恒 RC=1——
    四探针共用固定早时间戳 `2026-11-09T00:00:00`（台账末行 `14:06:52`），
    合规样本被「时间倒序」误判，另三探针也全靠时间倒序被检出、
    **没测到各自声称的判据**；更深层是 `probe()` 复刻判定逻辑、
    从不调用真实 `cmd_verify`（形态 C）。抽 `validate_rows()` 唯一真源，
    探针改纯内存 + 动态时间戳 + 逐条校验特定判据关键词（7 类）。
  - **P1/P2**：**S-E65** `scan_member_grades` 的 unreadable 被 determined
    后写覆盖（实测 1 坏 1 好 → verdict=determined，损坏产出静默吞掉）→
    严重度优先 + `unreadable_files` 落 detail ·
    **S-E66** `OPERATIONS.md:68-74` 四个幽灵 self-test 条目（实测全 RC=2）→
    改指向 `self_gate.py:GATES` 唯一真源 ·
    **S-E68** 文档手抄用例数漂移（20 用例 vs 实 22）→ **彻底删除手抄数字**，
    工具表补 `self_gate.py`（21/21 覆盖）。
  - **C4 再诊断新增**：**S-E69** `self_gate` 清单只做单向校验——注入带
    `--self-test` 的 canary 脚本后自测仍 RC=0 → 漏挂不会被发现。
    与 S-E54 同型，解法同为**双向差集**（`discover_selftest_scripts()`），
    顺带修掉子命令形态条目跳过参数校验的缺口。实测注入 canary → RC=1
    且精确点名文件，移除 → RC=0。
  - **判别力验收**：全套变异 **32/32 零逃逸**（evolution_log 8 +
    boundary_guard fail-closed 8 + threat_grade/boundary_guard 关键真源 16）；
    首轮 W3/W8 逃逸分别定位出「逻辑双份」与「自测自身可短路」，
    均补强用例后重测通过。
  - **本轮登记**：版本 2.11.0 → **2.11.1**；宿主门禁链升为 **4 gate**
    （第 4 项 = `self_gate.py`）；新增 `scripts/self_gate.py` 工具。
