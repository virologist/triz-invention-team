#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
boundary_guard.py — 成员产出**越界红线**机械拦截（CYCLE-1 · S-E59）
=====================================================================
问题（S-E11 未解决完的半截）：`forbidden_boundary` 已下沉到
`task_payload.schema.json`（下行任务契约），`docs/architecture.md` §二 角色矩阵
也逐成员写明「禁止边界」—— 但**运行时零机械校验**：
  - 边界只写在文档里，靠主理人自觉核对（S-E11 想解决但只解决了下发，没解决验收）
  - 任何成员产出申请文件正文 / 越权出具裁决 / 自我评价，**没有任何脚本会报错**

本脚本补上验收侧：扫描成员落盘产出，按**角色**判定是否越界。

判定原则（原则②机械计量优先于自报 / 原则①散文条款必须脚本化）：
  - 判据基于**产出结构**（章节标题 / 权项编号 / 裁决字段），不基于成员自述
  - 同一份产出**必须按其 agent_id 角色**判，不能一刀切
    （Executor 本来就要写权项书；Analyzer 写了才叫越界）
  - 只认**结构化越界信号**，不做语义判断；无法判定 → 明确报「不可判定」而非放过

用法：
  python3 scripts/boundary_guard.py --run-dir <产出目录>
  python3 scripts/boundary_guard.py --run-dir <产出目录> --json
  python3 scripts/boundary_guard.py --self-test

退出码：0=无越界  1=存在越界  2=用法/环境错误
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

# ── 角色矩阵真源（成员 → 角色）────────────────────────────────────────
# 与 docs/architecture.md §二 一致；由 contract_enforce 自测1b 反向校验一致性。
ROLE_BY_MEMBER = {
    "contradiction-analyst": "Analyzer",
    "patent-search-scout": "Analyzer",
    "disclosure-architect": "Executor",
    "patent-attorney-writer": "Executor",
    "patent-examiner-sim": "Reviewer",
    "second-opinion-reviewer": "Reviewer",
    "triz-invention-team-team-lead": "Orchestrator",
}

# ── 越界信号定义 ───────────────────────────────────────────────────────
# 每条信号 = (信号ID, 适用角色集合, 人类可读描述, 判定函数)
# 判定函数签名 (text) -> bool（True = 命中越界）

# 1) 撰写申请文件正文：权项书 / 说明书结构
# 标题形态多样：「权利要求书」「权利要求」「权利要求部分」/「说明书」「技术领域」…
# 故用宽松但有界的模式：权 + (利要求|利项求) + 可选「书/部分」等尾缀
_CLAIM_HEAD_RE = re.compile(r"^\s*#{1,4}\s*权(?:利要求|利项求)(?:书|部分|式)?", re.M)
# 说明书体章节（权项书标题不在此列）——变体必须**互斥覆盖**，
# 否则收窄其中一个分支时另一分支仍能兜住 → 变异逃逸（S-E59 变异 M10 的教训）
_SPEC_SEC_RE = re.compile(r"^\s*#{1,4}\s*(说明书|技术领域|背景技术|发明内容)", re.M)


def _has_claims_section(text):
    """是否产出「权利要求书」独立章节（Analyzer/Reviewer 不该有）。"""
    return bool(_CLAIM_HEAD_RE.search(text))


def _has_spec_body(text):
    """是否产出「说明书」正文（权项书标题由 _has_claims_section 覆盖，两者互斥）。"""
    return bool(_SPEC_SEC_RE.search(text))


# 2) 越权出具授权裁决：绿/黄/红 + 最终授权判断
# 关键区分（S-E59 自测对真实基线 A01 的实测教训）：
#   「综合评级：红」**不等于**授权裁决 —— Analyzer（scout）的职责边界明确包含
#   「三性风险评估」，给出红/黄/绿风险评级是职责内产出（基线 A01 原文即
#   「只做三性风险动态评估，不做终局裁决」）。
#   真正的越权是**肯定性授权断言**：「可以授权/建议授权/具备新颖性/具备创造性」。
#   故拆成两个信号：
#     B2 = 肯定性授权断言（对 Analyzer/Executor 禁止；Reviewer 出裁决是职责）
#     B5 = 非职责角色出具三性/风险评级（对 Executor 禁止——交底书/申请文件里不该有评级）
#
# B2 不做引用豁免：「可以授权/建议授权」是**断言句式**，成员写下即代表自己下断言，
#   即使后面跟「（据审查员意见）」也不改变性质。
# B5 做引用豁免：绿/黄/红评级有「本成员出具」与「转述他方结论」两种语境，
#   靠句内引用线索区分（见 _sentence_of + _REFERENCE_CUE_RE）。
_AUTH_JUDGE_RE = re.compile(
    r"(可以授权|建议授权|予以授权|符合授权条件|"
    r"具备(?:新颖性|创造性|授权前景)|授权前景(?:良好|为佳|是乐观))", re.I)
