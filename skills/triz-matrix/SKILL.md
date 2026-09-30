---
name: triz-matrix
displayName:
  en: "TRIZ Contradiction Matrix Toolkit"
  zh: "TRIZ 矛盾矩阵工具箱"
description: "TRIZ矛盾建模工具箱——40发明原理+39工程参数+完整Altshuller 39×39矛盾矩阵(1521交叉点·含查询器)+物理矛盾四大分离原理+ARIZ-85C+物-场76标准解+五级发明等级判定。适用：当用户面对'改善X会恶化Y'的技术矛盾、需查矩阵推荐原理、需评估发明高度1-5级、需ARIZ框架解高难度问题。中文触发词：TRIZ/矛盾矩阵/40原理/39参数/分离原理/物场模型/76标准解/ARIZ/发明等级/IFR。"
trigger_keywords:
  - "TRIZ"
  - "矛盾矩阵"
  - "技术矛盾"
  - "物理矛盾"
  - "分离原理"
  - "40原理"
  - "39参数"
  - "ARIZ"
  - "发明等级"
  - "76标准解"
  - "IFR"
---

# TRIZ矛盾建模工具箱

为TRIZ问题建模与原理引导提供参考资料。主用户：**contradiction-analyst**（解其纷）。

| 文件 | 内容 |
|------|------|
| [triz-matrix.md](references/triz-matrix.md) | 40发明原理速查、39工程参数（权威版）、权威矩阵速查表(20条高频对)、物理矛盾四大分离原理、ARIZ-85C九步概要、76标准解速查（含编号-场景映射）、物-场模型、TRIZ五级发明等级 |
| [Altshuller_Contradiction_Matrix.csv](references/Altshuller_Contradiction_Matrix.csv) | **完整39×39矩阵数据（1521交叉点·权威源）** |
| [Altshuller_39_Parameters.csv](references/Altshuller_39_Parameters.csv) · [_zh.md](references/Altshuller_39_Parameters_zh.md) | 39工程参数英文原名 + 中英对照 |
| [query_triz_matrix.py](../../scripts/query_triz_matrix.py) | **矩阵查询器（确定性·防幻觉）** |

## 使用原则

1. **矛盾矩阵查询一律走查询器**（覆盖全部1521交叉点，替代原12条速查表）：
   ```bash
   python3 scripts/query_triz_matrix.py --improve <编号> --worsen <编号>
   python3 scripts/query_triz_matrix.py --list-params        # 列39参数
   python3 scripts/query_triz_matrix.py --improve strength --worsen weight   # 关键词
   ```
2. 查询器不可用 → 查 triz-matrix.md 的权威速查表（20条高频对）
3. **严禁凭训练记忆生成原理编号**——矩阵查询必须走查询器或权威速查表
4. 76标准解速查按编号精确取用（1.1补全物场、1.2引入S3中介、2.1引入S3增强、4.1检测派生量、5.1廉价替代等）

### 降级路径决策树（实操必备 · 2026-09-30 升级）

```
起点：拿到具体矛盾（改善#A × 恶化#B）
  │
  ├─ 查询器查 (A,B)
  │    ├─ ✅ 有推荐原理 → 取2-4个原理编号，逐原理落地
  │    └─ ❌ 矩阵无推荐原理（15.4%交叉点）→ 进入降级分支
  │
  ├─ 降级分支（关键决策点）
  │    ├─ 是技术矛盾？（两参数方向不同）
  │    │    └─ 检索#A/#B相关40原理，组合2-3个候选（标注"非矩阵推荐"）
  │    ├─ 物理矛盾分支（同一参数需同时满足相反状态）
  │    │    └─ 查"四大分离原理快速匹配表"（已在references）
  │    └─ 物-场模型分支（功能不足/有害/测量困难）
  │         └─ 查76标准解（按编号精确取用）
  │
  └─ 兜底：登记`[矩阵无原理·已降级]`+`[INFERRED]`，向主理人反馈
```

> ⚠️ **区分两种"没有"**：①「矩阵本身无推荐原理」（查得出来·15.4%）→ 正当降级；②「查询器不可用」→ 查速查表或报告工具受限。**不得把①误报为②，也不得因①而凭记忆编造编号。**

### 失败处理·强制三件套（任何降级路径都需）

1. **登记限制**：`[矩阵无推荐原理·已转分离原理路径]`，写入result_envelope.issues
2. **不编造**：绝不凭训练记忆生成原理编号——必须经查询器或权威速查表
3. **降级路径标注**：使用physical contradiction / 76 standard solutions 时需标注"降级来源"

### 常见错误自查清单

- ❌ 凭训练记忆生成原理编号 → 必走查询器（failure-001根因；原12条速查表经核对0/12正确）
- ❌ 把76标准解编号改写（如1.1.1写成1.1）→ 立即修正为references原文编号
- ❌ 把分离原理映射到矩阵推荐编号（如"用#13"替代"用分离原理空间分离"）→ 矩阵未涵盖的必须用分离原理
- ❌ 跨矩阵库硬拼（把"物场5.1"和"矩阵#35"混用而不标层级）→ 必须分层标注

## 数据溯源与修复史

- 矩阵数据源：`jenson500/triz-prompt-engineering`（经 deepwiki / studyraid 两独立源交叉验证一致）
- **2026-09-30 数据修复**：原速查表12条经核对与权威矩阵 **0/12 一致**（LLM记忆产物·failure-001残留），已废弃重写；39参数表同步替换权威版；新增查询器使可用覆盖率 0.8%(12条) → 82.1%(1248个有原理交叉点)
