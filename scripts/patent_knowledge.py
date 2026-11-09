#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patent_knowledge.py — 专利族谱记忆（U3 · 2026-11-07 升维）
================================================================
把每次 scout 查新产出中的 X/Y 级威胁专利沉淀为跨任务知识库（knowledge/patent-family.jsonl），
同领域二次发明时 Phase 3 前先召回，免重复检索 + 提供"已知雷区"先验。

数据纪律（与团队红线同源）：
  - 只收 X/Y 级（威胁级）；A/R/P/E 不收（信息量低、噪音大）
  - 每条必含：patent_no / title / grade / domain / exposed_features / source_task
  - **凭记忆红线不适用豁免**：入库专利号必须来自 scout 落盘产出（机械提取），
    本脚本不手抄不合并外部数据
  - 去重键 = patent_no + domain（同专利跨域分别记——暴露特征可能不同）

用法：
  python3 scripts/patent_knowledge.py ingest tests/baselines/l2-full-a01/T-...__patent-search-scout.md \
      --domain 畜牧养殖/粪污处理            # 从 scout 产出沉淀
  python3 scripts/patent_knowledge.py ingest tests/baselines/l2-full-a01/ --domain 畜牧养殖/粪污处理
                                                    # 目录模式：自动找 *__patent-search-scout.md
  python3 scripts/patent_knowledge.py query 粪污 刮粪      # 按关键词召回
  python3 scripts/patent_knowledge.py query --domain 畜牧养殖
  python3 scripts/patent_knowledge.py stats                 # 库存统计

退出码：0=正常 1=无匹配/无数据 2=用法错
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
KB_PATH = os.path.join(PKG, "knowledge", "patent-family.jsonl")

PAT_NO_RE = r"(CN|US|EP|WO|JP|KR)[0-9]{7,14}[A-Z]?"
# CYCLE-1 · S-E45（单源化）：本常量此前**定义后从未被引用**，
# 而下方 parse_scout_output() 另写了一条功能等价的正则 —— 两条正则可各自漂移
# （如一条支持「### 4.1 X 类」编号在前、另一条不支持），
# 导致「常量看起来是规范、正则却各写各的」。现把**切分实现**下沉到常量，
# 解析处直接消费，形成唯一真源。
#
# 判据：标题形如「### 4.1 X 类（威胁）」——编号在前，X/Y 与「类」间允许空格；
# 捕获组1 = 等级(X/Y)，组2 = 节正文（到下一个标题为止）。
GRADE_SEC_RE = re.compile(
    r"^#{2,4}[^\n]*?\b(X|Y)\s*类[^\n]*$\n([^#]*?)(?=^#{2,4}\s|\Z)",
    re.M | re.S)


def _ensure_kb():
    os.makedirs(os.path.dirname(KB_PATH), exist_ok=True)
    if not os.path.isfile(KB_PATH):
        open(KB_PATH, "w", encoding="utf-8").close()


