# Changelog

All notable changes to the **TRIZ Invention Team** will be documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
