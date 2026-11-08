# Changelog

All notable changes to the **TRIZ Invention Team** will be documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-11-08

> 工作区整理 + 残留全清偿（11 个 commit：8285208…b43d2de）。第三轮诊断残留 8 项全部闭环。

### Changed（工作区整理）
- **基线资产归位**：包根游离 `darwin-results.tsv` 按 CHANGELOG 2.2.0 声明补迁移至 `docs/evolution-log.tsv`（该声明当时未实际执行，README.zh.md 引用悬空至今）
- **回归基线归档**：`outputs/regression-*` → `tests/baselines/{l2-full-a01, l1-analyst-b01, 20261014-p0-2, _pre-fix-b01}` + spawn 文案打包 `_archive/`；新增 baselines/README 导航；outputs/ 目录整体移除
- **10 个活跃引用点同步**（contract_enforce 自测2 / check_claim_scope --l2 / 5 脚本示例 / 3 文档）；工具清单 13 项
- OPERATIONS §一 settings.json 判据记载订正（5.9.3 缓存版仍带判据=误报，以 register 成功为准）

### Fixed（残留清偿 8 项）
- **C01 A6 法25 断言根因修复（d4bee57）**：member_files() 对同名成员多轮产出只留最后文件（A03 复检覆盖 A01 首轮）曾致永久误判——check_required_regex 新增 `any_member` 模式，C01 首次 8/8 全 PASS
- **U3 outdated 子命令（b0dddf9）**：失效标注/query ⚫显示/stats 计数，兑现 scout MD「失效反馈机制」承诺
- **D3-1 仲裁链订正 + D1 坍缩表（50d51ed）**：confidence 降为末位参考信号（不得单独裁定）；7 视角补 17 个 TRIZ 参数映射（权威 CSV 校验零越界）
- **spawn_watchdog 简版（e47a525 + b43d2de 补齐）**：四态判定（OK/WATCH/STALL/TIMEOUT）+ H4 处置建议，P2-15 债务关闭
- routing-log 单表化 + R-004 缺号登记；diagnosis-protocol 报告存放位置澄清；benchmark/cost_profile 示例改精确子目录

### Evaluated（评估后不实施）
- D4-2 himmpat 登录态探测：运行时状态不可预判，scout L2→L3 降档规则已覆盖——不实施
- 48h 回检窗口关闭：窗口内多轮门禁复跑全绿，唯一新发现（benchmark 传参混扫）非修复引入

## [2.9.0] - 2026-11-09

> **CYCLE-1 · 可持续迭代引擎（墨衡）**——针对本专家团的独立诊断 → 构建 → 测试&debug → 再诊断循环。
> 共 7 个批次 commit（3812043 → P1-4），19 项 S-E01…S-E19 首诊短板 + 第2轮交叉验证 19 条确证问题全部清偿。

### Added（新增机械能力）
- **`preflight_check.py` 第 12 项 · Workflow D 入口前置闸机械校验（S-E02）**：主理人 MD:359 曾声称
  「由 preflight 第9项机械校验」，实测 preflight 全文不含 G1/G2/G3/search_3rounds/trinity 任一字符串——
  该校验**从未存在**（幽灵验证项）。现落地真实实现：真源 = `state_store.GATE_ALIASES`，
  G1/G2/G3 全关 ∧ `state.evidence` 的查新/裁决落盘文件真实存在才放行，否则 BLOCK。新增 `--state-path` 参数。
- **`contract_enforce.py` 自测4 · DRIFT_PROBE 三源漂移反向验证（S-E21）**：CONTRACT_ENFORCEMENT.md:116
  曾声称「注入 DRIFT_PROBE → exit 1」，实测全仓仅该文档行命中、脚本内无此探针。落地真实探针：
  基线一致 → 注入 `DRIFT_PROBE_CANARY` 检出漂移（期望 exit 1）→ 镜像同步后无漂移（期望 exit 0，
  证明探针有判别力、非恒真）。
