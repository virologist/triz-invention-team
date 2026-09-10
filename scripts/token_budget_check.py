#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
token_budget_check.py — TRIZ专家团 H1上下文装配预算校验
模拟Context Assembler真实装配路径（角色MD + skills references + task_payload + 领域上下文 + state快照），
估算每个成员的上下文token数，校验是否超20K预算。

用法：
  python3 scripts/token_budget_check.py [专家包根目录] [--budget 20000]
估算方法：中文约1 token/1.5-2字节，混合内容按 bytes/3.5 近似（保守上界用 bytes/2.5）
"""
import sys, os, json, argparse

# 成员 → skills references 映射（与各MD frontmatter声明一致）
MEMBER_SKILLS = {
    "contradiction-analyst":   ["skills/triz-matrix/references/triz-matrix.md"],
    "patent-search-scout":     ["skills/patent-law/references/patent-law.md"],
    "patent-examiner-sim":     ["skills/patent-law/references/patent-law.md",
                                "skills/triz-matrix/references/triz-matrix.md"],
    "disclosure-architect":    ["skills/claims-drafting/references/disclosure-template.md"],
    "patent-attorney-writer":  ["skills/claims-drafting/references/claims-writing-guide.md",
                                "skills/patent-law/references/patent-law.md"],
    "second-opinion-reviewer": ["skills/patent-law/references/patent-law.md",
                                "skills/triz-matrix/references/triz-matrix.md"],
}

# 典型task_payload（取自历史实测用例的均值，约1.2K字符）
SAMPLE_PAYLOAD = {
    "task_id": "T-SAMPLE-001", "phase": 3,
    "instruction": "对技术方案执行标准流程任务，输出含上行信封与完整产出正文",
    "input": {"dependency_artifacts": ["前序phase产出的依赖部分（典型800-1500字符）"],
              "domain_context": "农业科学×仪器仪表交叉视角（精度/安全性/操作便利性）",
              "scenario": "典型技术场景描述约300-600字符，含现状痛点与约束条件"},
    "output_contract": {"required_fields": ["..."], "format": "markdown"},
    "constraints": ["硬约束清单3-6条，每条20-60字符"],
    "state_snapshot": {"phase": 3, "search_rounds": 2, "gates": {"G1": False}}
}

STATE_SNAPSHOT_CHARS = 800  # TASK_STATE完整快照典型规模


def est_tokens(text_len_bytes: int, conservative: bool = False) -> int:
    """中文为主的混合内容token估算：常规 bytes/3.5，保守 bytes/2.5"""
    return int(text_len_bytes / (2.5 if conservative else 3.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--budget", type=int, default=20000)
    ap.add_argument("--conservative", action="store_true", help="保守估算(bytes/2.5)")
    args = ap.parse_args()
    root = args.root

    payload_bytes = len(json.dumps(SAMPLE_PAYLOAD, ensure_ascii=False).encode("utf-8"))
    print(f"H1上下文装配预算校验  (预算={args.budget} tokens, 估算={'保守' if args.conservative else '常规'})")
    print("=" * 88)
    print(f"{'成员':<26}{'角色MD':>8}{'refs':>8}{'payload':>9}{'state':>7}{'合计':>9}{'余量':>9}  状态")
    print("-" * 88)

    all_pass = True
    rows = []
    for member, refs in MEMBER_SKILLS.items():
        md_path = os.path.join(root, "agents", f"{member}.md")
        try:
            md_bytes = os.path.getsize(md_path)
        except OSError:
            print(f"{member:<28}角色MD缺失！")
            all_pass = False
            continue
        ref_bytes = sum(os.path.getsize(os.path.join(root, r)) for r in refs if os.path.exists(os.path.join(root, r)))
        total_bytes = md_bytes + ref_bytes + payload_bytes + STATE_SNAPSHOT_CHARS
        tokens = est_tokens(total_bytes, args.conservative)
        margin = args.budget - tokens
        ok = margin >= 0
        all_pass &= ok
        status = "✅ PASS" if ok else "❌ 超预算"
        print(f"{member:<26}{md_bytes:>8}{ref_bytes:>8}{payload_bytes:>9}{STATE_SNAPSHOT_CHARS:>7}{tokens:>9}{margin:>+9}  {status}")
        rows.append((member, tokens, ok))

    print("-" * 88)
    verdict = "✅ 全员通过" if all_pass else "❌ 存在超预算成员"
    print(f"结论: {verdict}  (payload={payload_bytes}B, 预算口径见H1)")
    # 前序产出注入提示：Phase 4成员还会接收查新报告（典型3-5K tokens）
    heaviest = max(rows, key=lambda r: r[1]) if rows else None
    if heaviest and heaviest[1] > args.budget * 0.8:
        print(f"⚠️ 最重成员 {heaviest[0]}={heaviest[1]} tokens 已占预算{heaviest[1]/args.budget*100:.0f}%，"
              f"叠加前序产出(查新报告3-5K)可能触顶，建议装配时压缩依赖产出")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
