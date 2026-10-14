#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
token_budget_check.py — TRIZ专家团 H1上下文装配预算校验
模拟Context Assembler真实装配路径（角色MD + skills references + task_payload + 领域上下文 + state快照），
估算每个成员的上下文token数，校验是否超20K预算。

用法：
  python3 scripts/token_budget_check.py [专家包根目录] [--budget 20000]
  python3 scripts/token_budget_check.py --meter outputs/<run-dir> [--ledger]   # 实测计量（P1-8）
估算方法：中文约1 token/1.5-2字节，混合内容按 bytes/3.5 近似（conservative 用 bytes/2.5）

【--meter 实测计量模式（2026-10-14 新增，P1-8）】
从**落盘文件**机械计量产出规模，替代成员自报——自报已被 failure-006 实证不可靠
（摘要自评 281 字 vs 实测 371 字符）。同时回填/核对双轨制耗时字段（duration_ms_wall）。
输出：每个成员一行；--ledger 时把结果 append 到 <run-dir>/metrics.jsonl 作为跨轮次台账。
"""
import sys, os, json, argparse, re, glob, datetime

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


FILENAME_RE = re.compile(r"(T-\d{8}-\d{3})__([a-z0-9-]+)\.md$")


def meter_run(run_dir, ledger=False, conservative=False, global_budget=120_000):
    """实测计量：从落盘文件机械统计产出规模（P1-8）。

    计量口径（全部机械，不采信任何自报值）：
      - out_bytes / out_chars：落盘产出文件大小
      - out_tokens：est_tokens(out_bytes)（产出侧估算）
      - wall_ms：仅当信封里已被主理人回填 duration_ms_wall 才计入，否则标 missing
      - self_ms：成员自报 duration_ms，仅作展示，不参与任何汇总
    """
    files = sorted(glob.glob(os.path.join(run_dir, "*__*.md")))
    if not files:
        print("❌ 未找到落盘产出（匹配 *__*.md）：%s" % run_dir)
        return 1
    print("📏 实测计量 — run_dir=%s（口径：机械，不采信自报）" % run_dir)
    print("=" * 92)
    print(f"{'任务':<18}{'成员':<24}{'chars':>8}{'tokens':>8}{'自报ms':>9}{'墙钟ms':>10}  状态")
    print("-" * 92)

    rows, total_tokens = [], 0
    for f in files:
        m = FILENAME_RE.search(os.path.basename(f))
        if not m:
            continue
        task_id, member = m.group(1), m.group(2)
        raw = open(f, "rb").read()
        nbytes, text = len(raw), raw.decode("utf-8", errors="replace")
        nchars = len(text)
        tok = est_tokens(nbytes, conservative)
        total_tokens += tok

        # 提取信封（首个 json 代码块）
        env = {}
        mm = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
        if mm:
            try:
                env = json.loads(mm.group(1))
            except Exception:
                env = {}
        met = env.get("metrics") or {}
        self_ms = met.get("duration_ms")
        wall_ms = met.get("duration_ms_wall")
        wall_txt = str(wall_ms) if wall_ms is not None else "missing"
        self_txt = str(self_ms) if self_ms is not None else "—"

        flags = []
        if wall_ms is None:
            flags.append("墙钟未回填")
        elif self_ms not in (None, 0) and wall_ms:
            if abs(self_ms - wall_ms) / wall_ms > 0.5:
                flags.append("耗时自报失真(>50%)")
        status = "✅" if not flags else "⚠️ " + "、".join(flags)

        print(f"{task_id:<18}{member:<24}{nchars:>8}{tok:>8}{self_txt:>9}{wall_txt:>10}  {status}")
        rows.append({
            "task_id": task_id, "member": member,
            "file": os.path.basename(f), "chars": nchars, "bytes": nbytes,
            "out_tokens_est": tok,
            "duration_ms_self": self_ms, "duration_ms_wall": wall_ms,
            "status": env.get("status"), "confidence": env.get("confidence"),
            "flags": flags,
            "metered_at": datetime.datetime.now().isoformat(timespec="seconds"),
        })

    print("-" * 92)
    ratio = total_tokens / global_budget if global_budget else 0
    print(f"合计产出估算 {total_tokens:,} tokens（占全局预算 {ratio*100:.0f}%，上限 {global_budget:,}）")
    if ratio > 0.8:
        print("⚠️ 已超 80%，H3.5 要求向用户预警")
    print("注：本表只计**产出侧**；输入侧上下文预算另跑无 --meter 的默认模式。")

    if ledger:
        lp = os.path.join(run_dir, "metrics.jsonl")
        with open(lp, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("📒 台账已 append：%s（%d 行）" % (lp, len(rows)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--budget", type=int, default=20000)
    ap.add_argument("--conservative", action="store_true", help="保守估算(bytes/2.5)")
    ap.add_argument("--meter", default="", help="实测计量：传入 run-dir（含 *__*.md 落盘产出）")
    ap.add_argument("--ledger", action="store_true", help="实测计量结果 append 到 <run-dir>/metrics.jsonl")
    ap.add_argument("--global-budget", type=int, default=120_000, help="全局预算(H3.5)，用于占比预警")
    args = ap.parse_args()
    root = args.root

    if args.meter:
        return meter_run(args.meter, args.ledger, args.conservative, args.global_budget)

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