- **`agent_ci_gate.py` fallback 扫描（S-E22）**：此前只扫 `*-results.json`，全仓该类文件实测为 **0**
  → 扫描恒空、门禁恒返回 0、**从未真正校验过任何信封**（pre-commit hook ① 因此空转）。
  现回退扫基线 markdown 中的成员产出信封（`T-*__<member>.md`，排除下划线前缀的负例/归档区）。
  实测：扫描 10 个信封，合规率 100%。
- **`preflight_check.py` 第 10/11 项（S-E05/S-E09）**：诊断登记表结构完整性（断表/列数检测）·
  README 结构图与实际目录一致（按 `.gitignore` 解析后比对，对齐 git 实际入库口径）。
- **`contract_enforce.py` 自测1b（S-E11）**：`forbidden_boundary` 契约字段与角色矩阵一致性
  （schema 含该字段 · 矩阵覆盖 6 成员 · 禁止边界非空 · 角色归类一致）。
- **`agent_ci_gate.check_wall_clock()`（S-E12）**：墙钟双轨制 WARN 校验（metrics 缺
  `duration_ms_wall` / `duration_source` 非法）——不阻断，供主理人回填。
- **`evolution_log.py` 台账单源化（S-E08）**：自进化台账唯一写入口，含
  `append / backfill / verify / tail / self-test` 五子命令 + commit 确定性校验（禁 HEAD 等非确定标识）。
- **`state_store.py` `evidence` 键（S-E02）**：Workflow D 前置闸的落盘证据路径
  （`search_report` + `verdict_report`）——文件缺失 = 视为未查新。
- **`task_payload.schema.json` `forbidden_boundary` 字段（S-E11）**：下行任务的禁止边界清单
  （非 required，不破历史信封；凡下发即须填）。

### Fixed（缺陷清偿）
- **幽灵验证项 3 处（S-E21）**：preflight 第9项「门禁机械校验」· CONTRACT_ENFORCEMENT 的
  `DRIFT_PROBE` 反向验证 · `verify_triz_data.py --strict` 死参数（解析后从未被读取；现显式语义：
  strict 下 warn 也阻断，默认 warn 不阻断）。
- **门禁键名双轨（S-E01）**：`GATE_ALIASES` 别名归一（写入 `gates.G1` 自动落语义键）+ G2
  `trinity_verdict_pass` 补齐 + `run_regression.check_gates` 改精确读取（原按 dict 插入序取前 N 值
  → 假阴性 → Phase5 永远卡死）。
- **契约 fail-open（S-E15）**：违规默认即 `exit 1`，无需 `--exit-on-fail`。
- **preflight 假绿（S-E16）**：`checked=0` 时不再输出「全部存在」。
- **单字禁词误伤（S-E20）**：`可能` / `估计` 等单字在否定与风险语境误伤合法技术表述 → 豁免词限定。
- **回流硬闸（S-E10/S-E18）**：`reset_for_rework` 重置门禁 + `loopback_count` 累计（上限 2，超限升级 L4）。
- **Phase 2.5 状态节点（S-E19）**：汇聚校准纳入 `PHASE_NEXT` 状态机。

### Changed（口径同步）
- **架构文档四方位对齐（S-E24/S-E25/S-E26/S-E27）**：§3.2 state 模板补全至 5 gates +
  4 metrics 字段 + `evidence` 键（对齐 `state_store.py` 单一权威）；§3.5 改为墙钟双轨制
  （`duration_ms` 成员自报 / `duration_ms_wall` 主理人实测，禁止互相覆盖）；§6.2 L3 仲裁链
  confidence 降为末位参考信号（同步 D3-1 订正，2026-11-08 只落到 MD 未同步架构文档）；
  §4.1 task_payload 示例补 `forbidden_boundary`（schema `additionalProperties:false` → 按原示例
  下发会被拒）。
- **工具清单口径**：OPERATIONS §三 10 → 18 个脚本（补 `diagnosis_trigger.py` / `evolution_log.py`
  两行）；preflight 项数 8 → 10 → **12**（README.md 与 OPERATIONS.md 曾互相矛盾且都落后）。
- **门禁报告输出位置**：`agent_ci_gate` 报告从 `tests/baselines/` 迁至 `outputs/`
  （基线目录是只读真源，门禁产物属派生数据）。
