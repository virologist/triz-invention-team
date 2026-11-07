# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20261107-001] best_practice

**Logged**: 2026-11-07T17:50+08:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
macOS BSD grep 的 `\|` 交替语法是 GNU 扩展——不带 `-E` 时按字面量匹配，产生系统性假阴性。

### Details
第三轮独立诊断中 5 项关键结论依赖 `grep "A\|B"` 检索，在 macOS 上全部返回"无匹配"（实际存在）。靠 sed 直接读文件发现矛盾后用 `grep -E` 重验，纠正 2 项结论（scaffold state.json 集成其实已实现、preflight 第 8 项其实存在）。若未发现，将误报 2 项不存在的短板。

### Suggested Action
macOS 环境一律用 `grep -E "A|B"`（或 `grep -En`），禁用 `grep "A\|B"`；对"无匹配"结论做二次验证（sed/cat 直接读）再采信。

### Metadata
- Source: self-correction during triz-team-diagnosis-independent-20261107-r3
- Related Files: 工作区 outputs/triz-team-diagnosis-independent-20261107-r3.md
- Tags: bsd-grep, false-negative, verification

---

## [LRN-20261107-002] knowledge_gap

**Logged**: 2026-11-07T17:55+08:00
**Priority**: critical
**Status**: resolved
**Area**: config

### Summary
正则 `X.*?(?!Y)` 形态的"负向前瞻豁免"是死代码——`.*?` 可匹配空串，前瞻位置在命中点恒成立，豁免从未生效。

### Details
TRIZ 专家团 3 个成员 frontmatter 的禁词前瞻豁免（如 `基本.*?(?!设计|物理|常)`）经 python3 re 实测全部失效：应豁免样本（"基本设计常识"）仍命中。历史 L2 回归 13/13 PASS 靠的是行级清洗（代码块/表格/附录剔除）与词级豁免（EXEMPT_WORDS）巧合兜底，正则内前瞻从未参与判定。此类"写在纸上的豁免"与散文条款同型——看起来有防护，实际为零。

### Suggested Action
豁免逻辑用"命中后查上下文窗口"实现（见 contract_enforce.py CONTEXT_EXEMPT 表 + _context_exempt 函数，R1 修复），并为豁免/违规样本写双向断言自测；评审任何正则时优先检查 `.*?(?!` 组合。

### Resolution
- **Resolved**: 2026-11-07（R1 批次，commit 9ed7e96）
- **Notes**: CONTEXT_EXEMPT 上下文窗口豁免 + self-test 自测3 六组双向断言全过

### Metadata
- Source: triz-team-diagnosis-independent-20261107-r3.md D7-1
- Related Files: scripts/contract_enforce.py, agents/patent-examiner-sim.md
- Tags: regex, lookahead, dead-code, exemption

---

