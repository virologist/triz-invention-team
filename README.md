# TRIZ Invention Team (v2.2)

> **Cross-domain TRIZ invention team**: from contradiction modeling → three-round patent search → mock examination → disclosure and patent application drafting for **CN invention patents**.

A multi-agent system that collaborates like a real invention team — a director orchestrates, a contradiction analyst applies the 39×39 TRIZ matrix, a search scout runs three rounds of prior-art search, a mock examiner attacks novelty/inventiveness/utility, a second-opinion reviewer runs independent re-examination, a disclosure architect structures the invention into a five-element disclosure, and a patent attorney writer drafts the claims, description and abstract.

This v2.2 release formalizes the inter-agent contract as a JSON Schema (`agent-protocol`) and ships a CI gate script that automatically verifies all agent outputs against the schema before they can pass downstream verification.

---

## ✨ Highlights

- **7 specialists + 1 director**: Each agent has explicit role boundaries (ANALYZER / EXECUTOR / REVIEWER) and an enforcement rule against out-of-scope output.
- **TRIZ 39×39 contradiction matrix + 40 invention principles** (with downgrade path for off-table pairs)
- **Three-round prior-art search** with X / Y / A / R / P threat classification
- **Mock examination with independent second-opinion** — automatically catches confirmation bias
- **Patent portfolio strategy** (core / peripheral / alternative lines) for stronger protection
- **Embodiment parameter range design** — every numeric range backed by ≥3 data points (end × 2 + middle × 1) per CN Patent Law Art. 26.3-26.4
- **JSON Schema contract** with `agent_ci_gate.py` CI gate — 100% compliance rate (deducting legacy archives)
- **Cross-platform plugin format**: dual-manifest (`.claude-plugin/` + `.codebuddy-plugin/`) compatible with Claude Code, GitHub Copilot CLI, and WorkBuddy

---

## 📦 Installation

### Option A — Claude Code / GitHub Copilot CLI

Add this repo as a private marketplace:

```bash
# Inside Claude Code or Copilot CLI
/plugin marketplace add biodog/triz-invention-team
/plugin install triz-invention-team@triz-invention-team-marketplace
```

Or with `claude` CLI:

```bash
gh repo clone biodog/triz-invention-team ~/claude-plugins/triz-invention-team
claude --plugin-dir ~/claude-plugins/triz-invention-team
```

### Option B — WorkBuddy

```bash
# Place under WorkBuddy marketplaces directory
mkdir -p ~/.workbuddy/plugins/marketplaces/triz-invention-team
cp -R ./* ~/.workbuddy/plugins/marketplaces/triz-invention-team/
# Restart WorkBuddy; the team will appear under "Expert Teams"
```

---

## 🚀 Quick Start

Once installed, send any one of these starter prompts to the director `Qi Chuangjian`:

| Prompt | What happens |
|--------|--------------|
| *"I have an invention idea. Guide me from TRIZ contradiction analysis to a patent application draft."* | Full Workflow A: 0→1 invention pipeline |
| *"My design has a contradiction: improving X worsens Y. Use the contradiction matrix to generate invention directions."* | Workflow B: single-point TRIZ breakthrough |
| *"I have a technical scheme. Run three-round prior-art search and assess novelty/inventiveness/utility."* | Workflow C: patentability assessment |

The director will run a Socratic Phase 0 (≤5 rounds × ≤5 questions) to lock in domain context, then schedule the rest of the team.

---

## 👥 Team Composition

| Member | Role | ID |
|--------|------|----|
| **齐创见 Qi Chuangjian** | Director · Phase 0 Socratic lock-in · orchestration | `triz-invention-team-team-lead` |
| **解其纷 Xie Qifen** | TRIZ contradiction analyst · 40 invention principles | `contradiction-analyst` |
| **甄无遗 Zhen Wuyi** | Prior-art search · three rounds (keyword → IPC/CPC → differential) | `patent-search-scout` |
| **严三性 Yan Sanxing** | Mock examiner · X/Y/A threat attack · green/yellow/red verdict | `patent-examiner-sim` |
| **审外审 Shen Waishen** | Independent second-opinion · conflict-of-interest-aware | `second-opinion-reviewer` |
| **谭无隐 Tan Wuyin** | Disclosure architect · five-element structure · ≥3 gaps | `disclosure-architect` |
| **权要达 Quan Yaoda** | Patent attorney writer · claims + description + abstract | `patent-attorney-writer` |

---

## 🧠 Skills Bundled

- **`triz-matrix`**: 39×39 contradiction matrix, 40 invention principles, ARIZ-85C
- **`patent-law`**: CN Patent Law Art. 22.2 / 22.3 / 22.4 (novelty/inventiveness/practicality)
- **`claims-drafting`**: Claim writing guide + disclosure template (CN invention patent)
- **`agent-protocol`**: JSON Schema for `result_envelope` + `task_payload` + CI gate

---

## 🛠️ Repository Structure

```
triz-invention-team/
├── .claude-plugin/         # Claude Code / Copilot CLI manifest + marketplace
│   ├── plugin.json
│   └── marketplace.json
├── .codebuddy-plugin/      # WorkBuddy manifest + marketplace
│   ├── plugin.json
│   └── marketplace.json
├── agents/                  # 7 agent role definitions (Markdown)
├── skills/                  # 4 skill packages
├── scripts/                 # CI gate + token budget checker
├── docs/                    # architecture.md + OPERATIONS.md
├── avatars/                 # 512×512 agent portraits
├── settings.json
├── README.md                # ← you are here (English)
├── README.zh.md             # Chinese version
├── LICENSE                  # Apache-2.0
└── CHANGELOG.md            # release history
```

---

## 🧪 Quality Gates

```bash
# Validate the package
python3 scripts/agent_ci_gate.py --self-test          # schema self-test
python3 scripts/agent_ci_gate.py --results-dir outputs/ # CI gate over all archived test runs
python3 scripts/token_budget_check.py --conservative  # H1 context assembly budget
```

The CI gate currently reports **100% compliance** on all post-v2.2 archives (legacy pre-v2.0 archives are exempt by design).

---

## 🔄 Release Process

1. Update agents / skills / scripts
2. Run `scripts/agent_ci_gate.py --strict` to gate the commit
3. Bump version in **both** `.claude-plugin/plugin.json` and `.codebuddy-plugin/plugin.json` (semver)
4. Tag the release: `git tag v2.x.y`
5. Push to GitHub

See [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for the full cross-session recovery playbook.

---

## 🤝 Contributing

Issues and PRs welcome. Please ensure:

1. New agent prompts include a `result_envelope` JSON block per the [`agent-protocol` schema](skills/agent-protocol/result_envelope.schema.json)
2. CI gate passes with `--strict`
3. Token budget stays under 20K per agent (use `scripts/token_budget_check.py` to verify)

---

## 📜 License

Apache-2.0 — see [`LICENSE`](LICENSE). Patent grant is explicit; commercial use allowed with attribution.

---

## 🇨🇳 中文说明

中文用户请阅读 [`README.zh.md`](README.zh.md)。

— Authored by TZUVet · v2.2 · Built for CN invention patent quality at industrial scale.