- **README 口径**：阶段标题 6 阶段 → **7 阶段节点**；成员数统一「7 名智能体 = 1 主理人 + 6 成员」；
  结构图按实测重绘（补 `.gitignore` / `knowledge/` / `vendor/` / `.learnings/` / `tests/{cases,baselines}`）。
- **失效引用修正**：`outputs/` → `tests/baselines/`；`plugins/triz-invention-team/*` → 仓库根相对路径；
  删除不存在的 `scripts/register_expert.py` 与技能包名 `triz-patent-toolkit`（实际 4 个技能包）。
- **双 marketplace.json description 版本同步**：v2.6 / v2.7 → v2.9（version 字段本已是 2.8.0）。

### Evaluated（评估后不实施）
- `marketplace.json` 的 `source: "./plugins/triz-invention-team"`：本仓 git 根为平铺布局（无 `plugins/`
  嵌套层）。本地安装（`my-experts` 市场根含 `plugins/`）正常；**单仓 GitHub 安装**会指向不存在目录。
  C4 再诊断登记为待办项，本轮不擅自改动发布路径语义。

### 验收证据（机械实测）
- 9 项门禁全绿：`verify_triz_data --strict` · `agent_ci_gate --strict` · `agent_ci_gate --self-test` ·
  `contract_enforce --self-test` · `state_store self-test` · `test_vendor_core` · `preflight_check` ·
  `skill_test_runner` · `evolution_log verify`
- 三用例回归零回退：A 7/7 PASS · B 7/8 PASS + 1 INFO · C 8/8 PASS
- preflight 第 12 项三分支实测：门禁未关 → BLOCK(exit 1) · 证据缺失 → BLOCK · 全关+证据齐 → PASS(exit 0)
- 交叉验证 2 轮：第 1 轮 18 脚本 `--help` 无崩溃 + 13 JSON 合法；第 2 轮从零视角复读产出 19 条确证问题
  （🔴 8 · 🟡 7 · 🟢 4），本轮全部清偿

## [2.8.0] - 2026-11-07

> 第三轮独立诊断（triz-team-diagnosis-independent-20261107-r3.md · 11 维度从零基准）R1-R5 修复 + U1-U3 升维（用户 11-07 确认全量执行）。

### Fixed（R1-R5 · 14 项短板）
- **契约豁免机制重建（R1 · D7-1 高危）**：3 成员 frontmatter 的 `.*?(?!...)` 负向前瞻豁免
  经实测全部为死代码（`.*?` 匹配空串时前瞻恒成立，豁免从未生效）——删除前瞻、禁词纯净化，
  豁免职能收敛到 `contract_enforce.py` 新增 CONTEXT_EXEMPT 上下文窗口豁免表（基本X搭配/
  效果词附证据/约束约定节约复合词/估计否定语境）；`--self-test` 自测3 六组双向断言
  （豁免样本放行 ∧ 违规样本命中）；历史产出回归 exit=0 零误伤
- **路由落盘提醒回链（R2 · D2-1 高危）**：CHANGELOG 2.3.0 声明的 RoutingDecision 提醒在
  v2.4.0 下沉联邦时丢失（联邦真源 0 处该字样）——联邦 core assemble() 尾部注入提醒行 +
  主理人 MD 双保险 + 5 包 vendor 同步（sha 3c3648f1）V1-V6 全 PASS
- **预算口径统一（R3 · D4-1）**：主理人 MD H3.5 注释改「弹性上限120K / L2实测基线84K」
  与 preflight 同口径；**routing-log 单表化（R3 · D2-2）**：断表合并 + R-20260930-004
  缺号登记（无据不编造）+ R-20261015 系列 13 行结果列按证据回填
- **禁词第三源归一（R4 · D7-2）**：run_regression forbidden_regex 支持
  `patterns_source=frontmatter` 动态读真源 + 清洗/豁免与 contract_enforce 同构
  （import 复用 _clean_for_forbidden_scan + EXEMPT_WORDS + _context_exempt——
  B01 首跑 4 处误命中正是两套工具行为漂移的实证，同构后 PASS）
