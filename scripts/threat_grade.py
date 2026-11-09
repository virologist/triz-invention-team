#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
threat_grade.py — X/E 级威胁判定的**唯一真源**（CYCLE-1 · S-E53）
================================================================
背景：X 级威胁计数此前散落三处，且判据互不相同：

  1. scripts/preflight_check.py:scan_x_grade()   —— 宽松正则 `X\\s*[\\W_]*\\s*(\\d+)`
  2. scripts/patent_knowledge.py:GRADE_SEC_RE     —— 结构化（标题 + 表格行 + 专利号正则）
  3. skills/patent-law/SKILL.md §四 C3 定义      —— 散文「分级出现 X 或 E 时」

第 1 条与第 2 条对同一语义给出不同答案（幽灵验证项形态 E：判据式的两个来源实为
同一来源的两种写法），且第 1 条误判率高到会**假触发 C3 阻断**——
「本产出无 X 级威胁」被读成 1 条 X 级 → scout 正常流程被无端阻断。

本模块把「一份 scout 产出里有多少条 X 级 / E 级威胁」变成**唯一结构化判据**，
供 preflight（C3 自动触发）与 patent_knowledge（族谱沉淀）共同消费。

设计要点（原则②机械计量优先于自报 / 原则④禁止幽灵验证项）：
  - **只认结构，不认散文措辞**：JSON `xyape_grades` 数组，或 Markdown 分级表节
    （`### 4.1 X 类`）+ 表内专利号行。三种合法载体都覆盖，其余一律不计入。
  - **专利号必须过 PAT_NO_RE**：杜绝「X 39 参数」「坐标系 X 100」等误命中。
  - **否定表述不计数**：「本产出无 X 级威胁」→ 0 条。
  - **E 类独立计数**：C3 的权威触发条件是「出现 X **或** E」，此前 preflight
    只扫 X，漏 E 触发 —— 属判据与 skill 契约漂移，本模块一并修正。

用法：
  python3 scripts/threat_grade.py --self-test          # 判别力自测（变异测试用）
  python3 scripts/threat_grade.py <scout_md>           # 打印 X/E 级计数
  python3 scripts/threat_grade.py <scout_md> --json    # 机器可读输出
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

# 专利号真源：与 patent_knowledge.PAT_NO_RE 同形（单一真源由本模块导出，
# patent_knowledge 反向 import 本模块，消除双份手抄）。
PAT_NO_RE = r"(CN|US|EP|WO|JP|KR)[0-9]{7,14}[A-Z]?"
_PAT_NO_FULL_RE = re.compile(PAT_NO_RE)

# Markdown 分级节标题：形如「### 4.1 X 类（单独影响新颖性…）」
# 捕获组1 = 等级字母（X/Y/A/R/P/E），组2 = 节正文（到下一个标题为止）。
GRADE_SEC_RE = re.compile(
    r"^#{2,4}[^\n]*?\b([XYARPE])\s*类[^\n]*$\n([^#]*?)(?=^#{2,4}\s|\Z)",
    re.M | re.S)

# JSON 分级键：同时支持**数组形态**与**字符串形态**
#   数组形态：`"X": [ "CN223231803U", ... ]`（真实基线 A01 形态）
#   字符串形态：`"E": "无（可检索范围内未见）"` / `"R": "不适用（…）"`（真实基线形态）
# 两种形态都必须进入否定值判断，否则字符串形态的 E 会被整体漏判
# —— 这正是本轮变异测试 M2 暴露的判别力缺口。
_JSON_GRADE_RE = re.compile(
    r'"(?P<grade>[XYARPE])"\s*:\s*(?P<value>\[[^\]]*\]|"[^"]*")', re.S)

# 「无 / 不适用 / 未检索」等否定值——这些值表示该等级**没有威胁条目**，
# 不是威胁本身，必须排除（否则「"E": "无（…）"」会被误判）。
_NEGATIVE_VALUES = (
    "无", "不适用", "未检索", "不适用（", "无（", "未见", "不涉及",
    "n/a", "none", "n/a（",
)


def _norm_pat(token):
    """从一段文本中抽出合法专利号（只取第一个匹配）。"""
    m = _PAT_NO_FULL_RE.search(token)
    return m.group(0) if m else None


