# TRIZ通用发明专家团

跨领域TRIZ发明团队：从矛盾建模、三轮专利查新、模拟审查到交底书与申请文件撰写，全流程陪跑至中国发明专利申请草稿。

## 类型

Team 型（多角色协作团队）

## 团队构成

7 名智能体 = 1 主理人 + 6 成员。

| 成员 | ID | 职责 |
|------|-----|------|
| 齐创见（主理人） | triz-invention-team-team-lead | 阶段0需求锁定+领域坍缩+全流程调度 |
| 解其纷 | contradiction-analyst | TRIZ矛盾建模+40发明原理引导，≥3创意方向 |
| 甄无遗 | patent-search-scout | 三轮查新（关键词→分类号→差异化），X/Y/A/R/P分级 |
| 严三性 | patent-examiner-sim | 对抗式三性攻击，绿/黄/红裁决 |
| 审外审 | second-opinion-reviewer | 独立二审复核（含利益冲突边界，自动捕捉确认偏误） |
| 谭无隐 | disclosure-architect | 技术交底书五要素结构化 |
| 权要达 | patent-attorney-writer | 权利要求书+说明书+摘要撰写 |

## 工作流程（7 阶段节点 SOP）

阶段0需求锁定（苏格拉底≤5轮×≤5问）→ 阶段1 TRIZ问题建模 → 阶段2 原理引导（≥3方向）→ 阶段2.5 汇聚校准 → 阶段3 三轮查新（硬性）→ 阶段4 对抗式三性确认+独立二审+用户C1-C8确认 → 阶段5 交底书→申请文件撰写 → 最终交付。

预设Workflow：A全流程陪跑 / B单点TRIZ突破 / C查新+授权前景评估 / D交底书与申请文件代写（D 入口设前置闸：无三轮查新与 G2/G3 证据时不得直出草稿）。

## 附带技能

4 个技能包：
- `triz-matrix`：40发明原理全表、39工程参数、1521 交叉点矛盾矩阵、ARIZ概要
- `patent-law`：中国专利法第 22.2 / 22.3 / 22.4 条（新颖性 / 创造性 / 实用性）
- `claims-drafting`：权利要求撰写指南 + 交底书模板
- `agent-protocol`：`result_envelope` + `task_payload` 的 JSON Schema + CI gate

## 质量门禁

```bash
python3 scripts/agent_ci_gate.py --strict                  # 信封 schema 门禁
python3 scripts/contract_enforce.py --self-test            # 契约自测（三源一致性 + 豁免双向断言）
python3 scripts/state_store.py self-test                   # 门禁状态机（G1-G5 别名归一 + 回流重置）
python3 scripts/preflight_check.py                         # 建队前 13 项 preflight
python3 scripts/run_regression.py --list                   # 3 个回归用例
```

## 使用示例

- "我有一个发明想法，请团队帮我从TRIZ矛盾分析走到专利申请文件草稿"
- "我的设计存在矛盾：改善X会恶化Y，请用矛盾矩阵推演发明方向"
- "我已有技术方案，请做三轮专利查新并评估三性风险"

## 红线

禁止捏造专利号 / 未完成3轮查新禁止撰写 / 不做授权保证 / 不包装低创造性方案 / 输出供专利律师审定，不替代法律意见。

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

WorkBuddy 支持 git 型市场，直接添加即可：

```bash
/plugin marketplace add virologist/triz-invention-team
/plugin install triz-invention-team@triz-invention-team-marketplace
```

或克隆到本地市场目录（仓库根即插件本体，无 `plugins/` 嵌套层）：

```bash
gh repo clone virologist/triz-invention-team \
  ~/.workbuddy/plugins/marketplaces/triz-invention-team-marketplace
```

## 打包分享

```bash
zip -r triz-invention-team.zip triz-invention-team/
```
