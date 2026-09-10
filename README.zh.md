# TRIZ 通用发明专家团（v2.2）

> **跨领域 TRIZ 发明团队**：从矛盾建模 → 三轮专利查新 → 模拟审查 → 交底书与申请文件撰写，**陪跑至中国发明专利申请草稿**。

一个像真实发明团队一样协作的多代理系统——主理人调度全局，矛盾分析师应用 39×39 TRIZ 矩阵，查新员跑三轮专利查新，模拟审查员攻击新颖性/创造性/实用性，二审员做独立复审（自动捕捉确认偏误），交底书架构师把发明结构化为五要素，专利代理师撰写权项、说明书与摘要。

v2.2 版本把代理间契约形式化为 JSON Schema（`agent-protocol`），并附带 CI gate 脚本——在产出进入下游核验前自动校验所有代理输出。

---

## ✨ 亮点

- **7 名专家 + 1 名主理人**：每个代理都有明确的角色边界（ANALYZER / EXECUTOR / REVIEWER），并设有"禁止越界产出"的强制规则
- **TRIZ 39×39 矛盾矩阵 + 40 发明原理**（含越表矛盾对的降级路径）
- **三轮专利查新**（关键词 → 分类号 → 差异化验证），附 X / Y / A / R / P 威胁分级
- **模拟审查 + 独立二审**：自动捕捉确认偏误
- **专利组合策略**（核心 / 外围 / 替代路线）—— 加强保护范围
- **实施例参数范围设计**：每个数值范围配 ≥3 个实施例点位（端值×2 + 中间值×1），符合中国专利法第 26.3-26.4 条
- **JSON Schema 契约 + CI gate 脚本**：扣除 legacy 后 100% 合规率
- **跨平台插件格式**：双清单并列（`.claude-plugin/` + `.codebuddy-plugin/`）+ 双市场描述文件，同一仓库同时兼容 Claude Code、GitHub Copilot CLI 与 WorkBuddy

---

## 📦 安装

本仓库是一个**单插件市场（single-plugin marketplace）**。两个生态都可直接从 GitHub 添加，无需手工拷贝。

### 方式 A — Claude Code / GitHub Copilot CLI

```bash
# 在 Claude Code 或 Copilot CLI 内
/plugin marketplace add virologist/triz-invention-team
/plugin install triz-invention-team@triz-invention-team-marketplace
```

> **私有仓库？** 请先完成 `gh auth login` 或导出 `GITHUB_TOKEN`，否则市场克隆会失败。

备选——直接加载本地克隆：

```bash
gh repo clone virologist/triz-invention-team ~/claude-plugins/triz-invention-team
claude --plugin-dir ~/claude-plugins/triz-invention-team/plugins/triz-invention-team
```

### 方式 B — WorkBuddy

WorkBuddy 原生支持 git 型市场，因此命令与上面一致：

```bash
/plugin marketplace add virologist/triz-invention-team
/plugin install triz-invention-team@triz-invention-team-marketplace
```

或注册为本地目录型市场：

```bash
gh repo clone virologist/triz-invention-team \
  ~/.workbuddy/plugins/marketplaces/triz-invention-team-marketplace
# 重启 WorkBuddy，团队将出现在"专家团"列表
```

### 方式 C — 手工 / 其他 agent 宿主

插件在 `plugins/triz-invention-team/` 下**完全自包含**。把该目录放到宿主 agent 的插件发现路径即可：

```bash
cp -R plugins/triz-invention-team <你的agent插件目录>/
```

---

## 🚀 快速开始

安装完成后，向主理人"齐创见"发送任一启动 prompt：

| 提示语 | 触发流程 |
|--------|----------|
| *"我有一个发明想法，请团队帮我从 TRIZ 矛盾分析走到专利申请文件草稿"* | 完整 Workflow A：0→1 发明流水线 |
| *"我的设计存在矛盾：改善 X 会恶化 Y，请用矛盾矩阵推演发明方向"* | Workflow B：单点 TRIZ 突破 |
| *"我已有技术方案，请做三轮专利查新并评估三性风险"* | Workflow C：可专利性评估 |

主理人会先跑苏格拉底式 Phase 0（≤5 轮×≤5 问）锁定领域上下文，再调度其他成员。

---

## 👥 团队构成

