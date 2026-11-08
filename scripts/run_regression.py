#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_regression.py — 回归测试集执行器（P2-9 · 2026-10-15 建立）
================================================================
定位：把 tests/cases/ 下的固定用例（task.md + expected.json）变成可复跑的断言引擎。
      本脚本**不 spawn 成员**（那是主理人的职责）——它做两件确定性的事：
        1. scaffold：准备运行目录 + 打印派单指令（供主理人复制执行）
        2. verify：对运行目录里的落盘产出逐条跑断言，输出 PASS/FAIL 报告

三层分级（与 expected.json 的 level 字段一致）：
  L1（单成员·分钟级）—— workflow-b-01（analyst）/ workflow-c-01（scout）：日常改动后必跑
  L2（全链路·45min级）—— workflow-a-01（全团队 6 成员）：版本发布前人工触发

用法：
  python3 scripts/run_regression.py --list
  python3 scripts/run_regression.py --case workflow-b-01 --scaffold
  python3 scripts/run_regression.py --case workflow-b-01 --dir tests/baselines
  python3 scripts/run_regression.py --case workflow-b-01 --dir <dir> --json

退出码：0=全部断言通过（INFO 不影响）  1=存在 FAIL  2=用法/环境错误
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
CASES_DIR = os.path.join(PKG, "tests", "cases")


# ══════════════════ 工具 ══════════════════

def load_case(case_id):
    """加载用例：expected.json + task.md 全文"""
    exp_path = os.path.join(CASES_DIR, case_id + ".expected.json")
    if not os.path.isfile(exp_path):
        print(f"❌ 用例不存在：{exp_path}", file=sys.stderr)
        return None, None, None
    with open(exp_path, encoding="utf-8") as f:
        exp = json.load(f)
    task_path = os.path.join(CASES_DIR, exp.get("task_package", case_id + ".task.md"))
    task_text = open(task_path, encoding="utf-8").read() if os.path.isfile(task_path) else ""
    return exp, task_text, task_path


def list_cases():
    out = []
    for p in sorted(glob.glob(os.path.join(CASES_DIR, "*.expected.json"))):
        try:
            exp = json.load(open(p, encoding="utf-8"))
            out.append(exp)
        except Exception as e:  # noqa
            print(f"⚠️ 解析失败 {p}: {e}", file=sys.stderr)
    return out


def member_files(run_dir):
    """返回 {member_id: filepath}（取每个成员最新落盘的 T-*__<member>.md）"""
    res = {}
    for p in sorted(glob.glob(os.path.join(run_dir, "T-*__*.md"))):
        name = os.path.basename(p)
        m = re.match(r"T-[^_]+__(.+)\.md$", name)
        if m:
            res[m.group(1)] = p
    return res


def read(path):
    return open(path, encoding="utf-8", errors="replace").read() if os.path.isfile(path) else ""


def strip_fences(text):
    """去掉围栏代码块（```…```）——自检清单/正则示例常在此，防假阳性"""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def strip_selfcheck_lines(text):
    """去掉“自检/禁用词/正则”展示行——这些行会罗列被禁词本身（failure-006 教训）"""
    keep = []
    for line in text.split("\n"):
        if any(k in line for k in ("禁用词", "正则", "regex", "扫描结果", "自检清单")):
            continue
        keep.append(line)
    return "\n".join(keep)


def extract_section(text, titles):
    """提取某段（## 或 ### 标题），返回正文；找不到返回 None"""
    for t in titles:
        pat = re.compile(r"^#{2,4}\s*" + re.escape(t) + r".*$", re.M)
        m = pat.search(text)
        if m:
            rest = text[m.end():]
            nxt = re.search(r"^#{1,4}\s", rest, re.M)
            return rest[:nxt.start()] if nxt else rest
    return None


def extract_first_json(text):
    """栈平衡扫描提取第一个可解析 JSON 对象（处理嵌套 {}）"""
    i = text.find("{")
    while i != -1:
        depth, j, in_str, esc = 0, i, False, False
        while j < len(text):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        blob = text[i:j + 1]
                        try:
                            return json.loads(blob)
                        except Exception:  # noqa
                            break
            j += 1
        i = text.find("{", i + 1)
    return None


