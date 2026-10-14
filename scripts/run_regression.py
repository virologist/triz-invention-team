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
  python3 scripts/run_regression.py --case workflow-b-01 --dir outputs/regression-20261015
  python3 scripts/run_regression.py --case workflow-b-01 --dir <dir> --json

退出码：0=全部断言通过（INFO 不影响）  1=存在 FAIL  2=用法/环境错误
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

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
    txt_use = strip_selfcheck_lines(strip_fences(txt_use))
    hits = []
    for pat in a["patterns"]:
        for m in re.finditer(pat, txt_use):
            s = max(0, m.start() - 10)
            hits.append(f"「{pat}」@…{txt_use[s:m.end() + 10]}…")
    return (not hits), ("零命中" if not hits else f"{len(hits)} 处命中: " + " | ".join(hits[:3]))


def check_required_regex(exp, task_text, run_dir, files, a):
    mid = exp.get("target_member")
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
    vf = os.path.join(run_dir, "_VERIFY.md")
    txt = read(vf)
    if not txt:
        return False, "_VERIFY.md 不存在（主理人未汇编门禁校验）"
    missing = [g for g in a["expect"] if not re.search(re.escape(g), txt)]
    return (not missing), ("G1-G5 全登记" if not missing else f"缺: {missing}")


def check_abstract_max_chars(exp, task_text, run_dir, files, a):
    for mid in ("patent-attorney-writer",):
        if mid in files:
            txt = read(files[mid])
            sec = extract_section(txt, ["说明书摘要", "摘要"])
            if sec is None:
                return False, "未找到「说明书摘要」段"
            sec = re.sub(r"^[\s>|\-]+", "", sec.strip(), flags=re.M).strip()
            n = len(sec)
            return n <= a["max"], f"摘要 {n} 字符（≤{a['max']}）"
    return False, "未找到撰写员落盘文件"


def check_budget(exp, task_text, run_dir, files, a):
    ml = os.path.join(run_dir, "metrics.jsonl")
    if not os.path.isfile(ml):
        return None, "metrics.jsonl 不存在（未计量，跳过）"
    latest, wall_max = {}, 0
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
        w = d.get("duration_ms_wall") or 0
        wall_max = max(wall_max, w)
    tokens = sum(d.get("out_tokens_est") or 0 for d in latest.values())
    wall_min = round(wall_max / 60000, 1) if wall_max else None
    ok = tokens <= a["max_tokens"] and (wall_min is None or wall_min <= a["max_wall_min"])
    detail = f"tokens≈{tokens}（≤{a['max_tokens']}）"
    if wall_min is not None:
        detail += f" · 墙钟≈{wall_min}min（≤{a['max_wall_min']}）"
    return ok, detail


def check_no_fabrication_marker(exp, task_text, run_dir, files, a):
    """信息性：统计「矩阵无推荐」等诚实降级标记出现次数——不判失败"""
    n = 0
    for p in files.values():
        n += len(re.findall("|".join(a.get("forbidden", [])), read(p)))
    return None, f"INFORMATIONAL：诚实降级标记 {n} 处（{a.get('note','')}）"


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


def cmd_scaffold(case_id, out_dir):
    exp, task_text, task_path = load_case(case_id)
    if exp is None:
        return 2
    out_dir = out_dir or os.path.join(PKG, "outputs", "regression-" + datetime.date.today().strftime("%Y%m%d"))
    os.makedirs(out_dir, exist_ok=True)
    date8 = datetime.date.today().strftime("%Y%m%d")
    task_id = f"T-{date8}-REG-{case_id.split('-')[-2].upper()}{case_id.split('-')[-1]}"
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
    open(os.path.join(out_dir, "RUN_INFO.md"), "w", encoding="utf-8").write(info)
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
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    if args.list:
        return cmd_list()
    if not args.case:
        ap.print_help()
        return 2
    if args.scaffold:
        return cmd_scaffold(args.case, args.out)
    if args.dir:
        return cmd_verify(args.case, args.dir, args.json)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
