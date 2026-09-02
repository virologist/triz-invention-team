# TRIZ通用发明专家团

跨领域TRIZ发明团队：从矛盾建模、三轮专利查新、模拟审查到交底书与申请文件撰写，全流程陪跑至中国发明专利申请草稿。

## 类型

Team 型（多角色协作团队）

## 团队构成

| 成员 | ID | 职责 |
|------|-----|------|
| 齐创见（主理人） | triz-invention-team-team-lead | 阶段0需求锁定+领域坍缩+全流程调度 |
| 解其纷 | contradiction-analyst | TRIZ矛盾建模+40发明原理引导，≥3创意方向 |
| 甄无遗 | patent-search-scout | 三轮查新（关键词→分类号→差异化），X/Y/A/R/P分级 |
| 严三性 | patent-examiner-sim | 对抗式三性攻击，绿/黄/红裁决 |
| 谭无隐 | disclosure-architect | 技术交底书五要素结构化 |
| 权要达 | patent-attorney-writer | 权利要求书+说明书+摘要撰写 |

## 工作流程（6阶段SOP）

阶段0需求锁定（苏格拉底≤5轮×≤5问）→ 阶段1 TRIZ问题建模 → 阶段2 原理引导（≥3方向）→ 阶段3 三轮查新（硬性）→ 阶段4 对抗式三性确认+用户C1-C8确认 → 阶段5 交底书→申请文件撰写 → 最终交付。

预设Workflow：A全流程陪跑 / B单点TRIZ突破 / C查新+授权前景评估 / D交底书与申请文件代写。

## 附带技能

`triz-patent-toolkit`：40发明原理全表、39工程参数、矛盾矩阵用法、分离原理、ARIZ概要、专利法条速查、交底书模板、权利要求撰写指南。

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

将专家包目录放到专家目录下：

```
/Users/biodog/.workbuddy/plugins/marketplaces/my-experts/plugins/triz-invention-team/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r triz-invention-team.zip triz-invention-team/
```