- **登记表回检列（R4 · D6-1）**：诊断登记表增设「48h 回检」列；历史回填教训——
  v2.4.0 联邦下沉丢路由提醒正是缺回检的代价
- **.learnings 启用（R4 · D6-2）**：首两条（BSD grep 假阴性 high + 前瞻豁免死代码 critical）
- **SUMMARY 日期豁免（R5 · D5-1）**：早于 20261015 规范生效日的产出豁免格式告警；
  **resume 路由行规范（R5 · D10-1）**：中断续接须补 task_type=resume 决策行

### Added（U1-U3 · 升维三项）
- **成本感知调度（U1）**：`scripts/cost_profile.py`——metrics.jsonl 聚合成员成本画像
  （n/成功率/tokens 均值·中位·P90/墙钟均值·P90/覆盖率 + ΣP90 预算对照）；主理人路由协议
  增成本因子提示（P90 做预算线/重成员谨慎派/n<3 标样本不足）
- **语义禁词两级门禁（U2）**：`contract_enforce.py --llm-review`——机械层负责「抓」
  （秒级零成本），主理人 LLM 层负责「判」（复核清单：命中行+上下文+复核问题）；
  承认正则无法表达语义边界，判定权交还语义引擎
- **专利族谱记忆（U3）**：`scripts/patent_knowledge.py`——scout 产出 X/Y 威胁机械提取入库
  （幂等去重 patent_no+domain）+ 域/关键词召回（X级排前）+ 失效反馈机制；
  a01 产出初始化 16 条（X5/Y11）；召回=已知雷区先验**不替代三轮查新**；
  Phase 3 前召回预热 + 查新后沉淀——一次性查新升维为积累式查新记忆

### 残留（诚实登记）
- workflow-c-01「法25」断言 FAIL 为历史基线问题（断言按三轮独立产出设计 vs a01 紧凑模式单文件），待用例适配
- spawn_watchdog（P2-15）未建，H4 人工规则顶替
- 联邦 3 包 vendor 已同步含 R2 提醒但各自仓库未提交（提交权留各包活跃会话）
- U3 修复过程自曝并修正 2 处提取正则缺陷（节标题编号在前/专利号尾码 U 漏配）——已入库验证

## [2.7.0] - 2026-11-07

> 独立再诊断 Batch 4-5：检索源改造 + 升维两项（用户 11-07 确认）。

### Added
- **检索源冗余降档（Batch4）**：主源 Google Patents + himmpat（Chrome 登录态），
  L1→L4 逐级降档链（每级登记降档原因 + confidence 折减 L2-5/L3-10/L4-15）；
  凭记忆红线不因降档豁免；scout 新契约「检索渠道显式」（生效日 2026-11-07，
  `_scoped` 日期作用域不追溯——历史归档基线稳定）
- **A-Evolve benchmark 适配（Batch5B）**：`scripts/triz_benchmark.py`——tests/cases 三用例
  → `TrizBenchmark`（get_tasks/evaluate 鸭子类型接口，不硬依赖 a-evolve 包）；
  独立求值模式可直接算分（score=断言通过率，success 线 0.75）；演化闭环打通
- **包内 .learnings/ 三件套**（Batch3）：self-improving-agent 规范（LEARNINGS/ERRORS/FEATURE_REQUESTS）
- **诊断协议固化（Batch3）**：`docs/diagnosis-protocol.md`——触发器 T1-T4 / 10+1 维清单 /
  证据纪律 / 批次修复纪律 / 诊断登记表

### Fixed（Batch5A · 联邦层）
- **shared-core vendor 态 expert_dir 反推死路**：`resolve_expert_dir` 在 core 位于
  `<pkg>/vendor/shared-core/` 时反推到 `vendor/`（无 agents/）→ exit 3。
  修复：用 `__file__.parts` 匹配相邻 vendor/shared-core 段上跳到包根
  （注意 `parent.parent` 后 parts 里已无 shared-core 段——初版修复即栽在此，调试脚本实证）。
  联邦真源 + 4 包 vendor 副本 + VENDOR.json 清单全量同步，V1-V6 6/6 PASS