# 结论性评级陈述（用于 B5）——要求「评级/结论」锚点 + 颜色，
# 「三性风险评估：高风险」这类风险提示不含锚点 → 不命中（Analyzer 职责内）
_VERDICT_QUOTE_RE = re.compile(
    r"(综合评级|最终评级|三性综合(?:评级|结论)|授权结论|风险评级|三性评级)"
    r"\s*[：:]\s*(?:绿|黄|红|可授权)", re.I)
# 引用线索（同一句内出现 → 视为转述他方结论，不算本成员出具评级）
_REFERENCE_CUE_RE = re.compile(
    r"(由[^，。\n]{0,20}更新为|引用|参见|详见|见第|"
    r"据[^，。\n]{0,10}(?:报告|结论|裁决)|依据[^，。\n]{0,10}(?:报告|结论|裁决)|"
    r"沿用|继承)", re.I)
_SENT_DELIM = "。；;\n"


def _sentence_of(text, start, end):
    """取包含 [start, end) 的**整句**（以 。；; 换行 分隔）。

    S-E59 修正：原实现只取「匹配点**之前** 60 字符」作上下文 →
    中文引用线索常出现在**后置**补语（「综合评级：红（详见 A01）」），
    前置窗口看不到 → 引用排除形同虚设（变异 M2 逃逸暴露）。
    改为句级上下文：前后都覆盖，且被句界限定 → 不会把邻句的引用线索误算进来。
    """
    left = -1
    for c in _SENT_DELIM:
        p = text.rfind(c, 0, start)
        if p > left:
            left = p
    right = len(text)
    for c in _SENT_DELIM:
        p = text.find(c, end)
        if p != -1 and p < right:
            right = p
    return text[left + 1:right]


def _has_verdict(text):
    """肯定性授权断言 —— Analyzer/Executor 出这个都越权。

    Reviewer（patent-examiner-sim / second-opinion-reviewer）出授权结论是
    **职责内**（docs/architecture.md §二：Reviewer 产出 = verdict；
    且 Analyzer 的 forbidden_boundary 明写「禁止提前给出授权前景结论
    （属 patent-examiner-sim 职责）」）→ 故 Reviewer 不受 B2 约束。
    """
    return bool(_AUTH_JUDGE_RE.search(text))


def _has_rating_by_nonduty_role(text):
    """非职责角色出具三性/风险评级（当前仅 Executor 禁止）。

    句内含引用线索（详见 / 参见 / 据…报告 / 由…更新为 …）时视为转述，不算越界。
    """
    for m in _VERDICT_QUOTE_RE.finditer(text):
        sent = _sentence_of(text, m.start(), m.end())
        if _REFERENCE_CUE_RE.search(sent):
            continue
        return True
    return False


# 3) 自我评价质量：自称「本产出优秀/质量高/已通过」
_SELF_RATE_RE = re.compile(
    r"(本产出(?:质量)?(?:优秀|良好|高质量)|质量(?:优秀|良好|很高)"
    r"|(?:本报告|本文|本产出)(?:已)?(?:通过|满足)(?:质量)?(?:评审|检查)"
    r"|自我评价[：:]\s*(?:优秀|良好|合格))")


def _has_self_rating(text):
    return bool(_SELF_RATE_RE.search(text))


# 4) Reviewer 越权修改方案：Reviewer 只出裁决+建议，不得改写方案本体
_REWRITE_RE = re.compile(
    r"(将(?:权项|权利要求|方案|独立权项)\s*\d*\s*(?:修改|改为|替换为|修正为)"
    r"|权项\s*\d+\s*(?:已)?(?:修改|改写|改为)"
    r"|(?:已|现)(?:把|将)方案(?:第[一二三四五六七八九十\d]+(?:章|节|部分))?"
    r"\s*(?:修改|改写|替换))", re.I)


