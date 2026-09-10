---
name: agent-protocol
description: "团队智能体通信契约的形式化规范 — JSON Schema形式化的result_envelope（上行信封）和task_payload（下行任务），含agent_ci_gate.py脚本自动校验CI门禁。适用于任何使用主理人-成员架构的多代理团队。"
---

# Agent Protocol · 通信契约形式化

> v2.2基础设施（2026-09-03）：result_envelope和task_payload从"自然语言+JSON示例"升级为JSON Schema形式化规范，并配套`agent_ci_gate.py` CI门禁脚本。

## 🔴 单点权威约束（所有成员必须遵守）

**所有成员产出必须以result_envelope.schema.json定义的6项必填字段（agent_id/task_id/phase/status/confidence/deliverable_summary）开头**，以有效JSON块形式置于产出正文**最前**。

**违规处理**：
- 缺字段/JSON不可解析/agent_id未在白名单 = 主理人VERIFY阶段直接 `partial` 标记并触发补充重试
- 不再容忍无信封产出

**配套**：
- Schema：`result_envelope.schema.json`（本目录）
- CI门禁：`scripts/agent_ci_gate.py`（自动校验所有归档*results.json）
- 成员MD中的引用行仅作指向，单点权威定义在此SKILL.md

## 设计目标

- **机器可校验**：用标准jsonschema库自动校验agent产出，替代人工核对
- **门禁可自动化**：每次git commit自动跑核心契约+关键不变量
- **向后兼容**：`additionalProperties=true`+deprecated_fields机制，旧成员产出不被误报

## 文件清单

| 文件 | 作用 |
|------|------|
| `skills/agent-protocol/result_envelope.schema.json` | **上行信封**契约（成员→主理人） |
| `skills/agent-protocol/task_payload.schema.json` | **下行任务**契约（主理人→成员） |
| `scripts/agent_ci_gate.py` | CI门禁脚本，自动校验所有归档测试JSON的合规率 |

## result_envelope字段规范（必填6项）

| 字段 | 类型 | 约束 |
|------|------|------|
| `agent_id` | string | kebab-case，3-64字符，已知7代理+探针后缀（-probe/-reg/-test/-r2） |
| `task_id` | string | 格式 `^T-[0-9]{8}-[0-9]{3,}$` |
| `phase` | integer | 0-5 |
| `status` | enum | `success` / `partial` / `failed` / `blocked` |
| `confidence` | integer | 0-100 |
| `deliverable_summary` | string | 1-500字符，一句话摘要 |

可选字段：`evidence`（推荐，证据链数组）、`issues`（自评问题）、`next_agent_hint`、`metrics`（duration_ms/retry_count）

## 使用方法

### 1. 本地CI门禁

```bash
# 校验outputs目录下所有*-results.json的信封合规率
python3 scripts/agent_ci_gate.py --results-dir outputs/

# 严格模式（任何FAIL则exit 1，阻断git push）
python3 scripts/agent_ci_gate.py --strict

# Schema自测
python3 scripts/agent_ci_gate.py --self-test
```

### 2. 嵌入git pre-commit hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
python3 scripts/agent_ci_gate.py --strict || {
  echo "❌ Agent CI Gate failed — 修复信封字段后再commit"
  exit 1
}
```

### 3. 失败判定

- **valid**：信封完整+agent_id在白名单
- **partial**：信封完整但agent_id是探针（带-probe/-reg/-test/-r2后缀）
- **failed**：信封缺失/JSON不可解析/Schema校验失败/agent_id未知

## 校验算法（agent_ci_gate.py）

**栈平衡JSON扫描**（替代贪婪正则，处理嵌套{}）：
- 从每个`{`开始向后扫描，遇`{` depth+1，遇`}` depth-1
- depth=0时结束，尝试`json.loads
- 字符串内的引号需转义（用`in_str`+`esc`标志）

这比正则`\{[\s\S]*?\}`更鲁棒——后者在第一个`}`处停下会切断嵌套结构。

## 何时扩展

新增agent时：在`KNOWN_AGENTS`集合中加入新agent_id（在scripts/agent_ci_gate.py中）。

新增字段时：在schema的`properties`中加入，不需修改`required`（除非新字段为必填）。

Schema版本演进：bump `version`字段，旧归档通过`deprecated_fields`兼容。

## 关联资源

- 专家包根目录 `agents/triz-invention-team-team-lead.md` 第265-297行：原始自然语言契约定义
- `~/.workbuddy/MEMORY.md`：契约演进历史（v2.0/v2.1/v2.2）
- `~/.workbuddy/expert-failures/`：失败索引（含契约相关failure-003/004）