# ══════════════════ 断言实现 ══════════════════

def check_task_package_elements(exp, task_text, run_dir, files, a):
    missing = [e for e in a["expect"] if not re.search(r"^##\s*" + re.escape(e), task_text, re.M)]
    if missing:
        return False, f"任务包缺要素: {missing}"
    return True, f"四要素齐全（{len(a['expect'])} 项）"


def check_envelope_required_fields(exp, task_text, run_dir, files, a):
    targets = list(files.values()) if exp.get("target_member") == "full-team" else (
        [files[exp["target_member"]]] if exp.get("target_member") in files else list(files.values()))
    if not targets:
        return False, "未找到任何成员落盘文件"
    bad = []
    for p in targets:
        env = extract_first_json(read(p))
        if not env:
            bad.append(f"{os.path.basename(p)}: 无 JSON 信封")
            continue
        miss = [k for k in a["expect"] if k not in env]
        if miss:
            bad.append(f"{os.path.basename(p)}: 缺 {miss}")
    return (not bad), ("全部信封 6 必填齐全" if not bad else "; ".join(bad))


def check_envelope_agent_id(exp, task_text, run_dir, files, a):
    mid = a["expect"]
    if mid not in files:
        return False, f"未找到 {mid} 的落盘文件"
    env = extract_first_json(read(files[mid]))
    if not env:
        return False, f"{mid}: 无 JSON 信封"
    got = env.get("agent_id")
    return got == mid, f"agent_id={got}（期望 {mid}）"


def check_min_count(exp, task_text, run_dir, files, a):
    mid = exp.get("target_member")
    p = files.get(mid) or (list(files.values())[0] if files else None)
    if not p:
        return False, "无落盘文件"
    n = len(re.findall(a["pattern"], read(p)))
    return n >= a["min"], f"{a.get('field','pattern')} 命中 {n}（≥{a['min']}）"


def check_forbidden_regex(exp, task_text, run_dir, files, a):
    scope = a.get("scope")
    p = None
    if scope == "claims":
        # 找撰写员产出的权项段
        for mid, fp in files.items():
            txt = read(fp)
            sec = extract_section(txt, ["权利要求", "权利要求书", "4. 权利要求"])
            if sec:
                p, txt_use = fp, sec
                break
        if p is None:
            return False, "未找到权项段（无法做 claims 范围禁用词校验）"
    else:
        mid = exp.get("target_member")
        p = files.get(mid) or (list(files.values())[0] if files else None)
        txt_use = read(p) if p else ""

    # R4 · 2026-11-07：禁词真源归一——patterns_source=frontmatter 时动态读成员
    # agents/<id>.md frontmatter forbidden_phrases（与 contract_enforce 同一真源），
    # 消除用例自带静态表这第三源漂移；静态 patterns 保留（claims 限定域等场景仍用）
    patterns = list(a.get("patterns") or [])
    if a.get("patterns_source") == "frontmatter":
        mid = exp.get("target_member")
        fm_pats, fm_err = _load_frontmatter_patterns(mid)
        if fm_err:
            return False, f"frontmatter 真源读取失败: {fm_err}"
        patterns = fm_pats + patterns
    if not patterns:
        return True, "（无禁词断言）"

    # R4：清洗与豁免与 contract_enforce 同构（同真源必须同行为，防两套工具判定漂移）
    txt_use = strip_selfcheck_lines(strip_fences(txt_use))
    try:
        import contract_enforce as CE
        txt_use = CE._clean_for_forbidden_scan(txt_use)
    except Exception:
        pass  # 独立部署无 contract_enforce 时退回基础清洗
    hits = []
    for pat in patterns:
        try:
            for m in re.finditer(pat, txt_use):
                s = max(0, m.start() - 10)
                window = txt_use[s:m.end() + 10]
                # 命中后走 contract_enforce 同款豁免（EXEMPT_WORDS / 反例标记 / 判断语境）
                try:
                    import contract_enforce as CE
                    wide = txt_use[max(0, m.start() - 30):m.end() + 30]
                    if any(w in wide for w in CE.EXEMPT_WORDS):
                        continue
                    if any(re.search(q, wide) for q in (
                        r"不得[凭基估按]", r"禁止[凭基估按]", r"非[凭代估按]",
                        r"无一[处个].{0,4}凭", r"[遵按]守?.{0,6}红线", r"红线[：:]",
                        r"可能[被导引为会]", r"可能[性体化]")):
                        continue
                    _ok, _ = CE._context_exempt(m, txt_use)
                    if _ok:
                        continue
                except Exception:
                    pass
                hits.append(f"「{pat}」@…{window}…")
        except re.error as e:
            return False, f"禁词正则无效「{pat}」: {e}"
    return (not hits), ("零命中" if not hits else f"{len(hits)} 处命中: " + " | ".join(hits[:3]))