def _has_rewrite(text):
    return bool(_REWRITE_RE.search(text))


# 信号表：(信号ID, 禁止的角色, 描述, 判定函数)
BOUNDARY_SIGNALS = [
    ("B1", {"Analyzer", "Reviewer", "Orchestrator"},
     "撰写申请文件正文（权利要求书 / 说明书）",
     lambda t: _has_claims_section(t) or _has_spec_body(t)),
    # 注：Reviewer 不受 B2 约束——其产出定义就是 verdict（绿/黄/红 + 问题清单），
    # 且 Analyzer 的 forbidden_boundary 明写「授权前景结论属 patent-examiner-sim 职责」。
    ("B2", {"Analyzer", "Executor"},
     "出具最终授权裁决（绿/黄/红 · 授权结论）",
     _has_verdict),
    ("B3", {"Executor", "Reviewer", "Analyzer", "Orchestrator"},
     "自我评价产出质量",
     _has_self_rating),
    ("B4", {"Reviewer", "Analyzer"},
     "越权修改技术方案（只应出裁决与修复建议）",
     _has_rewrite),
    ("B5", {"Executor"},
     "在交付文档中出具三性/风险评级（属查新/审查职责）",
     _has_rating_by_nonduty_role),
]

# Analyzer 允许产出「三性风险评估」（scout 的职责），但不得出具**最终授权**裁决。
# 上面的 B2 已用「综合评级/最终评级/授权结论」等**结论性**措辞限定，
# 「三性风险评估：高风险」这类风险提示不命中（不含「评级/结论」锚点）。


def detect_agent_id(text):
    """从产出中提取 agent_id（信封 JSON 优先，其次文件名）。"""
    m = re.search(r'"agent_id"\s*:\s*"([a-z0-9-]+)"', text)
    if m:
        return m.group(1)
    return None


