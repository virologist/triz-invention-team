# Changelog

All notable changes to the **TRIZ Invention Team** will be documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **L1 回归首跑通过**（`outputs/regression-20261015/b01/`）：7/8 断言 PASS（1 INFO）；机械计量
  20,018 字符 / ≈10.8k out-tokens / 墙钟 321s（lead_measured）；`_VERIFY.md` 含完整证据链
- `outputs/regression-20261015/_pre-fix-b01/`：首跑违约 ID 产物归档 + NOTE 说明（缺陷发现即价值）

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
