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


def _self_test():
    """判别力自测（S-E58）：筛选语义 + 排序 + 截断。

    关键判别点：**成员筛 与 关键词筛 取并集**（OR），不是交集。
    这决定注入摘要的召回范围，取错了会漏注入真实教训。
    """
    fails = []

    def chk(name, got, expect):
        okk = (got == expect)
        print("  %s %-48s 期望=%-18s 实得=%s"
              % ("✅" if okk else "❌", name, expect, got))
        if not okk:
            fails.append(name)

    print("🧪 failure_memory 判别力自测\n")

    recs = [
        {"id": "f-1", "member_id": "contradiction-analyst", "severity": "major",
         "fail_type": "matrix", "fail_date": "2026-10-01",
         "symptom": "凭记忆补全矛盾矩阵", "learned_rule": "必须走查询器",
         "tags": ["矩阵", "TRIZ"]},
        {"id": "f-2", "member_id": "patent-search-scout", "severity": "critical",
         "fail_type": "envelope", "fail_date": "2026-10-02",
         "symptom": "信封字段缺失", "learned_rule": "六项必填字段置前",
         "tags": ["信封"]},
        {"id": "f-3", "member_id": "", "severity": "minor",
         "fail_type": "general", "fail_date": "2026-09-01",
         "symptom": "通用教训", "learned_rule": "先查权威数据",
         "tags": ["通用"]},
    ]

    # ── 1. 成员筛 ──
    print("  ── 成员筛 ──")
    got = [d["id"] for d in recs if matches(d, ["contradiction-analyst"], [])]
    chk("成员筛精确命中", got, ["f-1"])
    got = [d["id"] for d in recs if matches(d, ["nobody"], [])]
    chk("成员筛无命中 → 空", got, [])

    # ── 2. 关键词筛（跨字段：symptom/rule/tags/member/fail_type）──
    print("\n  ── 关键词筛 ──")
    chk("关键词命中 tags", [d["id"] for d in recs if matches(d, [], ["矩阵"])], ["f-1"])
    chk("关键词命中 learned_rule", [d["id"] for d in recs if matches(d, [], ["查询器"])], ["f-1"])
    chk("关键词命中 symptom", [d["id"] for d in recs if matches(d, [], ["信封字段"])], ["f-2"])
    chk("关键词命中 fail_type", [d["id"] for d in recs if matches(d, [], ["matrix"])], ["f-1"])

    # ── 3. 成员 + 关键词 = **并集**（OR），不是交集 ──
    print("\n  ── 成员+关键词 取并集（关键）──")
    got = [d["id"] for d in recs
           if matches(d, ["contradiction-analyst"], ["信封"])]
    chk("并集：成员命中 + 关键词命中", got, ["f-1", "f-2"])

    # ── 4. 全空条件 = 全收 ──
    print("\n  ── 空条件 ──")
    chk("无成员无关键词 → 全收", len([d for d in recs if matches(d, [], [])]), 3)

    # ── 5. 排序：severity 优先（critical → major → minor），同 severity 按日期 ──
    print("\n  ── 排序 ──")
    ordered = sorted(recs, key=sort_key)
    chk("severity 优先级顺序", [d["id"] for d in ordered], ["f-2", "f-1", "f-3"])
    chk("SEVERITY_RANK 映射", SEVERITY_RANK["critical"], 0)

    # ── 6. 截断 ──
    print("\n  ── 截断 ──")
    chk("brief 不超长时原样返回", brief("短文本", 10), "短文本")
    chk("brief 超长时截断+省略号", brief("a" * 50, 10), "a" * 9 + "…")
    chk("brief 折叠空白", brief("a   b\n\nc", 20), "a b c")

    # ── 7. 摘要渲染（空结果必须显式说明，不能静默空白）──
    print("\n  ── 摘要渲染 ──")
    empty_digest = render_digest([], [], [], False)
    chk("空记录 → 显式声明无记录", "无相关失败记录" in empty_digest, True)
    full_digest = render_digest(recs, [], [], False)
    chk("有记录 → 含标题", "失败记忆摘要" in full_digest, True)
    chk("有记录 → 含记录 id", "f-1" in full_digest or "f1" in full_digest, True)

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    print("\n✅ 自测全通过")
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
    ap.add_argument("--self-test", action="store_true", help="判别力自测")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()

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
