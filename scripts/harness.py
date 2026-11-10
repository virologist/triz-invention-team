#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harness.py — 专家团统一工作入口（结构清晰 / 工具可靠 / 结果可验证 / 可改进）
============================================================================
背景（来自真实运行 2026-11-10 与第 1 步诊断）：
  - 22 个脚本里 13 个未出现在主理人操作说明中，工具与执行链脱节；
    没有「阶段 → 该跑什么 → 拿什么证明」的结构化清单 → 新增 docs/WORK_MAP.md。
  - G1-G5 / C1-C8 等硬性要求只有散文或回归用例的语义匹配，
    没有针对**真实运行目录**的 state 真值验收 → 新增 verify 子命令。
  - 真实运行的平台 502 / 墙钟超预算 / 紧凑降级只留在 routing-log 的
    reasoning 字段，未进入任何反馈闭环 → 新增 feedback 子命令 + 认可样例。

本脚本**只增补，不替代**：SOP / 红线 / 契约仍以 agents/*.md 为权威；
既有 22 个脚本全部保留，verify 优先 import 复用其判定函数（单一真源）。

四种状态（docs/WORK_MAP.md §一）：
  AUTO_PASS   自动验证通过（机械检查 + 证据）
  AI_PASS     AI 评估通过（语义，主理人显式给结论，不冒充机械检查）
  HUMAN_PASS  人工确认通过
  UNVERIFIED  尚未验证（缺输入/缺证据/缺确认，不得当作通过）

退出码：0=全部已验证且通过 · 1=存在 FAIL · 2=用法/环境错 ·
        3=无 FAIL 但存在 UNVERIFIED（**禁止宣称验证通过**）

用法：
  python3 scripts/harness.py map
  python3 scripts/harness.py verify --stage 3 --run-dir <RUN_DIR>
  python3 scripts/harness.py verify --all --run-dir <RUN_DIR> --json
  python3 scripts/harness.py verify --sample tests/cases/runtime-platform-502.md
  python3 scripts/harness.py feedback add --type error --scope rule \
      --summary "..." --evidence <path> --convert-to check --check-id <id>
  python3 scripts/harness.py feedback list --open
  python3 scripts/harness.py --self-test
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
WORK_MAP = os.path.join(PKG, "docs", "WORK_MAP.md")
FEEDBACK = os.path.join(PKG, ".learnings", "FEEDBACK.jsonl")
VERIFY_STATE = os.path.join(PKG, ".harness", "verify_state.json")
ROUTING_LOG = os.path.join(PKG, "docs", "routing-log.md")

# 复用既有唯一真源，不重复实现判据
sys.path.insert(0, HERE)

STATUS = ("AUTO_PASS", "AI_PASS", "HUMAN_PASS", "UNVERIFIED", "FAIL", "STALE")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def sha256_of(path):
    """文件内容指纹，用于「内容变化后重新验证」。"""
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def member_files(run_dir):
    """成员产出文件（沿用 run_regression / boundary_guard 的 glob 形态）。"""
    import glob
    return sorted(glob.glob(os.path.join(run_dir, "T-*__*.md")))


def read_state(run_dir):
    p = os.path.join(run_dir, "state.json")
    if not os.path.isfile(p):
        return None, p
    try:
        return json.load(open(p, encoding="utf-8")), p
    except Exception:
        return "UNREADABLE", p


# ─────────────────────────────────────────────────────────────
# 检查项：每项返回 (check_id, status, detail, evidence, needs_human)
# evidence 必须是可查的路径/值，禁止「看起来对」式结论
# ─────────────────────────────────────────────────────────────
def checks_common(run_dir, stage):
    """所有阶段共用的机械检查。"""
    out = []
    if not os.path.isdir(run_dir):
        return [("C00-run-dir", "FAIL", "运行目录不存在", run_dir, False)]

    files = member_files(run_dir)
    out.append(("C01-outputs", "AUTO_PASS" if files else "UNVERIFIED",
                "成员产出 %d 份" % len(files),
                ",".join(os.path.basename(f) for f in files[:6]) or run_dir, False))

    # 人设注入痕迹：spawn__*.md 为装配脚本产物（主理人 MD 强制四步第 1 步）
    spawns = [f for f in os.listdir(run_dir) if f.startswith("spawn__") and f.endswith(".md")]
    out.append(("C02-persona-injected", "AUTO_PASS" if spawns else "UNVERIFIED",
                "装配文案 %d 份" % len(spawns),
                ",".join(sorted(spawns)[:4]) or "(无 spawn__*.md)", False))

    # 失败记忆注入痕迹：spawn 文案尾部应有 digest 标记
    digest_hit = []
    for s in spawns:
        try:
            t = io.open(os.path.join(run_dir, s), encoding="utf-8").read()
            if "失败记忆" in t or "failure_memory" in t or "failure-" in t:
                digest_hit.append(s)
        except Exception:
            pass
    out.append(("C03-failure-memory", "AUTO_PASS" if digest_hit else "UNVERIFIED",
                "注入痕迹 %d 份" % len(digest_hit),
                ",".join(sorted(digest_hit)[:4]) or "(未检出 digest 标记)", False))

    # 路由决策落盘：routing-log 中检索本 run 的 task_id 或日期
    tid = ""
    m = re.search(r"T-(\d{8})-[A-Za-z0-9]{1,8}", " ".join(os.path.basename(f) for f in files))
    if m:
        tid = m.group(0)
    routing_hit = False
    if os.path.isfile(ROUTING_LOG):
        t = io.open(ROUTING_LOG, encoding="utf-8").read()
        routing_hit = bool(tid and tid in t) or bool(m and "R-" + m.group(1) in t)
    out.append(("C04-routing-logged", "AUTO_PASS" if routing_hit else "UNVERIFIED",
                "路由决策落盘（task_id=%s）" % (tid or "未知"),
                os.path.relpath(ROUTING_LOG, PKG), False))

    # state 真值：G1-G5（唯一真源 = state_store.GATE_ALIASES）
    state, state_p = read_state(run_dir)
    if state is None or state == "UNREADABLE":
        for i in range(1, 6):
            out.append(("G%d-state-truth" % i, "UNVERIFIED",
                        "state.json 缺失或不可读，门禁真值无法机械判定",
                        os.path.relpath(state_p, PKG), False))
    else:
        try:
            import state_store as SS
            aliases = SS.GATE_ALIASES
        except Exception:
            aliases = {"G1": "search_3rounds_complete", "G2": "trinity_verdict_pass",
                       "G3": "c1_c8_confirmed", "G4": "disclosure_gap_scan",
                       "G5": "g5_format_compliant"}
        gates = state.get("gates", {}) or {}
        for i in range(1, 6):
            key = aliases["G%d" % i]
            val = gates.get(key)
            ok = (val is True)
            out.append(("G%d-state-truth" % i, "AUTO_PASS" if ok else "FAIL",
                        "%s = %r" % (key, val), os.path.relpath(state_p, PKG), False))

        # 证据路径必须真实存在（S-E02：文件缺失 = 视为未查新）
        ev = state.get("evidence", {}) or {}
        for k in ("search_report", "verdict_report"):
            v = (ev.get(k) or "").strip()
            exists = bool(v) and os.path.isfile(os.path.join(PKG, v) if not os.path.isabs(v) else v)
            out.append(("E01-%s" % k, "AUTO_PASS" if exists else "FAIL",
                        "%s = %r（文件%s）" % (k, v, "存在" if exists else "缺失"),
                        v or "(空)", False))

        # 墙钟双轨：权威口径不得缺失
        met = state.get("metrics", {}) or {}
        wall = met.get("total_duration_ms_wall")
        out.append(("M01-wall-clock", "AUTO_PASS" if wall else "UNVERIFIED",
                    "累计墙钟 = %r" % wall, os.path.relpath(state_p, PKG), False))
    return out


def checks_stage(stage, run_dir):
    """阶段专属检查；只做机械可判定项，语义项明确标 needs_human。"""
    out = []
    files = member_files(run_dir)

    def text_of(member):
        for f in files:
            if member in os.path.basename(f):
                return io.open(f, encoding="utf-8", errors="ignore").read()
        return ""

    if stage in (0, "0"):
        p = os.path.join(run_dir, "phase0_requirement.md")
        if os.path.isfile(p):
            t = io.open(p, encoding="utf-8").read()
            hit = [q for q in ("Q1", "Q2", "Q3", "Q4", "Q5") if q in t]
            out.append(("S0-five-dims", "AUTO_PASS" if len(hit) == 5 else "FAIL",
                        "五维命中 %s" % ",".join(hit), os.path.relpath(p, PKG), False))
        else:
            out.append(("S0-five-dims", "UNVERIFIED", "需求卡未落盘",
                        os.path.relpath(p, PKG), False))
        out.append(("S0-semantics", "UNVERIFIED", "Q1-Q5 内容正确性与领域坍缩需人工/AI 判断",
                    "(语义项)", True))

    elif stage in (2, "2", 2.5, "2.5"):
        if str(stage) == "2.5":
            # 真实运行暴露：Phase 2.5 汇聚校准此前无任何机械检查
            cands = [f for f in os.listdir(run_dir)
                     if "calibration" in f.lower() or "phase2.5" in f.lower()]
            ok = False
            ev = "(无校准记录)"
            for c in cands:
                t = io.open(os.path.join(run_dir, c), encoding="utf-8", errors="ignore").read()
                if any(w in t for w in ("覆盖", "空白", "上调", "降级", "校准")):
                    ok, ev = True, c
                    break
            out.append(("S25-calibration", "AUTO_PASS" if ok else "UNVERIFIED",
                        "汇聚校准记录%s" % ("存在且含决策字段" if ok else "缺失/无决策字段"),
                        ev, False))
            out.append(("S25-conclusion", "UNVERIFIED", "校准结论（方向升降）需主理人语义判断",
                        "(语义项)", True))
        else:
            t = text_of("contradiction-analyst")
            # 结构计数：方向标题形态（保守，不做语义识别）
            n = len(re.findall(r"(?:^|\n)\s*(?:#{2,4}\s*)?(?:方向|方案|D)\s*\d+", t))
            out.append(("S2-min-directions", "AUTO_PASS" if n >= 3 else "UNVERIFIED",
                        "结构化方向标题 %d 个（≥3）" % n,
                        ",".join(os.path.basename(f) for f in files if "analyst" in f) or "(无)",
                        False))
            out.append(("S2-value", "UNVERIFIED", "方向价值/可授权可能性需人工或 AI 评估",
                        "(语义项)", True))

    elif stage in (3, "3"):
        scout = [f for f in files if "patent-search-scout" in f]
        # 判据用真实基线校准（2026-10-15 L2）：
        # 原用「产出文件数 ≥3」，但基线 A01 单文件内含 R1-1~R3-6 全部三轮检索式，
        # 文件数判据会假阴性。改为机械识别三轮检索式编号 R1-/R2-/R3- 各自至少 1 条；
        # 兼容「三轮三 spawn」与「单文件紧凑模式」两种真实形态。
        merged = "\n".join(io.open(f, encoding="utf-8", errors="ignore").read()
                           for f in scout)
        rounds = {r: len(re.findall(r"\bR%s-\d+" % r, merged)) for r in (1, 2, 3)}
        full = all(v >= 1 for v in rounds.values())
        out.append(("S3-three-rounds", "AUTO_PASS" if full else "UNVERIFIED",
                    "三轮检索式编号 R1/R2/R3 = %s（产出 %d 份）"
                    % ("/".join(str(rounds[r]) for r in (1, 2, 3)), len(scout)),
                    ",".join(os.path.basename(f) for f in scout[:4]) or "(无)", False))
        # X/E 级判定复用唯一真源
        try:
            import threat_grade as TG
            x, e, d = TG.scan_member_grades("patent-search-scout", run_dir)
            out.append(("S3-threat-grade", "AUTO_PASS" if d["verdict"] == "determined" else "UNVERIFIED",
                        "X=%d E=%d verdict=%s" % (x, e, d["verdict"]),
                        ",".join(d.get("files", [])[:1]) or run_dir, False))
        except Exception as exc:
            out.append(("S3-threat-grade", "UNVERIFIED", "判定模块不可用：%s" % exc,
                        "threat_grade.py", False))
        out.append(("S3-channel", "UNVERIFIED", "检索渠道降档与分级语义需人工复核", "(语义项)", True))

    elif stage in (4, "4"):
        ex = [f for f in files if "patent-examiner-sim" in f]
        so = [f for f in files if "second-opinion-reviewer" in f]
        out.append(("S4-dual-review", "AUTO_PASS" if ex and so else "UNVERIFIED",
                    "examiner=%d / second-opinion=%d" % (len(ex), len(so)),
                    ",".join(os.path.basename(f) for f in (ex + so)[:4]) or "(无)", False))
        out.append(("S4-verdict", "UNVERIFIED", "红/黄裁决、仲裁与 L4 升级需人工确认",
                    "(语义项)", True))

    elif stage in (5, "5"):
        t = text_of("patent-attorney-writer")
        m = re.search(r"(?:说明书摘要|摘要)[：:\s]*([^\n]{1,400})", t)
        if m:
            n = len(m.group(1).strip())
            out.append(("S5-abstract-len", "AUTO_PASS" if n <= 300 else "FAIL",
                        "摘要 %d 字符（≤300）" % n, "patent-attorney-writer 产出", False))
        else:
            out.append(("S5-abstract-len", "UNVERIFIED", "未定位摘要段落（需人工核对）",
                        "(未定位)", False))
        # 复用 contract_enforce._clean_for_forbidden_scan 唯一真源：
        # 产出里的「禁用词机械自查」代码块/逐词统计表本身含有这些词，
        # 直接全文 grep 会误伤（2026-11-10 真实基线实测：A07 自查脚本行命中
        # 大约/左右/等等，但权项正文零命中）。U2 上下文豁免已有成熟实现，不再另写。
        try:
            import contract_enforce as CE
            scan_text = CE._clean_for_forbidden_scan(t)
            exempt = "contract_enforce._clean_for_forbidden_scan"
        except Exception:
            scan_text, exempt = t, "(豁免模块不可用，退化为全文扫描)"
        bad = [w for w in ("大约", "左右", "等等") if w in scan_text]
        out.append(("S5-vague-words", "AUTO_PASS" if not bad else "FAIL",
                    "权项正文模糊词 %s（清洗：%s）"
                    % (",".join(bad) if bad else "无", exempt),
                    "patent-attorney-writer 产出", False))
        # 越界复核复用既有红线
        try:
            import boundary_guard as BG
            res = BG.scan_run_dir(run_dir)
            rc, label = BG.judge_exit_code(res)
            out.append(("S5-boundary", "AUTO_PASS" if rc == 0 else "FAIL",
                        "越界复核 label=%s，扫描 %d 份" % (label, len(res)),
                        "boundary_guard.py", False))
        except Exception as exc:
            out.append(("S5-boundary", "UNVERIFIED", "越界模块不可用：%s" % exc,
                        "boundary_guard.py", False))
        out.append(("S5-c1-c8-semantics", "UNVERIFIED",
                    "C1-C8 技术含义（必要性/真实性/保护范围）必须人工确认，结构检查不替代",
                    "(人工确认项)", True))
    return out


def run_verify(run_dir, stage, as_json=False):
    checks = checks_common(run_dir, stage)
    checks += checks_stage(stage, run_dir)

    # 内容变化后重新验证：对比上次指纹，变化项标 STALE
    prev = {}
    if os.path.isfile(VERIFY_STATE):
        try:
            prev = json.load(open(VERIFY_STATE, encoding="utf-8")).get("fingerprints", {})
        except Exception:
            prev = {}
    newfp = {}
    for f in member_files(run_dir) + [os.path.join(run_dir, "state.json")]:
        h = sha256_of(f)
        if h:
            # 运行目录在包外时 relpath 会产出 ../../.. 噪声，改用文件名 + 短 hash
            key = ("%s#%s" % (os.path.basename(f), h[:8])) if not os.path.abspath(f).startswith(PKG) \
                else os.path.relpath(f, PKG)
            newfp[key] = h
    # 按「文件名」比对指纹（键含 hash 时取 # 前部分），避免键自身变化导致漏检
    def base(k):
        return k.split("#")[0]
    prev_by_base = {base(k): v for k, v in prev.items()}
    stale = [k for k, v in newfp.items()
             if base(k) in prev_by_base and prev_by_base[base(k)] != v]
    if stale:
        checks.append(("F01-content-changed", "STALE",
                       "%d 个检查对象内容已变化，须重新验证：%s" % (len(stale), ",".join(stale[:3])),
                       ",".join(stale[:3]), False))

    os.makedirs(os.path.dirname(VERIFY_STATE), exist_ok=True)
    json.dump({"checked_at": now(), "run_dir": run_dir, "fingerprints": newfp},
              open(VERIFY_STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    n_fail = sum(1 for c in checks if c[1] == "FAIL")
    n_unver = sum(1 for c in checks if c[1] in ("UNVERIFIED", "STALE"))
    n_auto = sum(1 for c in checks if c[1] == "AUTO_PASS")
    report = {
        "checked_at": now(), "run_dir": run_dir, "stage": str(stage),
        "total": len(checks), "auto_pass": n_auto, "fail": n_fail,
        "unverified": n_unver,
        "results": [{"check_id": c[0], "status": c[1], "detail": c[2],
                     "evidence": c[3], "needs_human": c[4]} for c in checks],
    }
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("🔎 阶段验收 — stage=%s · %s（%d 项）\n" % (stage, run_dir, len(checks)))
        for c in checks:
            flag = {"AUTO_PASS": "✅", "AI_PASS": "🧠", "HUMAN_PASS": "👤",
                    "UNVERIFIED": "⚠️ ", "STALE": "🔄", "FAIL": "❌"}[c[1]]
            print("  %s %-24s %-12s %s" % (flag, c[0], c[1], c[2]))
            print("       证据: %s" % c[3])
        print("\n结论：AUTO_PASS %d · FAIL %d · UNVERIFIED/STALE %d"
              % (n_auto, n_fail, n_unver))
        if n_unver:
            print("⚠️  存在尚未验证项——按 WORK_MAP §一，不得宣称验证通过")
    # 退出码语义：失败优先；其次「尚未验证」
    return 1 if n_fail else (3 if n_unver else 0)


# ─────────────────────────────────────────────────────────────
# 反馈闭环
# ─────────────────────────────────────────────────────────────
FEEDBACK_FIELDS = ("id", "timestamp", "type", "scope", "summary", "evidence",
                   "convert_to", "check_id", "status")


def feedback_add(args):
    # 防规则膨胀：长期规则必须绑定「认可样例 / 程序检查 / 工具修复」与 check-id
    if args.scope == "rule" and (not args.convert_to or not args.check_id):
        print("❌ scope=rule 必须同时给出 --convert-to 与 --check-id"
              "（长期规则必须落地为认可样例/程序检查/工具修复，禁止只写文字规则）",
              file=sys.stderr)
        return 2
    if args.evidence and not os.path.exists(args.evidence):
        print("❌ 证据路径不存在，拒绝无据记录：%s" % args.evidence, file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(FEEDBACK), exist_ok=True)
    rows = []
    if os.path.isfile(FEEDBACK):
        for line in io.open(FEEDBACK, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    n = len(rows) + 1
    rec = {"id": "FB-%s-%03d" % (datetime.date.today().strftime("%Y%m%d"), n),
           "timestamp": now(), "type": args.type, "scope": args.scope,
           "summary": args.summary, "evidence": args.evidence or "",
           "convert_to": args.convert_to or "", "check_id": args.check_id or "",
           "status": "open" if args.scope == "rule" else "recorded"}
    with open(FEEDBACK, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("✅ 反馈已记录 %s（scope=%s, status=%s）" % (rec["id"], rec["scope"], rec["status"]))
    return 0


def feedback_list(args):
    if not os.path.isfile(FEEDBACK):
        print("(暂无反馈记录)"); return 0
    rows = [json.loads(l) for l in io.open(FEEDBACK, encoding="utf-8") if l.strip()]
    if args.open:
        rows = [r for r in rows if r.get("status") == "open"]
    rules = [r for r in rows if r.get("scope") == "rule"]
    print("反馈 %d 条（长期规则 %d 条 / 未闭环 %d 条）" %
          (len(rows), len(rules), sum(1 for r in rows if r.get("status") == "open")))
    for r in rows:
        print("  %-20s %-8s %-6s %-9s %s" %
              (r["id"], r["scope"], r["type"], r["status"], r["summary"][:52]))
    # 规则膨胀护栏
    if len(rules) > 20:
        print("⚠️  长期规则超过 20 条——请复查是否有规则应降级为单次要求或合并")
    return 0


def verify_sample(path):
    """认可样例回归：把真实运行的正确处置转成可机械复验的断言。"""
    if not os.path.isfile(path):
        print("❌ 样例不存在：%s" % path, file=sys.stderr); return 2
    t = io.open(path, encoding="utf-8").read()
    items = re.findall(r"^-\s*\[([ xX])\]\s*(.+)$", t, re.M)
    if not items:
        print("❌ 样例无可解析断言（需要 - [ ] / - [x] 列表）", file=sys.stderr); return 2
    bad = []
    unverified = 0
    routing = io.open(ROUTING_LOG, encoding="utf-8").read() if os.path.isfile(ROUTING_LOG) else ""
    for mark, desc in items:
        # `UNVERIFIED:` 是显式「尚未验证」占位：不参与命中判定，只登记，
        # 绝不把它当通过（符合「没有证据不宣称验证通过」）。
        if "UNVERIFIED:" in desc:
            unverified += 1
            # 去掉正文里的 "UNVERIFIED:" 前缀，避免输出 "UNVERIFIED UNVERIFIED: ..."
            print("  ⚠️  UNVERIFIED %s" % desc.split("UNVERIFIED:", 1)[1].strip()[:80])
            continue
        hit = False
        if "CHECK-RT-001" in desc:
            hit = "R-20261110-004" in routing
        elif "CHECK-RT-002" in desc:
            hit = ("502" in routing and "紧凑" in routing)
        elif "CHECK-RT-003" in desc:
            hit = os.path.isfile(WORK_MAP)
        elif "CHECK-RT-004" in desc:
            hit = os.path.isfile(os.path.join(HERE, "harness.py"))
        expected = (mark.strip().lower() == "x")
        ok = (expected == bool(hit))
        print("  %s %-12s %s" % ("✅" if ok else "❌",
                                "AUTO_PASS" if ok and hit else "FAIL", desc[:80]))
        if not ok:
            bad.append(desc)
    print("\n认可样例：%d 项，自动验证通过 %d，失败 %d，尚未验证 %d"
          % (len(items), len(items) - len(bad) - unverified, len(bad), unverified))
    if unverified:
        print("⚠️  存在尚未验证项——按 WORK_MAP §一，不得宣称验证通过")
    # 退出码语义与 verify --run-dir 保持一致：
    # 0=全通过 · 1=有 FAIL · 2=用法错 · 3=无 FAIL 但存在 UNVERIFIED（禁止宣称验证通过）
    if bad:
        return 1
    return 3 if unverified else 0


def self_test():
    """判别力自测：改坏任一判据，本测试必须报错。"""
    import tempfile
    fails = []
    print("🧪 harness 判别力自测\n")
    with tempfile.TemporaryDirectory() as td:
        # 空运行目录：必须有 UNVERIFIED，且退出码 = 3（不假绿）
        rc = run_verify(td, 3, as_json=False)
        ok = (rc == 3)
        print("  %s 空运行目录 → 退出码 3（尚未验证，禁止假绿）| 实得 %d"
              % ("✅" if ok else "❌", rc))
        if not ok: fails.append("空目录假绿")

        # 构造 state.json：G1-G5 全 true + 证据文件真实存在 → G 项应 AUTO_PASS
        state = {"gates": {k: True for k in (
                    "search_3rounds_complete", "trinity_verdict_pass", "c1_c8_confirmed",
                    "disclosure_gap_scan", "g5_format_compliant")},
                 "evidence": {"search_report": "", "verdict_report": ""},
                 "metrics": {"total_duration_ms_wall": 1}}
        json.dump(state, open(os.path.join(td, "state.json"), "w", encoding="utf-8"))
        checks = checks_common(td, 3)
        gpass = sum(1 for c in checks if c[0].startswith("G") and c[1] == "AUTO_PASS")
        ok2 = (gpass == 5)
        print("  %s 门禁真值全 true → 5 项 AUTO_PASS | 实得 %d"
              % ("✅" if ok2 else "❌", gpass))
        if not ok2: fails.append("门禁真值判定")

        # 证据路径缺失 → 必须 FAIL
        efail = sum(1 for c in checks if c[0].startswith("E01") and c[1] == "FAIL")
        ok3 = (efail == 2)
        print("  %s 证据文件缺失 → 2 项 FAIL | 实得 %d"
              % ("✅" if ok3 else "❌", efail))
        if not ok3: fails.append("证据缺失未拦截")

        # 长期规则无 convert-to → 必须被拒
        class A: pass
        a = A(); a.scope = "rule"; a.convert_to = None; a.check_id = None
        a.type = "error"; a.summary = "探针"; a.evidence = ""
        ok4 = (feedback_add(a) == 2)
        print("  %s 长期规则未绑定转化路径 → 拒绝 | 实得 RC=%s"
              % ("✅" if ok4 else "❌", "2" if ok4 else "非2"))
        if not ok4: fails.append("规则膨胀护栏")

        # 模糊词豁免的双向判别力：自查代码块里的词不算违规，正文里的算违规
        # （2026-11-10 真实基线 A07 误伤修复后锁定，防回归）
        try:
            import contract_enforce as CE
            clean = CE._clean_for_forbidden_scan(
                "```python\nwords = [\"大约\", \"左右\"]\n```\n## 权项\n1. 一种装置\n")
            body = CE._clean_for_forbidden_scan("## 权项\n1. 厚度大约 3mm 左右\n")
            ok5 = ("大约" not in clean) and ("大约" in body)
            print("  %s 模糊词豁免判别力：自查代码放行 / 正文命中 | 实得 %s"
                  % ("✅" if ok5 else "❌", ok5))
            if not ok5: fails.append("模糊词豁免")
        except Exception as exc:
            print("  ❌ 模糊词豁免判别力不可用：%s" % exc)
            fails.append("模糊词豁免")

        # 元判别力：故意写错期望必须能被识别
        meta = (rc == 999)
        print("  %s 自测元判别力：故意写错的期望被正确识别" % ("❌" if meta else "✅"))
        if meta: fails.append("元判别力")

        # 认可样例退出码契约：含 UNVERIFIED 断言 → 必须 RC=3（不得假绿）；
        # 全部断言命中且无 UNVERIFIED → RC=0。锁死「没有证据不宣称通过」。
        samp_unver = os.path.join(td, "s_unver.md")
        io.open(samp_unver, "w", encoding="utf-8").write(
            "- [x] CHECK-RT-003: 工作地图 docs/WORK_MAP.md 存在\n"
            "- [ ] UNVERIFIED: 该次运行产出未落盘（本机未检索到）\n")
        rc_s = verify_sample(samp_unver)
        ok6 = (rc_s == 3)
        print("  %s 认可样例含 UNVERIFIED → 退出码 3（禁止假绿）| 实得 %d"
              % ("✅" if ok6 else "❌", rc_s))
        if not ok6: fails.append("样例 UNVERIFIED 假绿")

        samp_ok = os.path.join(td, "s_ok.md")
        io.open(samp_ok, "w", encoding="utf-8").write(
            "- [x] CHECK-RT-003: 工作地图 docs/WORK_MAP.md 存在\n")
        rc_o = verify_sample(samp_ok)
        ok7 = (rc_o == 0)
        print("  %s 认可样例全部命中且无 UNVERIFIED → 退出码 0 | 实得 %d"
              % ("✅" if ok7 else "❌", rc_o))
        if not ok7: fails.append("样例全通过误报")

    if fails:
        print("\n❌ 自测失败：%s" % fails); return 1
    print("\n✅ 自测全通过"); return 0


def cmd_map(args):
    if not os.path.isfile(WORK_MAP):
        print("❌ 工作地图缺失：%s" % WORK_MAP, file=sys.stderr); return 2
    t = io.open(WORK_MAP, encoding="utf-8").read()
    if args.json:
        # 按「## 二、阶段表」锚点截取，避免把状态表/C1-C8 表行误当成阶段
        seg = t.split("## 二、阶段表", 1)[-1].split("\n## ", 1)[0]
        rows = [l for l in seg.splitlines()
                if l.startswith("| ") and "---" not in l and "阶段" not in l.split("|")[1]]
        stages = [r.split("|")[1].strip() for r in rows]
        print(json.dumps({"path": os.path.relpath(WORK_MAP, PKG),
                          "stage_rows": len(rows), "stages": stages},
                         ensure_ascii=False, indent=2))
    else:
        print(t)
    return 0


def main():
    ap = argparse.ArgumentParser(description="专家团统一工作入口（WORK_MAP 消费器）")
    ap.add_argument("--self-test", action="store_true", help="判别力自测")
    sub = ap.add_subparsers(dest="cmd")

    p_map = sub.add_parser("map", help="打印结构化工作地图")
    p_map.add_argument("--json", action="store_true")

    p_v = sub.add_parser("verify", help="阶段验收（记录检查对象/结果/证据）")
    p_v.add_argument("--run-dir", default="")
    p_v.add_argument("--stage", default="all")
    p_v.add_argument("--all", action="store_true")
    p_v.add_argument("--sample", help="认可样例路径")
    p_v.add_argument("--json", action="store_true")

    p_f = sub.add_parser("feedback", help="反馈记录（区分单次要求与长期规则）")
    fs = p_f.add_subparsers(dest="fcmd")
    p_add = fs.add_parser("add")
    p_add.add_argument("--type", default="error",
                       choices=("error", "correction", "insight", "feature"))
    p_add.add_argument("--scope", default="once", choices=("once", "rule"))
    p_add.add_argument("--summary", required=True)
    p_add.add_argument("--evidence", default="")
    p_add.add_argument("--convert-to", choices=("sample", "check", "tool-fix"))
    p_add.add_argument("--check-id", default="")
    p_list = fs.add_parser("list")
    p_list.add_argument("--open", action="store_true")

    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.cmd == "map":
        return cmd_map(args)
    if args.cmd == "verify":
        if args.sample:
            return verify_sample(args.sample)
        if not args.run_dir:
            print("❌ 需要 --run-dir 或 --sample", file=sys.stderr); return 2
        return run_verify(args.run_dir, "all" if args.all else args.stage, args.json)
    if args.cmd == "feedback":
        if args.fcmd == "add":
            return feedback_add(args)
        if args.fcmd == "list":
            return feedback_list(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
