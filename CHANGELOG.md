# Changelog

All notable changes to the **TRIZ Invention Team** will be documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-09-10

### Added
- **`agent-protocol` skill**: JSON Schema formalization of `result_envelope` (member → lead) and `task_payload` (lead → member) contracts. Schema files: `skills/agent-protocol/result_envelope.schema.json` + `task_payload.schema.json`
- **CI gate script** (`scripts/agent_ci_gate.py`): Stack-balanced JSON extraction, manual fallback validation (no `jsonschema` library required), legacy archive whitelist, `--strict` mode, `--self-test` mode
- **Token budget checker** (`scripts/token_budget_check.py`): Validates H1 context assembly budget (≤20K tokens) per member
- **`docs/OPERATIONS.md`**: Cross-session recovery playbook (cat> heredoc, settings.json timing-issue workarounds)
- **Dual plugin manifest**: Both `.claude-plugin/` (Claude Code / GitHub Copilot CLI) and `.codebuddy-plugin/` (WorkBuddy) coexist; `marketplace.json` in both
- **Bilingual README**: English (`README.md`) + Chinese (`README.zh.md`)
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