- **run_regression 三处断言锚点**（Batch3）：gates 语义匹配（旧版只查字面 G1-G5，
  A01 实际用语义表述 → 假阴性）/ abstract 摘要正文段优先锚点 / subprocess 导入缺失
- **L2 断言首次机械全跑 7/7 PASS**（含新 A7 conditions_closed 条件对账）

### Changed（Batch1-3）
- 契约禁词单源化：唯一真源=成员 frontmatter `forbidden_phrases`（脚本启动解析）；
  CONTRACT_ENFORCEMENT.md 全验证项标注 `[机械已实现]`/`[暂缓·人工执行]`
- TASK_STATE 持久化：`scripts/state_store.py`（init/update/show/resume）+ scaffold 自动初始化
  + 主理人 SOP H2 落盘硬规则；envelope schema v1.2.0 增可选 `verdicts{result,score}`
- 预算经验值按 L2 实测校准 111K→84K（92%→70% 预警消除）；H3 软终止评分机械分优先

## [2.6.0] - 2026-11-07

> 独立再诊断（11 维度·11-07）Batch 1：契约单源化 + 文档对齐。含此前未入账的 3 个 commit。

### Added
- **契约禁词单源化（S-Q1）**：`contract_enforce.py` 启动时解析各成员 frontmatter
  `forbidden_phrases` 为唯一真源（删除脚本自维护副本）；`--self-test` 新增三源一致性检查；
  解析失败显式告警不静默
- **验证项实现状态标注（S-Q2）**：`CONTRACT_ENFORCEMENT.md` 全部验证项标注
  `[机械已实现]` / `[暂缓·人工执行]`，消除幽灵验证项；scout「应用号」笔误修正为「申请号」

### Changed
- **架构文档编排对齐（S-C1）**：`architecture.md` §五任务分配表标注编排权威=主理人 SOP
  P2-10 白名单（W1/W2），删除已被取代的"Phase1-2‖Phase3 泛并行"旧实例
- **routing-log 表格修复（S-C3）**：R-004 起断裂在"复盘笔记"后的表格行归位到表结构
- 6 成员 frontmatter 禁词表归一（含新增 `(显著|大幅|明显|高效).*?(?!附实测|附数据)` 等）
- anti-pattern 豁免链补 3 条实测漏配（"而非凭记忆/无一处凭记忆/红线："），L2 全量 13/13 PASS

## [2.5.4] - 2026-10-30 ~ 11-04（补录）

> 此前未入 CHANGELOG 的 3 个 commit（S-Q5）。

- `623a19e` vendor 同步：shared-core B21 升级（check_task_package_v5 结构化校验，联邦真源 1809085da349）
- `91be1a1` fix: 移除 settings.json（宿主 ExpertPluginService 删除判据命中）
- `90d04bd` fix: 订正 settings.json 恢复playbook（宿主删除机制）+ vendor 清单基线刷新
  （详见 `docs/OPERATIONS.md` §二 · failure-005 结案记录）

## [2.5.3] - 2026-10-15

> 独立诊断（triz-team-diagnosis-independent-20261015.md）P0 三项 + 两项遗留债清偿。

### Added（P0）
- **S4-1 五包 vendor 兜底**：viral-evo-lab / research-orchestration-team / smart-textbook-team /
  vet-med-ppt-team 各自获得 vendor/shared-core 三件套 + 防漂移门禁（V1-V5 PASS）；
  分发工具沉淀至 `shared-core/scripts/distribute_vendor.py`
- **S1-1 六成员契约化**：6 成员 frontmatter 增 5 字段（schema_version/contract_owner/
  verified_at/forbidden_phrases/must_verify）；`docs/CONTRACT_ENFORCEMENT.md` +
  `scripts/contract_enforce.py` 门禁（L2 八阶段产物 10/10 PASS，含豁免链：
  元数据标记/通用豁免词/反例引用/学术表达）