def _is_negative(text):
    """判断一个分级值是否为否定表述（无 / 不适用 / 未检索 …）。"""
    t = (text or "").strip()
    if not t:
        return True
    low = t.lower()
    for neg in _NEGATIVE_VALUES:
        if low.startswith(neg.lower()):
            return True
    return False


def extract_grade_counts(text):
    """从一份 scout 产出文本中提取各等级威胁条目数（按专利号去重）。

    返回 {
      "counts":  {"X": n, "Y": n, ...},     # 去重后的条目数
      "sources": {"X": ["json:5", "md:5"], ...},  # 各载体各自命中数（诊断用）
      "carriers": ["json:xyape_grades", "md:###4.1 X类"],  # 识别到的载体形态
      "patents": {"X": ["CN...", ...]},    # 去重后的专利号清单
    }

    关键设计（S-E53 变异测试暴露的第三个缺口）：
      - **按专利号去重**：真实产出中同一批文献会同时出现在 JSON 信封的
        `xyape_grades` 数组与 Markdown 分级表里（基线 A01 即如此）。
        不去重 → X 级被数成 10 条（实为 5 条）。
      - **去重只在等级内部**：同一文献可同时出现在 X 与 Y（基线 CN202279501U
        即如此），跨等级去重会漏掉 Y 级威胁。
      - **carriers 与 counts 分离**：count=0 有两种截然不同的含义——
        「确实无威胁」与「未识别到任何分级载体（无法机械判定）」。
        二者不可混同，否则恒返回 0 = 幽灵验证项形态 B。
    """
    pat_sets = {g: [] for g in "XYARPE"}
    seen = {g: set() for g in "XYARPE"}
    sources = {}
    carriers = []

    # ── 来源 1：JSON 信封形态 —— "xyape_grades": { "X": [...], "E": "无（…）" }
    json_hits = False
    for m in _JSON_GRADE_RE.finditer(text):
        grade = m.group("grade")
        raw = m.group("value")
        is_array = raw.startswith("[")
        body = raw[1:-1]
        if not is_array:
            # 字符串形态：整段当一个值判否定
            if _is_negative(body):
                continue
        else:
            body_items = [x for x in re.split(r"[,\n]", body) if x.strip()]
        if is_array:
            # 数组内逐项抽专利号；字符串值可能带中文后缀说明，只取号本身
            n = 0
            for it in body_items:
                p = _norm_pat(it)
                if p and p not in seen[grade]:
                    seen[grade].add(p)
                    pat_sets[grade].append(p)
                    n += 1
        else:
            # 字符串形态若含专利号 → 视为 1 条威胁（如 "E": "CN123456789A"）
            p = _norm_pat(body)
            n = 0
            if p and p not in seen[grade]:
                seen[grade].add(p)
                pat_sets[grade].append(p)
                n = 1
        if n:
            json_hits = True
            sources.setdefault(grade, []).append("json:%d" % n)
    if json_hits:
        carriers.append("json:xyape_grades")

    # ── 来源 2：Markdown 分级表节 —— 「### 4.1 X 类」+ 表内专利号行
    md_carrier = False
    for m in GRADE_SEC_RE.finditer(text):
        grade = m.group(1)
        body = m.group(2)
        n = 0
        for line in body.split("\n"):
            line = line.strip()
            if not line.startswith("|"):
                continue
            if set(line) <= set("|-: \n"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 2:
                continue
            p = _norm_pat(cols[0])
            if not p:
                continue
            md_carrier = True
            if p in seen[grade]:
                continue
            seen[grade].add(p)
            pat_sets[grade].append(p)
            n += 1
        if n:
            sources.setdefault(grade, []).append("md:%d" % n)
    if md_carrier:
        carriers.append("md:分级表节")

    counts = {g: len(pat_sets[g]) for g in "XYARPE"}
    return {"counts": counts, "sources": sources,
            "carriers": carriers, "patents": pat_sets}


def scan_grade_counts(md_path):
    """扫描指定 scout 产出文件，返回 X/E 级计数。

    返回 (x_count, e_count, detail)；
      - detail["verdict"] ∈ {"determined", "no_carrier", "unreadable"}
        "determined"  = 识别到分级载体，计数可信
        "no_carrier"  = 未识别到任何分级载体 → **不可判定**（≠ 确实无威胁）
        "unreadable"  = 文件不可读
      - detail["carriers"] 识别到的载体形态列表
    """
    detail = {"path": md_path, "exists": False, "verdict": "no_carrier"}
    if not md_path or not os.path.isfile(md_path):
        return 0, 0, detail
    try:
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        detail["error"] = str(e)
        detail["verdict"] = "unreadable"
        return 0, 0, detail
    detail["exists"] = True
    res = extract_grade_counts(text)
    detail["counts"] = res["counts"]
    detail["sources"] = res["sources"]
    detail["carriers"] = res["carriers"]
    detail["patents"] = res["patents"]
    detail["verdict"] = "determined" if res["carriers"] else "no_carrier"
    return res["counts"].get("X", 0), res["counts"].get("E", 0), detail


def latest_scout_output(member_id, outputs_dir):
    """找出该成员在 outputs_dir 下的最新落盘产出（沿用 preflight 原 glob 语义）。"""
    import glob
    if not member_id or not os.path.isdir(outputs_dir):
        return None
    pattern = os.path.join(outputs_dir, "T-*__" + member_id + ".md")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def c3_should_trigger(x_count, e_count):
    """C3 触发判定：分级出现 X **或** E 时触发。

    权威依据：skills/patent-law/SKILL.md §四 检查点表
    「C3 | 对比文件分级出现 X 或 E 时 | 直接决定方案是否可申请，必须与用户确认再推进 Phase 4」
    """
    return (x_count or 0) > 0 or (e_count or 0) > 0


# ─────────────────────────────────────────────────────────────────────
# 判别力自测（S-E53 · 变异测试靶点）
# ─────────────────────────────────────────────────────────────────────
_SELF_TEST_CASES = [
    # (用例名, 文本, 期望X, 期望E, 期望来源标记)
    ("真实基线A01表格形态-X级5条",
     "### 4.1 X 类（最高威胁）\n\n| 专利号 | 标题 |\n|---|---|\n"
     "| CN223231803U | 畜牧养殖刮粪装置 |\n| CN214126439U | 猪舍粪污处理设备 |\n",
     2, 0, "md"),
    ("JSON形态-分级数组",
     '{"xyape_grades": {"X": ["CN223231803U", "CN214126439U"], '
     '"Y": ["CN224124877U"], "E": "无（可检索范围内未见）"}}',
     2, 0, "json"),
    ("否定表述-无X级威胁",
     "本产出无 X 级威胁。", 0, 0, None),
    ("坐标轴误伤-坐标系X 100",
     "坐标系 X 100, Y 200", 0, 0, None),
    ("XML误伤-XML解析完成12条",
     "XML 解析完成 12 条记录", 0, 0, None),
    ("PX误伤-PX 5",
     "PX 5", 0, 0, None),
    ("参数误伤-X 39 参数",
     "X 39 参数", 0, 0, None),
    ("无关文本-实验 t 12",
     "实验 t 12", 0, 0, None),
    ("E类触发-E类有一条",
     '{"xyape_grades": {"X": [], "E": ["CN123456789A"]}}',
     0, 1, "json"),
    ("E类否定-E类为无",
     '{"xyape_grades": {"E": "无（未见）"}}', 0, 0, None),
    # ── 以下用例为**判别力补强**（变异测试 M1/M2 暴露缺口后追加）──
    # M1 靶点：专利号正则被放宽时，必须仍能识别「非专利号 → 不计数」
    ("判别力-宽正则也不误伤-X坐标值",
     '{"xyape_grades": {"X": "坐标系 X 100"}}', 0, 0, None),
    ("判别力-宽正则也不误伤-普通词",
     '{"xyape_grades": {"X": "无"}}', 0, 0, None),
    # M2 靶点：否定值过滤被删时，**字符串形态**的否定必须仍判 0
    ("判别力-字符串否定过滤-E类为无",
     '{"xyape_grades": {"R": "无（可检索范围内未见）", '
     '"P": "不适用（任务包明示无优先权）"}}', 0, 0, None),
    ("判别力-字符串否定过滤-X类为无",
     '{"xyape_grades": {"X": "无"}}', 0, 0, None),
    # ── M2 的真正判别场景 ──
    # 否定表述里**带专利号**（真实场景：scout 写「未检索到（线索 CN… 存疑，不计入）」）
    # → 必须判 0，否则「无威胁」被读成 1 条 E → 假触发 C3 阻断
    ("判别力-否定含专利号-E类未检索到",
     '{"xyape_grades": {"E": "未检索到（线索 CN202311321256.8 存疑，不计入）"}}',
     0, 0, None),
    # 对照：否定词出现在**专利号之后**时不算否定（防止过度收紧→漏判）
    ("判别力-非否定场景-X类含说明文字",
     '{"xyape_grades": {"X": "CN223231803U（针对无磨损场景）"}}', 1, 0, "json"),
    # ── 双载体去重（真实基线 A01：JSON 数组 + Markdown 表格同批文献）──
    ("双载体去重-同批文献只计一次",
     '{"xyape_grades": {"X": ["CN223231803U", "CN214126439U"]}}\n\n'
     "### 4.1 X 类\n\n| 专利号 | 标题 |\n|---|---|\n"
     "| CN223231803U | 畜牧养殖刮粪装置 |\n| CN214126439U | 猪舍粪污处理设备 |\n",
     2, 0, "json"),
    # ── 跨等级不去重（同一文献可同属 X 与 Y）──
    ("跨等级不去重-同文献X与Y各计一条",
     "### 4.1 X 类\n\n| 专利号 | 标题 |\n|---|---|\n| CN202279501U | 双色刮除器 |\n\n"
     "### 4.2 Y 类\n\n| 专利号 | 标题 |\n|---|---|\n| CN202279501U | 双色刮除器 |\n",
     1, 0, "md"),
]


def _self_test():
    """判别力自测：每条用例必须同时满足「期望值命中」与「来源标记正确」。

    判别力验收标准（原则④）：改坏真源后本测试必须报错；
    还原后必须 PASS。若某用例在错误实现下同样通过 → 该用例无判别力，
    应被剔除（否则自测本身沦为形式化验证）。
    """
    fails = []
    print("🧪 threat_grade 判别力自测（%d 用例）\n" % len(_SELF_TEST_CASES))
    for name, text, exp_x, exp_e, exp_src in _SELF_TEST_CASES:
        res = extract_grade_counts(text)
        got_x = res["counts"].get("X", 0)
        got_e = res["counts"].get("E", 0)
        src = None
        for g in ("X", "E"):
            if res["sources"].get(g):
                src = res["sources"][g][0].split(":")[0]
                break
        ok_x = (got_x == exp_x)
        ok_e = (got_e == exp_e)
        ok_src = (src == exp_src) if exp_src else (src is None)
        passed = ok_x and ok_e and ok_src
        flag = "✅" if passed else "❌"
        print("  %s %-28s 期望X=%d/E=%d 来源=%-4s | 实得X=%d/E=%d 来源=%s"
              % (flag, name, exp_x, exp_e, exp_src or "-", got_x, got_e, src or "-"))
        if not passed:
            fails.append((name, "X" if not ok_x else "E" if not ok_e else "来源"))

    # C3 触发语义自测
    print("\n  ── C3 触发语义 ──")
    for desc, x, e, expect in [
        ("X=4,E=0 → 触发", 4, 0, True),
        ("X=0,E=1 → 触发（E 类同样触发 C3）", 0, 1, True),
        ("X=0,E=0 → 不触发", 0, 0, False),
    ]:
        got = c3_should_trigger(x, e)
        flag = "✅" if got == expect else "❌"
        print("  %s %s" % (flag, desc))
        if got != expect:
            fails.append((desc, "c3"))

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    print("\n✅ 自测全通过（%d 用例 + 3 项 C3 语义）" % len(_SELF_TEST_CASES))
    return 0


def main():
    ap = argparse.ArgumentParser(description="X/E 级威胁判定唯一真源")
    ap.add_argument("scout_output", nargs="?", help="scout 产出文件路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--self-test", action="store_true", help="判别力自测")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()

    if not args.scout_output:
        ap.print_help()
        return 2
    x, e, detail = scan_grade_counts(args.scout_output)
    if args.json:
        print(json.dumps({"x_count": x, "e_count": e, "detail": detail},
                         ensure_ascii=False, indent=2))
    else:
        print("X 级 %d 条 / E 级 %d 条" % (x, e))
        print("C3 应触发：%s" % ("是" if c3_should_trigger(x, e) else "否"))
        if "counts" in detail:
            print("全等级：%s" % json.dumps(detail["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