def _load_frontmatter_patterns(member_id):
    """R4：从成员 frontmatter 读 forbidden_phrases（真源）——与 contract_enforce._load_frontmatter_forbidden 同构。
    返回 (patterns, error)。"""
    import os
    md = os.path.join(PKG, "agents", (member_id or "") + ".md")
    if not os.path.isfile(md):
        return [], f"agents/{member_id}.md 不存在"
    text = open(md, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return [], "无 frontmatter 块"
    fm_m = re.search(r"^forbidden_phrases:\s*\n((?:[ \t]+-[ \t]*.*\n?)+)", m.group(1), re.M)
    if not fm_m:
        return [], "frontmatter 无 forbidden_phrases"
    pats = []
    for line in fm_m.group(1).splitlines():
        item = re.match(r"^[ \t]+-[ \t]*(.+?)\s*$", line)
        if item:
            pats.append(item.group(1))
    return pats, None


def check_required_regex(exp, task_text, run_dir, files, a):
    mid = exp.get("target_member")
    # any_member 模式（2026-11-08 C01 A6 清偿）：成员多轮产出（如 scout A01 首轮 + A03 复检）
    # 同目录并存时，member_files 只保留最后一个文件——首轮专有段落（客体预审/法25）会被复检
    # 报告覆盖而误判缺失。any_member=true 时扫该成员全部落盘产出，任一命中即过。
    if a.get("any_member"):
        pats = a["patterns"]
        # 直接从 run_dir glob 该成员全部落盘产出（files dict 会被同名成员多轮文件覆盖，不可靠）
        cand = sorted(glob.glob(os.path.join(run_dir, f"T-*__{mid}.md")))
        if not cand:
            return False, f"any_member 模式：run_dir 内无 {mid} 落盘产出"
        missing = [pat for pat in pats
                   if not any(re.search(pat, read(p)) for p in cand)]
        return (not missing), ("全部命中（any_member 扫 %d 份产出）" % len(cand)
                               if not missing else f"缺: {missing}（扫 {len(cand)} 份该成员产出）")
    p = files.get(mid) or (list(files.values())[0] if files else None)
    if not p:
        return False, "无落盘文件"
    txt = read(p)
    missing = [pat for pat in a["patterns"] if not re.search(pat, txt)]
    return (not missing), ("全部命中" if not missing else f"缺: {missing}")


def check_min_chars(exp, task_text, run_dir, files, a):
    mid = exp.get("target_member")
    p = files.get(mid) or (list(files.values())[0] if files else None)
    if not p:
        return False, "无落盘文件"
    n = len(read(p))
    return n >= a["min"], f"{n} 字符（≥{a['min']}）"


def check_all_members_landed(exp, task_text, run_dir, files, a):
    missing = [m for m in a["expect"] if m not in files]
    return (not missing), ("6 成员全部落盘" if not missing else f"缺落盘: {missing}")


def check_gates(exp, task_text, run_dir, files, a):
    """G1-G5 门禁登记核验（v2.6.0 修 S-Q4 断言锚点）。

    登记位置两处任一即可：
      1. state.json 的 gates 键（Batch2 起标准路径）
      2. _VERIFY.md 文本——旧版只查字面 "G1"，但 A01 实际用语义表述（"红→黄放行"等），
         已知假阴性；现改为：字面 Gn 或 state gates 键名 或 语义关键词（三轮查新/裁决/条件/缺口/摘要字符）任一命中
    """
    # 1) state.json 路径（权威）
    # CYCLE-1 · S-E01：改为按 GATE_ALIASES 精确读取，取消「按 dict 插入序取前 N 值」的
    # 脆弱映射（实测键名漂移时前5值=[false×4,true] → 必然假阴性，且回归基线无 state.json
    # 导致该路径零覆盖）。别名表唯一真源 = state_store.GATE_ALIASES。
    sp = os.path.join(run_dir, "state.json")
    if os.path.isfile(sp):
        try:
            import state_store as SS
            state = json.load(open(sp, encoding="utf-8"))
            gkeys = state.get("gates") or {}
            if gkeys:
                missing = [g for g in a["expect"]
                           if not gkeys.get(SS.GATE_ALIASES.get(g, g))]
                return (not missing), ("state.json 门禁全关（别名精确读取）" if not missing
                                       else f"state 未关: {missing}")
        except Exception as e:  # noqa
            return False, f"state.json 门禁读取失败: {e}"
    # 2) _VERIFY.md 文本路径
    vf = os.path.join(run_dir, "_VERIFY.md")
    txt = read(vf)
    if not txt:
        return False, "_VERIFY.md 不存在（主理人未汇编门禁校验）"
    semantic = {
        "G1": r"G1|三轮|search_rounds|查新.*?(完成|轮)",
        "G2": r"G2|裁决|黄|绿|红|二审|附条件",
        "G3": r"G3|C1-C8|C1－C8|确认清单|逐项确认|C 表|已确认|K表.*?兑现|M1-M\d+兑现",
        "G4": r"G4|缺口",
        "G5": r"G5|摘要.*?\d+\s*字符|禁用词",
    }
    missing = []
    for g in a["expect"]:
        pat = semantic.get(g, re.escape(g))
        if not re.search(pat, txt):
            missing.append(g)
    return (not missing), ("G1-G5 全登记（语义匹配）" if not missing else f"缺: {missing}")


def check_abstract_max_chars(exp, task_text, run_dir, files, a):
    for mid in ("patent-attorney-writer",):
        if mid in files:
            txt = read(files[mid])
            # 优先"摘要正文"粗体段（A07 实际结构：## 三、说明书摘要 下有 **摘要正文**：）
            bm = re.search(r"\*\*摘要正文\*\*[:：]?\s*\n+(.*?)(?=\n\s*\*\*(?:摘要附图|机械验证|结论|自查))", txt, re.S)
            if bm:
                sec = bm.group(1)
            else:
                sec = extract_section(txt, ["说明书摘要", "摘要"])
                if sec is None:
                    return False, "未找到「说明书摘要」段"
                sec = re.sub(r"^[\s>|\-]+", "", sec.strip(), flags=re.M).strip()
            n = len(sec.strip())
            return n <= a["max"], f"摘要 {n} 字符（≤{a['max']}）"
    return False, "未找到撰写员落盘文件"


def check_budget(exp, task_text, run_dir, files, a):
    ml = os.path.join(run_dir, "metrics.jsonl")
    if not os.path.isfile(ml):
        return None, "metrics.jsonl 不存在（未计量，跳过）"
    latest, wall_sum, wall_max = {}, 0, 0
    for line in open(ml, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:  # noqa
            continue
        key = (d.get("task_id"), d.get("member"))
        latest[key] = d
    for d in latest.values():
        w = d.get("duration_ms_wall") or 0
        wall_sum += w
        wall_max = max(wall_max, w)
    tokens = sum(d.get("out_tokens_est") or 0 for d in latest.values())
    # 口径（2026-10-15 修正）：SOP 为串行链，链式墙钟 ≈ 各成员墙钟之和（下界；不含主理人编排开销）。
    # 原实现取 max() 会严重低估全流程耗时。
    wall_min = round(wall_sum / 60000, 1) if wall_sum else None
    ok = tokens <= a["max_tokens"] and (wall_min is None or wall_min <= a["max_wall_min"])
    detail = f"tokens≈{tokens}（≤{a['max_tokens']}）"
    if wall_min is not None:
        detail += f" · 链式墙钟≈{wall_min}min（Σ成员墙钟·下界，≤{a['max_wall_min']}）"
    return ok, detail


def check_no_fabrication_marker(exp, task_text, run_dir, files, a):
    """信息性：统计「矩阵无推荐」等诚实降级标记出现次数——不判失败"""
    n = 0
    for p in files.values():
        n += len(re.findall("|".join(a.get("forbidden", [])), read(p)))
    return None, f"INFORMATIONAL：诚实降级标记 {n} 处（{a.get('note','')}）"


def check_conditions_closed(exp, task_text, run_dir, files, a):
    """J2（v2.6.0 Batch3）：二审条件清单兑现对账。

    数据源（二选一，state.json 优先）：
      1. state.json 的 conditions 键值（Batch2 起主理人 VERIFY 后登记）
      2. 回退：从二审产出文件提取条件编号（K1..K9/M1..M9），扫描下游产出（architect/writer）
         是否逐条命中——机械底线
    INFO 语义：任一条件未检出兑现 → FAIL（阻断交付汇编），除非 --json 报告标注 warn_only
    """
    # 1) state.json 路径
    sp = os.path.join(run_dir, "state.json")
    conds = {}
    if os.path.isfile(sp):
        try:
            state = json.load(open(sp, encoding="utf-8"))
            conds = state.get("conditions") or {}
        except Exception:  # noqa
            pass
    if conds:
        open_conds = [k for k, v in conds.items() if not v]
        return (not open_conds), (
            f"state.json 条对账：{len(conds)} 条，未关闭 {open_conds or '无'}")
    # 2) 回退：从二审产出提取条件编号
    reviewer_file = files.get("second-opinion-reviewer")
    if not reviewer_file:
        return None, "无二审落盘，跳过条件对账"
    rtxt = read(reviewer_file)
    cond_ids = sorted(set(re.findall(r"\b([KM]\d{1,2})\b", rtxt)))
    if not cond_ids:
        return None, "二审产出未检出条件编号（K*/M*），跳过"
    downstream = "".join(read(files[m]) for m in ("disclosure-architect", "patent-attorney-writer")
                         if m in files)
    if not downstream:
        return None, "无下游产出可扫，跳过"
    missing = [c for c in cond_ids if c not in downstream]
    return (not missing), (
        f"条件对账（回退·文本扫描）：二审 {len(cond_ids)} 条，下游未提及 {missing or '无'}")


CHECKERS = {
    "task_package_elements": check_task_package_elements,
    "envelope_required_fields": check_envelope_required_fields,
    "envelope_agent_id": check_envelope_agent_id,
    "min_count": check_min_count,
    "forbidden_regex": check_forbidden_regex,
    "required_regex": check_required_regex,
    "min_chars": check_min_chars,
    "all_members_landed": check_all_members_landed,
    "gates": check_gates,
    "abstract_max_chars": check_abstract_max_chars,
    "budget": check_budget,
    "no_fabrication_marker": check_no_fabrication_marker,
    "conditions_closed": check_conditions_closed,
}


# ══════════════════ 命令 ══════════════════

def cmd_list():
    cases = list_cases()
    print(f"共 {len(cases)} 个回归用例（{CASES_DIR}）\n")
    print(f"{'case_id':18s} {'WF':3s} {'level':6s} {'target':24s} 断言数")
    print("-" * 72)
    for c in cases:
        print(f"{c['case_id']:18s} {c.get('workflow','?'):3s} {c.get('level','L1'):6s} "
              f"{c.get('target_member','?'):24s} {len(c.get('assertions',[]))}")
    return 0


def load_task_id_pattern():
    """从 result_envelope.schema.json 读取 task_id pattern（读不到时用保底字面量）。

    教训（2026-10-15 · failure-008）：scaffold 曾生成 'T-<date>-REG-B01'（第二个连字符），
    违反 schema 与 meter 的文件名契约 → 在此加自校验，防止再生违约 ID。"""
    fp = os.path.join(PKG, "skills", "agent-protocol", "result_envelope.schema.json")
    try:
        d = json.load(open(fp, encoding="utf-8"))
        return d["properties"]["task_id"]["pattern"]
    except Exception:  # noqa
        return r"^T-[0-9]{8}-[A-Za-z0-9]{1,8}$"


def cmd_scaffold(case_id, out_dir, task_id_override=None):
    exp, task_text, task_path = load_case(case_id)
    if exp is None:
        return 2
    out_dir = out_dir or os.path.join(PKG, "outputs", "regression-" + datetime.date.today().strftime("%Y%m%d"))
    os.makedirs(out_dir, exist_ok=True)
    date8 = datetime.date.today().strftime("%Y%m%d")
    if task_id_override:
        task_id = task_id_override
    else:
        # 合规 ID：workflow-b-01 → T-<date>-B01（字母数字后缀，与 schema 对齐；禁止第二个连字符）
        parts = [p for p in case_id.split("-") if p]
        suffix = (parts[-2].upper() + parts[-1]) if len(parts) >= 2 else parts[-1].upper()
        task_id = f"T-{date8}-{suffix}"
    # 自校验：违约即拒绝生成（fail fast，防 failure-008 复发）
    pat = load_task_id_pattern()
    if not re.match(pat, task_id):
        print(f"❌ task_id「{task_id}」不符合 envelope schema 约束 {pat}", file=sys.stderr)
        print("   提示：task_id 形如 T-YYYYMMDD-NNN 或 T-YYYYMMDD-B01（第三段仅字母数字，无连字符）", file=sys.stderr)
        return 2
    info = f"""# 回归运行 · {case_id}

- 用例：`tests/cases/{case_id}.task.md`（{exp.get('level','L1')} 级 · 目标 {exp.get('target_member')}）
- 建议任务 ID：`{task_id}`
- 运行目录：`{os.path.relpath(out_dir, PKG)}`

## 派单步骤（主理人执行）

1. 装配 spawn 文案：
   ```bash
   python3 scripts/assemble_spawn_prompt.py --member {exp.get('target_member') if exp.get('target_member')!='full-team' else '<成员>'} \\
     --phase 2 --task-id {task_id} --task-file tests/cases/{case_id}.task.md \\
     --run-dir {os.path.relpath(out_dir, PKG)} --check-task-package \\
     --out {os.path.relpath(out_dir, PKG)}/spawn.md
   ```
2. spawn 成员并等待落盘（产出写入 `{os.path.relpath(out_dir, PKG)}/`）
3. 计量：`python3 scripts/token_budget_check.py --meter {os.path.relpath(out_dir, PKG)} --ledger`
4. 验证：`python3 scripts/run_regression.py --case {case_id} --dir {os.path.relpath(out_dir, PKG)}`

## 断言清单

"""
    for a in exp.get("assertions", []):
        info += f"- [{a.get('id')}] {a.get('type')}：{json.dumps({k: v for k, v in a.items() if k not in ('id','type')}, ensure_ascii=False)}\n"
    # 恢复点段（v2.6.0 Batch2 · S-X3）：scaffold 同时初始化 state.json，断点续接有确定性入口
    members_for_state = ",".join(exp["expect"]) if exp.get("target_member") == "full-team" else exp.get("target_member", "")
    phase_hint = {"full-team": 0, "contradiction-analyst": 1, "patent-search-scout": 3}.get(exp.get("target_member"), 0)
    info += f"""
## 恢复点（断点续接 · v2.6.0）

- 状态文件：`state.json`（本目录，已随 scaffold 初始化）
- 中断恢复：`python3 scripts/state_store.py resume --run-dir {os.path.relpath(out_dir, PKG)}`
- 每次主理人 VERIFY 后更新：`python3 scripts/state_store.py update --run-dir {os.path.relpath(out_dir, PKG)} --set phase=N --set gates.GX=true`
- 追加轨迹自动写入 state.json 的 history[]，续接时按"最后更新 + 未关门禁 + 下一动作"三要素恢复

"""
    open(os.path.join(out_dir, "RUN_INFO.md"), "w", encoding="utf-8").write(info)
    # 初始化 state.json（失败不阻断 scaffold——state 是增强不是依赖）
    try:
        subprocess.run(
            [sys.executable, os.path.join(PKG, "scripts", "state_store.py"), "init",
             "--run-dir", out_dir, "--task-id", task_id, "--members", members_for_state],
            capture_output=True, text=True)
        subprocess.run(
            [sys.executable, os.path.join(PKG, "scripts", "state_store.py"), "update",
             "--run-dir", out_dir, "--set", f"phase={phase_hint}"],
            capture_output=True, text=True)
        print("   已初始化 state.json（恢复点就绪）")
    except Exception as e:  # noqa
        print(f"   ⚠ state.json 初始化失败（不阻断）：{e}")
    print(f"✅ 运行目录就绪：{out_dir}")
    print(f"   已写入 RUN_INFO.md（含派单步骤与断言清单）")
    print(f"   任务 ID 建议：{task_id}")
    return 0


def cmd_verify(case_id, run_dir, as_json):
    exp, task_text, _ = load_case(case_id)
    if exp is None:
        return 2
    if not os.path.isdir(run_dir):
        print(f"❌ 运行目录不存在：{run_dir}", file=sys.stderr)
        return 2
    files = member_files(run_dir)
    results = []
    for a in exp.get("assertions", []):
        fn = CHECKERS.get(a["type"])
        if fn is None:
            results.append({"id": a.get("id"), "pass": None, "detail": f"未实现的断言类型 {a['type']}"})
            continue
        ok, detail = fn(exp, task_text, run_dir, files, a)
        results.append({"id": a.get("id"), "type": a["type"], "pass": ok, "detail": detail})
    fails = [r for r in results if r["pass"] is False]
    info = [r for r in results if r["pass"] is None]
    passes = [r for r in results if r["pass"] is True]

    report = {
        "case_id": case_id, "run_dir": run_dir, "checked_at": datetime.datetime.now().isoformat(),
        "total": len(results), "passed": len(passes), "failed": len(fails), "info": len(info),
        "results": results, "verdict": "PASS" if not fails else "FAIL",
    }
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"═══ 回归验证 · {case_id} ═══")
        print(f"目录: {run_dir} | 成员落盘: {sorted(files.keys()) or '（无）'}")
        print()
        for r in results:
            icon = {True: "✅", False: "❌", None: "ℹ️"}[r["pass"]]
            print(f"  {icon} [{r['id']}] {r.get('type','')}: {r['detail']}")
        print()
        print(f"结果：{len(passes)}/{len(results)} PASS · {len(fails)} FAIL · {len(info)} INFO → {report['verdict']}")
    # 报告落盘（供归档）
    rp = os.path.join(run_dir, f"regression_report__{case_id}.json")
    try:
        json.dump(report, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if not as_json:
            print(f"报告: {os.path.relpath(rp, PKG)}")
    except Exception as e:  # noqa
        print(f"⚠️ 报告写入失败: {e}", file=sys.stderr)
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser(description="TRIZ 专家团回归测试集执行器（P2-9）")
    ap.add_argument("--list", action="store_true", help="列出全部用例")
    ap.add_argument("--case", help="用例 ID（如 workflow-b-01）")
    ap.add_argument("--scaffold", action="store_true", help="准备运行目录 + 打印派单指令")
    ap.add_argument("--dir", help="要对之验证的运行目录")
    ap.add_argument("--out", help="scaffold 输出目录（默认 outputs/regression-<date>）")
    ap.add_argument("--task-id", help="覆盖 scaffold 自动生成的 task_id（须符合 envelope schema）")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    if args.list:
        return cmd_list()
    if not args.case:
        ap.print_help()
        return 2
    if args.scaffold:
        return cmd_scaffold(args.case, args.out, args.task_id)
    if args.dir:
        return cmd_verify(args.case, args.dir, args.json)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