- **S3-1 C3 自动触发**：preflight 7→8 项（`--after-search/--outputs-dir/--c3-confirmation-path`）；
  X 级出现且无确认件 → 阻断（3 场景实测）

### Fixed（遗留债）
- pre-commit 钩子增第④层：契约门禁（touches 成员产物时自动跑 contract_enforce）
- `distribute_vendor.py` 入库 shared-core（新增包接入联邦一条命令）

## [2.5.1] - 2026-10-15

> L1 回归（workflow-b-01）首跑暴露的契约一致性缺陷修复（failure-008）。

### Fixed
- **task_id 契约漂移（failure-008）**：`run_regression.py` scaffold 曾生成违约 ID（`T-<date>-REG-B01`，
  第三段含连字符，违反 `result_envelope.schema.json`）→ ①改为合规 ID（`T-<date>-B01`）②新增自校验：
  读取 schema pattern，违约即 exit 2 拒绝生成（fail fast）
- **`token_budget_check.py` FILENAME_RE 过窄**：仅接受 `\d{3}` 数字后缀，比 schema 契约更窄 →
  合法字母数字 ID 被 `--meter` 静默跳过（表现为计量 0 行）。已放宽为与 schema 对齐的 `[A-Za-z0-9]{1,8}`
- **`agent_ci_gate.py` 重复 `extract_envelopes` 定义**：删除死代码（1505 字符），保留版加来源注释；`--self-test` 复验通过

### Added
- **L1 回归首跑通过**（`tests/baselines/l1-analyst-b01/`）：7/8 断言 PASS（1 INFO）；机械计量
  20,018 字符 / ≈10.8k out-tokens / 墙钟 321s（lead_measured）；`_VERIFY.md` 含完整证据链
- `tests/baselines/_pre-fix-b01/`：首跑违约 ID 产物归档 + NOTE 说明（缺陷发现即价值）

## [2.5.0] - 2026-10-15

> 完成 2026-10-14 五维诊断的 P2 全项（P2-9~P2-12）+ 补 commit 级门禁。
> 上游 P0-1~P0-3、P1-4~P1-8 见 [2.4.0]。

### Added
- **`scripts/run_regression.py` + `tests/` 回归测试集（P2-9）**：3 个固定用例
  （workflow-a-01 全链路 L2 / workflow-b-01 analyst L1 / workflow-c-01 scout L1）+
  12 种断言引擎（任务包四要素 / 信封 6 必填（栈平衡提取）/ 模糊词零命中（自动剔除
  代码块与自检行防 failure-006 假阳性）/ 摘要机械计量 / 门禁登记 / 预算汇总等）。
  用法 `--list | --scaffold | --case X --dir <run>`，报告落盘 `regression_report__*.json` 可跨轮对比。
- **`scripts/failure_memory.py`（P2-12）**：episodic 失败记忆注入器——按「本次派单成员 +
  任务域关键词」从 `~/.workbuddy/expert-failures/` 运行时筛出 learned_rule 摘要，
  供主理人追加到 spawn 文案（永远最新，替代静态抄写）。
- **`~/.workbuddy/git-hooks/pre-commit`（P1-6 补全 · commit 级门禁）**：三层快速校验——
  ① `agent_ci_gate.py --strict` ② `scripts/*.py` 语法 ③ 装配链 `--list-members` 冒烟
  （防 shared-core 断链类事故）；硬失败阻断提交。与既有 push 级门禁（release-sync.sh
  `run_gates` 三闸）构成 commit→push 双层防护。
- **并行与预装配协议（P2-10 · 主理人 MD）**：① 预装配流水线强制（等待窗口完成下一
  成员的装配/预读，重叠开销）② 并行白名单 W1 独立咨询 / W2 盲态双审（默认关闭，
  启用须登记对账段）③ 禁用清单（有依赖的串行对禁止假并行）④ routing-log 记录义务。

### Changed
- **主理人 MD 人设注入协议：强制三步 → 强制四步**（新增第 2 步「失败记忆注入」）
- **Phase 3 查新并行化评估结论（P2-11）**：三轮串行为设计约束不做轮间并行；
  新增可选「紧凑模式」（R2+R3 合并为单次 spawn，省 ≈3-4 分钟；须满足区别特征
  明确 + 时间紧迫两条件，默认不启用）