def scan_output(md_path, agent_id=None):
    """扫描单份产出，返回越界结论。

    返回 dict:
      {agent_id, role, verdict, violations: [...], reason}
      verdict ∈ {"clean", "violation", "unknown_role", "unreadable"}
    """
    fname = os.path.basename(md_path)
    if not os.path.isfile(md_path):
        return {"agent_id": agent_id, "role": None, "verdict": "unreadable",
                "violations": [], "reason": "文件不存在"}
    try:
        with open(md_path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        return {"agent_id": agent_id, "role": None, "verdict": "unreadable",
                "violations": [], "reason": str(e)}

    if not agent_id:
        m = re.search(r"T-[^_]+__([a-z0-9-]+)\.md$", fname)
        agent_id = m.group(1) if m else detect_agent_id(text)
    if not agent_id:
        return {"agent_id": None, "role": None, "verdict": "unknown_role",
                "violations": [], "reason": "无法确定 agent_id（信封与文件名均无）"}

    role = ROLE_BY_MEMBER.get(agent_id)
    if not role:
        return {"agent_id": agent_id, "role": None, "verdict": "unknown_role",
                "violations": [], "reason": "未知成员（不在角色矩阵内）"}

    violations = []
    for sig_id, forbidden_roles, desc, checker in BOUNDARY_SIGNALS:
        if role in forbidden_roles and checker(text):
            violations.append({"signal": sig_id, "role": role,
                               "desc": desc})
    return {
        "agent_id": agent_id, "role": role,
        "verdict": "violation" if violations else "clean",
        "violations": violations,
        "reason": "命中 %d 条禁止边界" % len(violations) if violations else "未命中越界信号",
    }


def scan_run_dir(run_dir):
    """扫描目录内所有成员产出。"""
    import glob
    results = []
    for p in sorted(glob.glob(os.path.join(run_dir, "T-*__*.md"))):
        results.append(scan_output(p))
    return results


# ─────────────────────────────────────────────────────────────────────
# 判别力自测
# ─────────────────────────────────────────────────────────────────────
_SELF_TEST_CASES = [
    # (用例名, agent_id, 文本, 期望 verdict, 期望信号集)
    ("Analyzer正常产出-矛盾矩阵",
     "contradiction-analyst",
     "## 一、矛盾矩阵\n\n| # | 矛盾 | 分离原理 |\n|---|---|---|\n| 1 | 强度与成本 | 分割 |\n",
     "clean", set()),
    ("Analyzer正常产出-查新报告含风险评估",
     "patent-search-scout",
     "## 三性风险评估\n\n新颖性：高风险\n创造性：高风险\n",
     "clean", set()),
    ("Analyzer越界-写了权利要求书",
     "contradiction-analyst",
     "# 权利要求书\n\n1. 一种刮粪装置，其特征在于……\n",
     "violation", {"B1"}),
    ("Analyzer越界-写了说明书",
     "patent-search-scout",
     "## 说明书\n\n### 技术领域\n本发明涉及……\n",
     "violation", {"B1"}),
    # 锁定「说明书体章节」四个分支各自独立可判（变异 M10 的教训）：
    # 「技术领域/背景技术/发明内容」是说明书体的标准小节标题，
    # Analyzer/Reviewer 产出中不应出现 → 收窄 _SPEC_SEC_RE 必被捕获。
    ("Analyzer越界-写了技术领域小节",
     "contradiction-analyst",
     "### 技术领域\n\n本发明涉及猪舍粪沟清理装置。\n",
     "violation", {"B1"}),
    ("Analyzer越界-写了发明内容小节",
     "patent-search-scout",
     "## 发明内容\n\n本发明公开了一种刮粪装置。\n",
     "violation", {"B1"}),
    ("Executor越界-出具授权裁决",
     "patent-attorney-writer",
     "## 结论\n\n可以授权，建议提交申请。\n",
     "violation", {"B2"}),
    ("Executor正常产出-写权项书（不越界）",
     "patent-attorney-writer",
     "# 权利要求书\n\n1. 一种刮粪装置，其特征在于……\n",
     "clean", set()),
    ("Reviewer正常产出-出具裁决（不越界）",
     "patent-examiner-sim",
     "## 裁决\n\n综合评级：红\n问题清单：……\n",
     "clean", set()),
    ("Analyzer正常产出-风险评级（职责内）",
     "patent-search-scout",
     "### 5.3 综合评级与放行判断\n\n**综合评级：红。**\n"
     "按角色职责边界，本报告只做三性风险动态评估，不做终局裁决。\n",
     "clean", set()),
    ("Executor越界-在交底书里出具评级",
     "disclosure-architect",
     "## 交底书\n\n### 风险评级\n\n综合评级：绿\n",
     "violation", {"B5"}),
    # 锁定「风险评级/三性评级」这两个锚点（变异 M18 的教训）：
    # Executor 在交底书里写「风险评级：红」与写「综合评级：红」性质相同 → 都算越界。
    ("Executor越界-只写风险评级锚点",
     "disclosure-architect",
     "## 交底书\n\n风险评级：红\n",
     "violation", {"B5"}),
    ("Executor越界-只写三性评级锚点",
     "disclosure-architect",
     "## 交底书\n\n三性评级：黄\n",
     "violation", {"B5"}),
    # 锁定「Reviewer 出授权断言不算越界」语义（变异 M7 的教训）：
    # Reviewer 的产出定义就是 verdict，授权结论属其职责 → B2 不禁 Reviewer。
    # 无此用例时，把 Reviewer 加进 B2 角色集不会被自测发现。
    ("Reviewer正常产出-出具授权结论（职责内）",
     "patent-examiner-sim",
     "## 裁决\n\n本案具备新颖性，可以授权。\n",
     "clean", set()),
    ("Reviewer正常产出-二审同意（职责内）",
     "second-opinion-reviewer",
     "## 二审意见\n\n✅同意\n\n该方案具备创造性，符合授权条件。\n",
     "clean", set()),
    # 注意（S-E59 补强）：原用例写「综合评级由红更新为黄」——该形态**不匹配**
    # _VERDICT_QUOTE_RE（要求「综合评级」后紧跟「：+颜色」），故本用例从未真正
    # 经过引用排除分支 → **假绿**。变异测试 M2（删掉引用排除）逃逸暴露了它。
    # 改为真实形态：先有结论式评级，再带引用线索 → 命中 _VERDICT_QUOTE_RE
    # 但被 _REFERENCE_CUE_RE 排除 → 判 clean。
    ("Executor正常产出-引用上游评级不算越界",
     "disclosure-architect",
     "## 交底书\n\n依据 patent-search-scout 报告，综合评级：黄（由 A01 报告更新为黄）。\n",
     "clean", set()),
    ("Executor正常产出-引用他处结论不算越界",
     "disclosure-architect",
     "## 交底书\n\n三性综合评级：红（详见查新报告 A01 第三节）。\n",
     "clean", set()),
    ("Reviewer越界-修改方案",
     "patent-examiner-sim",
     "综合评级：绿\n建议将权项1改为「……」（直接改写方案文本）\n",
     "violation", {"B4"}),
    ("Analyzer越界-越权修改方案",
     "contradiction-analyst",
     "已将方案第三部分修改为分体式结构\n",
     "violation", {"B4"}),
    ("Executor越界-自我评价",
     "disclosure-architect",
     "本产出质量优秀，已通过质量检查。\n",
     "violation", {"B3"}),
    ("全员越界-自我评价质量",
     "second-opinion-reviewer",
     "## 自查\n\n本产出质量优秀，已通过质量检查。\n",
     "violation", {"B3"}),
    ("未知成员-不可判定",
     "not-a-member",
     "# 权利要求书\n\n1. xxx\n",
     "unknown_role", set()),
]


def _self_test():
    """判别力自测：每条用例必须同时满足「verdict 命中」与「信号集精确匹配」。"""
    fails = []
    print("🧪 boundary_guard 判别力自测（%d 用例）\n" % len(_SELF_TEST_CASES))
    for name, agent_id, text, exp_verdict, exp_sigs in _SELF_TEST_CASES:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            fp = os.path.join(td, "T-20261015-A01__%s.md" % agent_id)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(text)
            r = scan_output(fp, agent_id=agent_id)
        got_sigs = {v["signal"] for v in r["violations"]}
        ok_v = (r["verdict"] == exp_verdict)
        ok_s = (got_sigs == exp_sigs)
        passed = ok_v and ok_s
        print("  %s %-38s 期望=%-13s 信号=%-10s | 实得=%-13s 信号=%s"
              % ("✅" if passed else "❌", name, exp_verdict,
                 ",".join(sorted(exp_sigs)) or "-",
                 r["verdict"], ",".join(sorted(got_sigs)) or "-"))
        if not passed:
            fails.append(name)

    # 角色矩阵完整性
    print("\n  ── 角色矩阵 ──")
    for m, role in sorted(ROLE_BY_MEMBER.items()):
        ok = role in ("Analyzer", "Executor", "Reviewer", "Orchestrator")
        print("  %s %-32s → %s" % ("✅" if ok else "❌", m, role))
        if not ok:
            fails.append(m)

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    print("\n✅ 自测全通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="成员产出越界红线机械拦截（S-E59）")
    ap.add_argument("--run-dir", help="成员产出目录")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if not args.run_dir:
        ap.print_help()
        return 2
    if not os.path.isdir(args.run_dir):
        print("❌ 目录不存在：%s" % args.run_dir, file=sys.stderr)
        return 2

    results = scan_run_dir(args.run_dir)
    if not results:
        print("⚠️  目录内无成员产出（T-*__*.md）")
        return 0

    n_viol = sum(1 for r in results if r["verdict"] == "violation")
    n_unknown = sum(1 for r in results if r["verdict"] == "unknown_role")

    if args.json:
        print(json.dumps({"run_dir": args.run_dir, "scanned": len(results),
                          "violations": n_viol, "unknown": n_unknown,
                          "results": results}, ensure_ascii=False, indent=2))
    else:
        print("🛡️ 越界红线扫描 — %s（%d 份产出）\n" % (args.run_dir, len(results)))
        for r in results:
            if r["verdict"] == "clean":
                print("  ✅ %-30s [%s] 未越界" % (r["agent_id"], r["role"]))
            elif r["verdict"] == "violation":
                for v in r["violations"]:
                    print("  ❌ %-30s [%s] %s：%s"
                          % (r["agent_id"], r["role"], v["signal"], v["desc"]))
            else:
                print("  ⚠️  %-30s %s" % (r["agent_id"], r["reason"]))
        print("\n越界 %d 份 / 不可判定 %d 份 / 共 %d 份"
              % (n_viol, n_unknown, len(results)))

    if n_viol:
        print("❌ 存在越界产出——禁止边界不是文档条款，是运行时红线", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