| 成员 | 角色 | Agent ID |
|------|------|----------|
| **齐创见** | 主理人 · Phase 0 需求锁定 · 编排 | `triz-invention-team-team-lead` |
| **解其纷** | TRIZ 矛盾分析师 · 40 发明原理引导 | `contradiction-analyst` |
| **甄无遗** | 专利查新员 · 三轮检索 | `patent-search-scout` |
| **严三性** | 模拟审查员 · 三性攻击 · 绿/黄/红裁决 | `patent-examiner-sim` |
| **审外审** | 独立二审员 · 含利益冲突边界 | `second-opinion-reviewer` |
| **谭无隐** | 交底书架构师 · 五要素结构 · ≥3 类缺口 | `disclosure-architect` |
| **权要达** | 专利代理师 · 权项+说明书+摘要 | `patent-attorney-writer` |

---

## 🧠 附带技能

- **`triz-matrix`**：39×39 矛盾矩阵、40 发明原理、ARIZ-85C
- **`patent-law`**：中国专利法第 22.2 / 22.3 / 22.4 条（新颖性 / 创造性 / 实用性）
- **`claims-drafting`**：权项撰写指南 + 交底书模板（中文发明专利）
- **`agent-protocol`**：`result_envelope` + `task_payload` 的 JSON Schema + CI gate

---

## 🛠️ 仓库结构

```
triz-invention-team/                          # ← 市场根目录
├── .claude-plugin/
│   └── marketplace.json                      # Claude Code / Copilot CLI 市场描述
├── .codebuddy-plugin/
│   └── marketplace.json                      # WorkBuddy 市场描述
├── plugins/
│   └── triz-invention-team/                  # ← 自包含插件本体
│       ├── .claude-plugin/plugin.json        # Claude Code / Copilot CLI 清单
│       ├── .codebuddy-plugin/plugin.json     # WorkBuddy 清单
│       ├── agents/                           # 7 个代理角色定义（Markdown）
│       ├── skills/                           # 4 个技能包
│       ├── scripts/                          # CI gate + token 预算校验
│       ├── docs/                             # architecture · OPERATIONS · evolution-log
│       ├── avatars/                          # 512×512 代理头像
│       └── settings.json
├── README.md                                 # 英文版
├── README.zh.md                              # ← 中文版（当前文件）
├── CHANGELOG.md                              # 发布历史
└── LICENSE                                   # Apache-2.0
```

---

## 🧪 质量门禁

```bash
cd plugins/triz-invention-team

python3 scripts/agent_ci_gate.py --self-test              # schema 自测
python3 scripts/agent_ci_gate.py --results-dir outputs/   # CI gate 校验所有归档测试
python3 scripts/token_budget_check.py --conservative      # H1 上下文装配预算
```

CI gate 当前对所有 v2.2 后归档报告 **100% 合规率**（legacy 早期归档按设计豁免）。

---

## 🔄 发布流程

1. 更新 `plugins/triz-invention-team/` 下的 agents / skills / scripts
2. 跑 `python3 plugins/triz-invention-team/scripts/agent_ci_gate.py --strict` 把守 commit 门禁
3. 同时 bump `plugins/triz-invention-team/.claude-plugin/plugin.json` 和 `plugins/triz-invention-team/.codebuddy-plugin/plugin.json` 的版本号（semver）
4. 保持两个市场描述文件同步：`.claude-plugin/marketplace.json`、`.codebuddy-plugin/marketplace.json`
5. 打 tag：`git tag v2.x.y`
6. 推送：`git push origin main --tags`

完整跨会话恢复剧本见 [`docs/OPERATIONS.md`](plugins/triz-invention-team/docs/OPERATIONS.md)。

---

## 🤝 贡献

欢迎 issue 和 PR。请确保：

1. 新代理 prompt 含 `result_envelope` JSON 块（参照 [`agent-protocol` schema](plugins/triz-invention-team/skills/agent-protocol/result_envelope.schema.json)）
2. CI gate `--strict` 通过
3. 单代理 token 预算不超过 20K（用 `scripts/token_budget_check.py` 验证）

---

## 📜 许可证

Apache-2.0 — 见 [`LICENSE`](LICENSE)。专利授权明示，允许商用，保留归属。

---

— 作者：TZUVet · v2.2 · 为中国发明专利工业化质量而建。