### Fixed
- 回归用例 workflow-b-01 首次冒烟即捕获 1 处「快速」模糊词违规（既有产出），
  验证断言引擎有效（非回归引入）

## [2.4.0] - 2026-10-14

### Added
- **耗时指标双轨制**：`result_envelope` schema v1.0.0 → v1.1.0，新增 `metrics.duration_ms_wall`（主理人实测墙钟）与 `metrics.duration_source`（`self_report|lead_measured|estimated`）
- **`scripts/preflight_check.py`**：团队启动前检查脚本化（7 项：失败索引命中 / routing-log 可写 / 预算估算 / Phase0 五参数 / 权威数据 / 装配器可用 / skills 路径存在），退出码 0=可启动、1=阻断
- **`scripts/verify_triz_data.py`**：TRIZ 权威数据自检（A 矩阵1521交叉点 B 参数39行 C 中文表译名不重复 D 权威锚点复算）
- **路由日志「结果」列**：13 行回填，无据行显式标注「—（无据未补）」禁止凭印象编造
- **发布门禁接入 release-sync.sh**：推送前必跑门禁，不过即阻断（逃生阀 `RELEASE_SYNC_SKIP_GATE=1`）

### Fixed
- **39 参数中文表 #34/#35 译名错位**（failure-007）：#34 Ease of repair 曾误作「装置复杂性」、#35 误作「监控与测试的复杂性」。因查询器把译名拼进输出，错误直接注入成员上下文 → 已改「可维修性」「适应性及多用性」
- **耗时失真规则假阳性**：自报 0 + issues 注明「无法自估」原被判失真 → 改为「未自报」豁免分支（规则若惩罚诚实，下一步就是逼出编造）
- **manifest 版本漂移**：`.codebuddy-plugin` 2.3.0 / `.claude-plugin` 2.2.0 → 三处统一 2.4.0

### Changed
- `assemble_spawn_prompt.py` 下沉 shared-core 联邦共享件（369 行 → 45 行 shim，4 包共用一份真源）；6 成员装配输出 md5 新旧逐一一致，零回归

## [2.3.0] - 2026-09-30

### Added
- **v2.3 装配链**：`RoutingDecision → assemble_spawn_prompt.py → Agent spawn → 落盘验收 → VERIFY`，派单必经脚本
- **H4 平台级错误类**：429/配额耗尽 → 停派同批后续成员 + 三选一降级
- **H3.5 全局预算**：≤120K token / ≤45min / 单成员重试≤4 / 429 最多等 1 次重置
- **团队启动前检查清单 + Phase 0 工程实施参数清单**（安装方式/改造成本/维护频次/失效容忍度/已有部件）
- **路由决策协议**（RoutingDecision JSON + 三档置信度策略 + 强制落盘 routing-log）
- **12 条 RoutingDecision 真实记录**（协议上线后首批，此前为零）

### Fixed
- **triz-matrix 数据准确性灾难**（failure-001 根治）：12 条速查表经核对 0/12 与权威矩阵相符 → 废弃，改为 1521 交叉点权威 CSV + 确定性查询器 `query_triz_matrix.py`，覆盖率 0.8% → 82.1%
- **ACP 双协议跨团队根治**（failure-003）：research / smart-textbook 共 12 成员统一 `result_envelope` v2.4
- **摘要长度门禁被突破**（failure-006）：自评 281 字 vs 实测 371 字符 → 重写 240 字符 + CI gate 机械校验
- **同阶段 handoff 协议冲突**：9-18「有限放开」与 9-29「横直连禁止」矛盾 → 统一为同阶段接力也经主理人中转

## [2.2.0] - 2026-09-10

