#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
failure_memory.py — episodic 失败记忆注入器（P2-12 · 2026-10-15 建立）
=====================================================================
定位：把 ~/.workbuddy/expert-failures/ 的 learned_rule 按「本次派单的成员/关键词」
      筛出摘要，供主理人在 spawn 前注入到派单文案——失败经验不靠人肉同步。
      （对标 a-evolve 的 episodic memory：lessons from failures，运行时注入而非静态写死）

为什么不直接写进成员 MD：静态注入会过期（修好了还在提醒）且无法按任务域筛选；
运行时摘要永远取最新记录，且只给相关成员看。

用法：
  # 全量清单（表格）
  python3 scripts/failure_memory.py --list

  # 本次派单的注入摘要（推荐：按成员筛）
  python3 scripts/failure_memory.py --digest --members contradiction-analyst,patent-attorney-writer

  # 按任务域关键词筛（与成员筛取并集）
  python3 scripts/failure_memory.py --digest --keywords 摘要,矩阵,信封

  # 机器可读 / 全量正文
  python3 scripts/failure_memory.py --digest --members ... --json
  python3 scripts/failure_memory.py --digest --members ... --full

退出码：0=正常（无记录也返回 0，摘要里注明）  2=用法/环境错误
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

DEFAULT_DIR = os.path.expanduser("~/.workbuddy/expert-failures")
SEVERITY_RANK = {"critical": 0, "major": 1, "minor": 2}
DIGEST_RULE_MAX = 240          # 摘要模式下 learned_rule 截断长度
DIGEST_SYMPTOM_MAX = 90        # 症状截断长度


def load_records(exp_dir):
    recs = []
    for p in sorted(glob.glob(os.path.join(exp_dir, "failure-*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
            d["_path"] = p
            recs.append(d)
        except Exception as e:  # noqa
            print(f"⚠️ 跳过无法解析的记录 {os.path.basename(p)}: {e}", file=sys.stderr)
    return recs


def haystack(d):
    """把一条记录的可检索文本拼起来"""
    parts = [
        str(d.get("symptom", "")), str(d.get("root_cause", "")),
        str(d.get("learned_rule", "")), str(d.get("fix_action", "")),
        " ".join(d.get("tags", []) or []), str(d.get("member_id", "")),
        str(d.get("fail_type", "")),
    ]
    return " ".join(parts)


def matches(d, members, keywords):
    """筛选：成员匹配 或 关键词匹配；两者都空 = 全收（按 expert 已筛过）"""
    m_ok = k_ok = False
    if members:
        m_ok = str(d.get("member_id", "")) in members
    if keywords:
        hay = haystack(d)
        k_ok = any(kw and kw in hay for kw in keywords)
    if members and keywords:
        return m_ok or k_ok
    if members:
        return m_ok
    if keywords:
        return k_ok
    return True


def brief(text, n):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def sort_key(d):
    return (
        SEVERITY_RANK.get(str(d.get("severity", "minor")), 9),
        str(d.get("fail_date", "")),
    )


def render_digest(recs, members, keywords, mode_full):
    if not recs:
        return ("## 失败记忆摘要（failure_memory）\n\n"
                "> ✅ 本次筛选条件下无相关失败记录。\n")
    lines = [
        "## 失败记忆摘要（failure_memory · 自动生成）",
        "> 交付前自查：以下教训来自历史失败记录（按相关度筛选），逐条确认本次不重犯。",
        "> 规则来源：`~/.workbuddy/expert-failures/`（failure_memory.py 运行时注入，不用静态抄写）。",
        "",
    ]
    for d in recs:
        fid = d.get("id", "?")
        sev = d.get("severity", "?")
        mid = d.get("member_id", "（通用）")
        ft = d.get("fail_type", "")
        tags = ",".join((d.get("tags") or [])[:4])
        lines.append(f"### [{fid}·{sev}] {brief(d.get('symptom',''), DIGEST_SYMPTOM_MAX)}")
        lines.append(f"- **成员**：{mid} ｜ **类型**：{ft} ｜ **日期**：{d.get('fail_date','?')}"
                     + (f" ｜ **标签**：{tags}" if tags else ""))
        rule = str(d.get("learned_rule", "")).strip()
        if not mode_full:
            rule = brief(rule, DIGEST_RULE_MAX)
        lines.append(f"- **必须遵守的规则**：{rule}")
        lines.append("")
    return "\n".join(lines)


def render_list(recs):
    print(f"共 {len(recs)} 条失败记录（{'~/.workbuddy/expert-failures'}）\n")
    print(f"{'id':12s} {'sev':8s} {'date':10s} {'member':26s} {'type':18s} 症状摘要")
    print("-" * 118)
    for d in sorted(recs, key=sort_key):
        print(f"{d.get('id','?'):12s} {d.get('severity','?'):8s} {d.get('fail_date','?'):10s} "
              f"{str(d.get('member_id','-'))[:26]:26s} {str(d.get('fail_type','-'))[:18]:18s} "
              f"{brief(d.get('symptom',''), 46)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="episodic 失败记忆注入器（P2-12）")
    ap.add_argument("--dir", default=DEFAULT_DIR, help=f"失败索引目录（默认 {DEFAULT_DIR}）")
    ap.add_argument("--expert", default="triz-invention-team", help="专家团 ID 筛选（默认 triz-invention-team）")
    ap.add_argument("--list", action="store_true", help="列出全部记录（表格）")
    ap.add_argument("--digest", action="store_true", help="输出注入摘要（markdown）")
    ap.add_argument("--members", default="", help="逗号分隔的成员 ID（按成员筛）")
    ap.add_argument("--keywords", default="", help="逗号分隔关键词（与成员筛取并集）")
    ap.add_argument("--max", type=int, default=12, help="摘要最多条数（默认 12）")
    ap.add_argument("--full", action="store_true", help="摘要不截断正文")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        print(f"❌ 失败索引目录不存在：{args.dir}", file=sys.stderr)
        return 2

    recs = load_records(args.dir)
    # 专家筛选：expert_id 匹配 或 member_id 为空（通用教训）；--expert "" 表示全收
    if args.expert:
        recs = [d for d in recs
                if str(d.get("expert_id", "")) == args.expert or not d.get("member_id")]

    if args.list:
        return render_list(recs)

    members = [m.strip() for m in args.members.split(",") if m.strip()]
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    sel = [d for d in recs if matches(d, members, keywords)]
    sel.sort(key=sort_key)
    sel = sel[: args.max]

    if args.json:
        out = {
            "generated_at": datetime.datetime.now().isoformat(),
            "expert": args.expert, "members": members, "keywords": keywords,
            "count": len(sel),
            "records": [{"id": d.get("id"), "severity": d.get("severity"),
                         "member_id": d.get("member_id"), "fail_type": d.get("fail_type"),
                         "fail_date": d.get("fail_date"), "symptom": d.get("symptom"),
                         "learned_rule": d.get("learned_rule"), "tags": d.get("tags")}
                        for d in sel],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_digest(sel, members, keywords, args.full))
        if not args.digest:
            print("（提示：加 --digest 即为此用途；当前输出相同内容但语义上用于注入。）",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