def _load_kb():
    entries = []
    if os.path.isfile(KB_PATH):
        for line in open(KB_PATH, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    return entries


def parse_scout_output(md_path, domain):
    """从 scout 落盘产出提取 X/Y 威胁表 → entry 列表。

    解析规则（面向结构的确定性提取，非语义判断）：
      - 找「### 4.1 X 类」「### 4.2 Y 类」等节（#{2,4} + X/Y + 类）
      - 节内表格行：| 专利号 | 标题 | ... | ——前两列固定，后续列拼 exposed_features
      - 专利号不匹配 PAT_NO_RE 的行跳过（存疑/申请号线索不入库）
    """
    text = open(md_path, encoding="utf-8").read()
    task_id = "-"
    m = re.search(r'"task_id"\s*:\s*"(T-[^"]+)"', text)
    if m:
        task_id = m.group(1)
    entries = []
    # 按 X/Y 节切分（标题形如「### 4.1 X 类（…）」——编号在前，X/Y 与「类」间允许空格）
    for sec_m in GRADE_SEC_RE.finditer(text):   # S-E45：消费唯一真源常量
        grade = sec_m.group(1)
        body = sec_m.group(2)
        for line in body.split("\n"):
            line = line.strip()
            if not line.startswith("|") or set(line) <= set("|-: \n"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 2 or not re.fullmatch(PAT_NO_RE, cols[0]):
                continue
            pat_no, title = cols[0], cols[1]
            features = "；".join(c for c in cols[2:] if c and not re.match(r"^[-—\s]*$", c))
            entries.append({
                "patent_no": pat_no,
                "title": title,
                "grade": grade,
                "domain": domain,
                "exposed_features": features[:300],
                "source_task": task_id,
                "source_file": os.path.relpath(md_path, PKG),
            })
    return entries


def cmd_ingest(args):
    targets = []
    if os.path.isdir(args.scout_output):
        targets = sorted(glob.glob(os.path.join(args.scout_output, "**", "*__patent-search-scout.md"), recursive=True))
    elif os.path.isfile(args.scout_output):
        targets = [args.scout_output]
    else:
        print(f"❌ 路径不存在: {args.scout_output}")
        return 2
    if not targets:
        print("❌ 目录内无 *__patent-search-scout.md 产出")
        return 1

    _ensure_kb()
    existing = {(e["patent_no"], e["domain"]) for e in _load_kb()}
    added, skipped = 0, 0
    with open(KB_PATH, "a", encoding="utf-8") as f:
        for t in targets:
            for e in parse_scout_output(t, args.domain):
                key = (e["patent_no"], e["domain"])
                if key in existing:
                    skipped += 1
                    continue
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
                existing.add(key)
                added += 1
    print(f"✅ 专利族谱沉淀：+{added} 条（去重跳过 {skipped}）→ {os.path.relpath(KB_PATH, PKG)}")
    return 0


def cmd_query(args):
    entries = _load_kb()
    if not entries:
        print("库为空（先跑 ingest 沉淀 scout 产出）")
        return 1
    hits = entries
    if args.domain:
        hits = [e for e in hits if args.domain in e.get("domain", "")]
    for kw in args.keywords or []:
        hits = [e for e in hits if kw in json.dumps(e, ensure_ascii=False)]
    if not hits:
        print(f"无匹配（domain={args.domain} keywords={args.keywords}；库存 {len(entries)} 条）")
        return 1
    # X 级排前（威胁更高），同级按专利号
    hits.sort(key=lambda e: (0 if e["grade"] == "X" else 1, e["patent_no"]))
    print(f"🔍 召回 {len(hits)}/{len(entries)} 条（X级 {sum(1 for e in hits if e['grade']=='X')} / Y级 {sum(1 for e in hits if e['grade']=='Y')}）\n")
    n_outdated = 0
    for e in hits:
        if e.get("outdated"):
            n_outdated += 1
        icon = "🔴" if e["grade"] == "X" else "🟠"
        mark = " ⚫[已失效]" if e.get("outdated") else ""
        print(f"{icon} {e['patent_no']}（{e['grade']}级·{e['domain']}·源 {e['source_task']}）{mark}")
        print(f"   {e['title']}")
        print(f"   已公开: {e['exposed_features'][:120]}{'…' if len(e['exposed_features'])>120 else ''}")
        if e.get("outdated"):
            print(f"   ⚫ 失效: {e.get('outdated_reason')}（{e.get('outdated_at')}）——不可作为现行威胁依据")
    print("\n⚠️ 使用纪律：召回结果是「已知雷区先验」不是查新结论——Phase 3 三轮查新不可省，"
          "召回用于 R1 检索式预热与差异化路径预判。")
    return 0


def cmd_stats(args):
    entries = _load_kb()
    if not entries:
        print("库为空")
        return 1
    by_grade = {}
    by_domain = {}
    for e in entries:
        by_grade[e["grade"]] = by_grade.get(e["grade"], 0) + 1
        by_domain[e["domain"]] = by_domain.get(e["domain"], 0) + 1
    n_out = sum(1 for e in entries if e.get("outdated"))
    print(f"📚 专利族谱库存：{len(entries)} 条（其中已失效 {n_out} 条）")
    for g, n in sorted(by_grade.items()):
        print(f"  {g}级: {n}")
    for d, n in sorted(by_domain.items(), key=lambda x: -x[1]):
        print(f"  域「{d}」: {n}")


def cmd_outdated(args):
    """标注库条目失效（scout MD「失效反馈机制」的兑现命令）。

    用法：patent_knowledge.py outdated CN223231803U --reason "本轮检索确认已被无效宣告"
    条目不删除——打 outdated:true + reason + 时间戳（保留雷区历史，防止二次引用）。
    """
    entries = _load_kb()
    hit = None
    for e in entries:
        if e.get("patent_no") == args.patent_no:
            hit = e
            break
    if not hit:
        print(f"❌ 库中无 {args.patent_no}（用 query/stats 先核对编号）")
        return 1
    import datetime
    hit["outdated"] = True
    hit["outdated_reason"] = args.reason
    hit["outdated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(KB_PATH, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"✅ 已标注失效：{args.patent_no}（{args.reason}）——条目保留，query 时标记 🔴⚫")
    return 0


def main():
    ap = argparse.ArgumentParser(description="专利族谱记忆（跨任务查新沉淀与召回）")
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("ingest", help="从 scout 产出沉淀 X/Y 威胁")
    p1.add_argument("scout_output", help="scout 产出文件或其所在目录")
    p1.add_argument("--domain", required=True, help="领域标签（如 畜牧养殖/粪污处理）")

    p2 = sub.add_parser("query", help="按域/关键词召回")
    p2.add_argument("keywords", nargs="*", help="关键词（标题/特征内子串匹配）")
    p2.add_argument("--domain", help="域过滤（子串）")

    sub.add_parser("stats", help="库存统计")

    p3 = sub.add_parser("outdated", help="标注库条目失效（不删除，打标记）")
    p3.add_argument("patent_no", help="专利号（如 CN223231803U）")
    p3.add_argument("--reason", required=True, help="失效理由（如 已被无效宣告/公开不充分）")

    args = ap.parse_args()
    if args.cmd == "ingest":
        return cmd_ingest(args)
    if args.cmd == "query":
        return cmd_query(args)
    if args.cmd == "stats":
        return cmd_stats(args)
    if args.cmd == "outdated":
        return cmd_outdated(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
