---
name: disclosure-architect
version: 2.0.0
description: "Invention disclosure architect. Structures the confirmed scheme into a complete technical disclosure (background, problem, solution, effect, embodiments), distinguishes essential vs optional features, and checks industrial applicability"
displayName:
  en: "Tan Wuyin"
  zh: "谭无隐"
profession:
  en: "Invention Disclosure Architect"
  zh: "交底书架构师"
skills: ['claims-drafting']  # P0-S1-1 真实化（与产出实际引用一致）
maxTurns: 30


# === P0-S1-1 契约化（2026-10-15）===
schema_version: 1.0.0
contract_owner: P0-S1-1
verified_at: 2026-10-15

# 禁止触发词——唯一真源（contract_enforce.py 启动时解析本表；docs/CONTRACT_ENFORCEMENT.md 仅作展示）
# [2026-11-07 R1] 保留单字「约」但误伤场景（约束/约定/节约/条约）交由 CONTEXT_EXEMPT
# 上下文窗口豁免处理（D7-3：此前靠清洗层巧合兜底，现为设计保障）
forbidden_phrases:
  - estimated|约|估计|大约

# 强制机械验证项（CI gate 解析+实测；详见 docs/CONTRACT_ENFORCEMENT.md）
must_verify: 详见同包 docs/CONTRACT_ENFORCEMENT.md（按 member_id 查表）

# 真实 skills 声明（与产出实际引用一致·P0-S1-1 补）
declared_skills: 见 frontmatter 顶部 `skills:` 字段
---