### Added
- **`agent-protocol` skill**: JSON Schema formalization of `result_envelope` (member → lead) and `task_payload` (lead → member) contracts. Schema files: `skills/agent-protocol/result_envelope.schema.json` + `task_payload.schema.json`
- **CI gate script** (`scripts/agent_ci_gate.py`): Stack-balanced JSON extraction, manual fallback validation (no `jsonschema` library required), legacy archive whitelist, `--strict` mode, `--self-test` mode
- **Token budget checker** (`scripts/token_budget_check.py`): Validates H1 context assembly budget (≤20K tokens) per member
- **`docs/OPERATIONS.md`**: Cross-session recovery playbook (cat> heredoc, settings.json timing-issue workarounds)
- **Dual plugin manifest**: Both `.claude-plugin/` (Claude Code / GitHub Copilot CLI) and `.codebuddy-plugin/` (WorkBuddy) coexist inside `plugins/triz-invention-team/`
- **Single-plugin marketplace layout**: repo root carries the two `marketplace.json` descriptors, the plugin lives self-contained under `plugins/triz-invention-team/` — installable straight from GitHub on Claude Code, GitHub Copilot CLI, and WorkBuddy (`/plugin marketplace add virologist/triz-invention-team`)
- **Bilingual README**: English (`README.md`) + Chinese (`README.zh.md`)
- **`.gitignore`** covering OS / editor / Python / backup / secrets artifacts
- **`docs/evolution-log.tsv`**: self-evolution score history (previously a stray root-level TSV)
- **Apache-2.0 LICENSE** with explicit patent grant
- **CI gate documentation** with typical pitfalls A-D (spawn context stickiness, member no-reply, validate timing, TeamCreate re-spawn)

### Changed
- **Adaptive interaction mode** added to lead agent (interactive vs. autonomous execution)
- **Phase 2.5 fan-in calibration** explicit: search round-1 results must recalibrate analyst directions before round-2
- **Patent portfolio strategy** (core / peripheral / alternative) required at Phase 2 output
- **Embodiment range design hard rule**: numeric ranges require ≥3 data points (end×2 + middle×1) per CN Patent Law Art. 26.3-26.4
- **Tier-break interest-conflict boundary** added: when second-opinion is itself a disputant, escalate L4 directly with conditional-merged verdict (avoids deadlock)
- **Member MD hard constraint** for `result_envelope` (single-point definition in `agent-protocol` SKILL.md; members only reference)

### Fixed
- **B-001** (contract duplication): 6-member MD hard-constraint block (135 chars × 6) replaced with single-point reference + authoritative definition in `agent-protocol/SKILL.md`
- **Validator message format** now uses stack-balanced JSON extraction (handles nested envelopes correctly; was failing on 11/20 archives with regex-based extraction)

### Quality
- CI gate compliance rate: **100%** (24/24 post-v2.2 archives; 5 legacy pre-v2.0 archives exempt by design)
- RedTeam 5-focus diagnosis (responsibility conflict / chain breakage / resource waste / context loss / tool errors): **0 critical bugs**
- All 6 member MDs confirmed boundary compliance via spawn testing
- 2 members (attorney + disclosure) correctly return `status: blocked` on empty upstream input

## [2.0.0] - 2026-08-29

### Added
- Harness 5-layer architecture (H1-H5): Context Assembler, State Store, Loop Controller, Error Recovery, Observability
- Interface contract: result_envelope JSON + task_payload JSON
- Failure index mechanism (12-Factor XII) → `~/.workbuddy/expert-failures/`
- State machine (SOP 6-phase)
- L1-L4 conflict arbitration priority chain
- Member contract: role / capabilities / boundary / output verification

## [1.5.0] - 2026-08-28

### Added
- TRIZ matrix skill (39 parameters, 40 principles, ARIZ-85C, 76 standard solutions)
- Patent law skill (CN Patent Law Art. 22.2/22.3/22.4)
- Claims drafting skill
- Mock examination (严三性) + second-opinion review (审外审)
- Disclosure architect five-element structure
- Patent attorney writer self-check (no ambiguous words, claim dependencies, ≤300-char abstract)

## [1.0.0] - 2026-08-15

### Added
- Initial 7-member team scaffold (lead + analyst + scout + examiner + disclosure + attorney + second-opinion)
- Basic 6-phase SOP
- Single workflow (workflow A)
