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

# CYCLE-1 · S-E53：X/Y 级判定与专利号正则的唯一真源在 scripts/threat_grade.py
# （与 preflight_check.py 共用）。此处 import 使两处判据**必然同形**。
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import threat_grade  # noqa: E402

PAT_NO_RE = threat_grade.PAT_NO_RE
# CYCLE-1 · S-E45（单源化）：本常量此前**定义后从未被引用**，
# 而下方 parse_scout_output() 另写了一条功能等价的正则 —— 两条正则可各自漂移
# （如一条支持「### 4.1 X 类」编号在前、另一条不支持），
# 导致「常量看起来是规范、正则却各写各的」。现把**切分实现**下沉到常量，
# 解析处直接消费，形成唯一真源。
#
# CYCLE-1 · S-E53（真源合并）：本模块的 GRADE_SEC_RE 与 PAT_NO_RE 与
# scripts/preflight_check.py 的 X 级扫描曾是**两套独立手抄**——preflight 用宽松
# 正则 `X\s*[\W_]*\s*(\d+)`，本模块用结构化判据，对同一语义给出不同答案
# （preflight 对 7 个真实场景误判 4 例，最严重「本产出无 X 级威胁」误判为 1 条
# → 假触发 C3 阻断）。
# 现统一由 scripts/threat_grade.py 导出，本模块与 preflight 共同消费 →
# 「X 级有几条」只有一份判据，改一处即全链路同步。
GRADE_SEC_RE = threat_grade.GRADE_SEC_RE


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
    #
    # CYCLE-1 · S-E59（单源化的副作用清偿）：S-E53 把 GRADE_SEC_RE 收敛到
    # threat_grade 后，该正则的等级组从 [XY] 放宽为 [XYARPE]（threat_grade 需要
    # 统计全部 6 级）→ 本模块**顺带把 A 级也收了**（实测 A01 基线多出 11 条 A 级），
    # 违反本文件的数据纪律「只收 X/Y 级；A/R/P/E 不收（信息量低、噪音大）」。
    # 根因：真源合并后**消费方的过滤义务被稀释**。
    # 现显式按本模块的收库范围过滤——真源管「怎么解析」，本模块管「收什么」。
    for sec_m in GRADE_SEC_RE.finditer(text):   # S-E45：消费唯一真源常量
        grade = sec_m.group(1)
        if grade not in ("X", "Y"):            # S-E59：只收威胁级
            continue
        body = sec_m.group(2)
        for line in body.split("\n"):
            line = line.strip()
            if not line.startswith("|") or set(line) <= set("|-: \n"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 2 or not re.fullmatch(PAT_NO_RE, cols[0]):
                continue
            pat_no, title = cols[0], cols[1]
            # S-E61（消费方过滤义务显式化）：真源 PAT_NO_RE 现同时覆盖
            # 「授权公告号」（CN223231803U）与「申请号」（CN202311321256.8）。
            # 申请号**尚未公开审查结论**，本库的用途是「跨任务复用已核验的
            # 对比文件族谱」→ 申请号**不入库**（只保留在 scout 原始产出中）。
            # 判据：含小数点校验码者 = 申请号形态。
            if "." in pat_no:
                continue
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


def _self_test():
    """判别力自测（S-E58）：scout 产出解析 + 专利号正则 + 否定值过滤。

    与 threat_grade 共用真源（S-E53），本自测验证**族谱沉淀**这条消费路径
    不会因上游改动而静默失效。
    """
    import threat_grade as TG
    fails = []

    def chk(name, got, expect):
        okk = (got == expect)
        print("  %s %-48s 期望=%-18s 实得=%s"
              % ("✅" if okk else "❌", name, expect, got))
        if not okk:
            fails.append(name)

    print("🧪 patent_knowledge 判别力自测\n")

    # ── 1. 真源一致性（必须与 threat_grade 同形）──
    print("  ── 真源一致性 ──")
    chk("PAT_NO_RE == threat_grade.PAT_NO_RE", PAT_NO_RE, TG.PAT_NO_RE)
    chk("GRADE_SEC_RE == threat_grade.GRADE_SEC_RE",
        GRADE_SEC_RE.pattern, TG.GRADE_SEC_RE.pattern)

    # ── 2. 专利号正则 ──
    print("\n  ── 专利号正则 ──")
    for pat in ("CN223231803U", "CN214126439U", "US1234567B1", "EP1234567A"):
        chk("合法专利号 %s" % pat, bool(re.fullmatch(PAT_NO_RE, pat)), True)
    for bad in ("CN123", "123456789", "XX223231803U", "CN223231803UU"):
        chk("非法专利号 %s" % bad, bool(re.fullmatch(PAT_NO_RE, bad)), False)
    # S-E61（真源收紧后消费方同步）：申请号形态（CN+数字+小数点校验码）
    # 现已是**合法专利号形态**（THREAT 判定必须计入，否则漏计 X 级威胁）；
    # 但本模块的收库纪律是「只收已公开的授权公告号」——
    # 申请号尚未公开审查结论，**不入族谱库**。
    # 真源管「怎么解析」，本模块管「收什么」——与 S-E59 的等级过滤同型。
    chk("申请号形态是合法专利号（S-E61 真源）",
        bool(re.fullmatch(PAT_NO_RE, "CN202311321256.8")), True)
    chk("纯数字号段不是专利号（S-E61 反证）",
        bool(re.fullmatch(PAT_NO_RE, "CN202279501")), False)

    # ── 3. Markdown 分级节解析 ──
    print("\n  ── 分级节解析 ──")
    md = ("### 4.1 X 类（最高威胁）\n\n"
          "| 专利号 | 标题 | 特征 |\n|---|---|---|\n"
          "| CN223231803U | 畜牧养殖刮粪装置 | 免工具拆装 |\n"
          "| CN214126439U | 猪舍粪污处理设备 | 弹性卡块 |\n\n"
          "### 4.2 Y 类（组合威胁）\n\n"
          "| 专利号 | 标题 | 组合 |\n|---|---|---|\n"
          "| CN224124877U | 养猪舍用刮粪车 | 与CN223231803U组合 |\n")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, "T-20261015-A01__patent-search-scout.md")
        open(fp, "w", encoding="utf-8").write(md)
        entries = parse_scout_output(fp, "测试域")
        chk("解析条目数", len(entries), 3)
        chk("X 级条数", sum(1 for e in entries if e["grade"] == "X"), 2)
        chk("Y 级条数", sum(1 for e in entries if e["grade"] == "Y"), 1)
        chk("首条专利号", entries[0]["patent_no"] if entries else None, "CN223231803U")
        chk("首条标题", entries[0]["title"] if entries else None, "畜牧养殖刮粪装置")
        chk("域标签写入", entries[0]["domain"] if entries else None, "测试域")
        chk("task_id 缺省为 -", entries[0]["source_task"] if entries else None, "-")

        # 无效专利号行必须跳过（存疑线索不入库）
        md_bad = md + "\n| 申请号线索 CN202520926963.8 | 存疑 | 不入库 |\n"
        fp2 = os.path.join(td, "T-20261015-A02__patent-search-scout.md")
        open(fp2, "w", encoding="utf-8").write(md_bad)
        chk("无效专利号行被跳过", len(parse_scout_output(fp2, "测试域")), 3)

        # 空产出 → 空列表（不编造）
        fp3 = os.path.join(td, "T-20261015-A03__patent-search-scout.md")
        open(fp3, "w", encoding="utf-8").write("没有分级节的普通文本")
        chk("无分级节 → 空列表", len(parse_scout_output(fp3, "测试域")), 0)

    # ── 4. 真实基线 ──
    print("\n  ── 真实基线 ──")
    real = os.path.join(PKG, "tests", "baselines", "l2-full-a01",
                        "T-20261015-A01__patent-search-scout.md")
    if os.path.isfile(real):
        e = parse_scout_output(real, "畜牧养殖/粪污处理")
        chk("A01 基线解析出条目", len(e) > 0, True)
        chk("A01 含 X 级", sum(1 for x in e if x["grade"] == "X") > 0, True)
        chk("A01 不含 A/R/P/E 级（只收 X/Y）",
            all(x["grade"] in ("X", "Y") for x in e), True)
    else:
        chk("A01 基线存在", False, True)

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    print("\n✅ 自测全通过")
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

    ap.add_argument("--self-test", action="store_true", help="判别力自测")
    args = ap.parse_args()
    if getattr(args, "self_test", False):
        return _self_test()
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
