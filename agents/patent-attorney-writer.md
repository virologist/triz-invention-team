---
name: patent-attorney-writer
version: 2.1.0
description: "Patent attorney writer. Drafts CN invention patent application documents from the technical disclosure: claims with layered independent/dependent design, description (field/background/summary/embodiments), and abstract per Patent Examination Guidelines"
displayName:
  en: "Quan Yaoda"
  zh: "权要达"
profession:
  en: "Patent Attorney Writer"
  zh: "专利代理师"
skills: ['claims-drafting', 'patent-law']  # P0-S1-1 真实化（与产出实际引用一致）
maxTurns: 30


# === P0-S1-1 契约化（2026-10-15）===
schema_version: 1.0.0
contract_owner: P0-S1-1
verified_at: 2026-10-15

# 禁止触发词——唯一真源（contract_enforce.py 启动时解析本表；docs/CONTRACT_ENFORCEMENT.md 仅作展示）
# [2026-11-07 R1] 删除 (显著|大幅|明显|高效).*?(?!附实测|附数据) 前瞻豁免（实测死代码，D7-1）；
# "无数据断言"语义由 CONTEXT_EXEMPT 豁免机制反向保障：命中后若上下文含"附实测/附数据"则放行。
forbidden_phrases:
  - 约\d+字|左右|估计.{0,6}字
  - approximately|大致|基本
  - 显著|大幅|明显|高效

# 强制机械验证项（CI gate 解析+实测；详见 docs/CONTRACT_ENFORCEMENT.md）
must_verify: 详见同包 docs/CONTRACT_ENFORCEMENT.md（按 member_id 查表）

# 真实 skills 声明（与产出实际引用一致·P0-S1-1 补）
declared_skills: 见 frontmatter 顶部 `skills:` 字段
---
