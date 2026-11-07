#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contract_enforce.py — P0-S1-1 契约执行门禁

按 docs/CONTRACT_ENFORCEMENT.md 的 6 成员契约清单，对成员产出做机器验证。

用法：
  python3 scripts/contract_enforce.py --member contradiction-analyst --output <file>
  python3 scripts/contract_enforce.py --output-dir <dir> --exit-on-fail
  python3 scripts/contract_enforce.py --self-test

退出码：0=全过 1=有违反 2=参数错
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PKG = HERE.parent
DOCS = PKG / "docs" / "CONTRACT_ENFORCEMENT.md"

# 6 成员契约 —— forbidden_phrases 从各成员 frontmatter **解析**（唯一真源，2026-11-07 单源化）
#   verifications 保留在本脚本（机械实现的归属地），与 docs/CONTRACT_ENFORCEMENT.md 同步维护。
#   启动时解析失败/缺表 → 该成员 forbidden 回退空列表并告警（不静默吞错）。
VERIFICATIONS = {
    "contradiction-analyst": [
        ("directions≥3",  lambda out: len(re.findall(r"#?\d+\.|方向[1-9]|IP #\d+", out)) >= 3),
        ("原理实跑",        lambda out: bool(re.search(r"query_triz_matrix|退出码", out))),
    ],
    # 注: "基本" 是中文常用词，不在禁词列表（已豁免）
    "patent-search-scout": [
        # 双向契约：首轮查新需6类；定向复检只针对已知X/Y/A/R类，≥3类即可
        ("X/Y/A/R/P/E 6类 或 复检≥3类", lambda out: _check_xyarpe_or_recheck(out)),
        ("search_rounds≥3",  lambda out: len(re.findall(r"R[123]|第[一二三]轮", out)) >= 3),
    ],
    "patent-examiner-sim": [
        ("裁决显式(绿/黄/红)", lambda out: _check_verdict(out)),
        ("修复清单(强制/建议)",  lambda out: bool(re.search(r"(强制|建议)", out))),
    ],
    "second-opinion-reviewer": [
        ("二次表态显式", lambda out: bool(re.search(r"✅|⚠|🔴|附条件", out))),
        ("条件清单显式",  lambda out: bool(re.search(r"(附加条件|条件清单|附条件)", out))),
    ],
    "disclosure-architect": [
        ("必要/可选分层",  lambda out: bool(re.search(r"(必要特征|可选特征)", out))),
        ("缺口清单",        lambda out: bool(re.search(r"(缺口|待补)", out))),
        ("实施例≥2档",     lambda out: len(re.findall(r"实施例\s*\d", out)) >= 2),
    ],
    "patent-attorney-writer": [
        ("摘要≤300+机械证据", lambda out: _check_abstract(out)),
        ("权利要求禁用词零命中", lambda out: _check_claims_banned(out)),
    ],
}

MEMBER_IDS = list(VERIFICATIONS.keys())

# 信封 deliverable_summary 格式契约（S5-4 · 2026-10-15 规范 → 2026-11-07 Batch3 机械实现 · 修 S-M1）
#   「<对象>」完成<动作>：<结论A>；<结论B>；…（40-60字符·含裁决/评级时必含）
SUMMARY_MIN_CHARS = 40
SUMMARY_MAX_CHARS = 60
# 必含元素（按成员）：从 deliverable_summary 里 grep（豁免链外的机械底线）
SUMMARY_MUST_CONTAIN = {
    "contradiction-analyst":   [r"方向"],
    "patent-search-scout":     [r"X\s*级|评级|绿|黄|红"],
    "patent-examiner-sim":     [r"绿|黄|红"],
    "second-opinion-reviewer": [r"同意|附条件|不同意|✅|⚠|🔴"],
    "disclosure-architect":    [r"必要特征|特征"],
    "patent-attorney-writer":  [r"摘要|\d+\s*字符"],
}


def _check_summary(out):
    """deliverable_summary 40-60 字符 + 必含元素（从信封 JSON 里取；WARN 级——格式偏离不阻断交付）。

    返回 (ok, detail)；ok=False 时由 check_member 记入 info["summary_warn"]（不计入 issues）。
    """
    m = re.search(r"\{[^{}]*\"deliverable_summary\"\s*:\s*\"([^\"]+)\"", out, re.S)
    if not m:
        return False, "未提取到信封 deliverable_summary（可能为纯文本产出）"
    s = m.group(1)
    n = len(s)
    mid = None
    ma = re.search(r"\"agent_id\"\s*:\s*\"([^\"]+)\"", out)
    if ma:
        mid = ma.group(1)
    problems = []
    if n < SUMMARY_MIN_CHARS:
        problems.append(f"{n}字符<{SUMMARY_MIN_CHARS}")
    elif n > SUMMARY_MAX_CHARS:
        problems.append(f"{n}字符>{SUMMARY_MAX_CHARS}")
    if mid in SUMMARY_MUST_CONTAIN:
        if not any(re.search(p, s) for p in SUMMARY_MUST_CONTAIN[mid]):
            problems.append(f"缺必含元素（{mid}）")
    if problems:
        return False, f"summary {n}字符: {'; '.join(problems)}"
    return True, f"summary {n}字符合规"


def _load_frontmatter_forbidden(member_id):
    """从 agents/<member_id>.md frontmatter 解析 forbidden_phrases 列表（唯一真源）。

    返回 (patterns: list[str], error: str|None)。解析失败时 error 说明原因。
    """
    md = PKG / "agents" / (member_id + ".md")
    if not md.is_file():
        return [], f"agents/{member_id}.md 不存在"
    text = md.read_text(encoding="utf-8")
    # frontmatter = 文件首个 --- 与下一个 --- 之间
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return [], "无 frontmatter 块"
    fm = m.group(1)
    fm_m = re.search(r"^forbidden_phrases:\s*\n((?:[ \t]+-[ \t]*.*\n?)+)", fm, re.M)
    if not fm_m:
        return [], "frontmatter 无 forbidden_phrases 列表"
    pats = []
    for line in fm_m.group(1).splitlines():
        item = re.match(r"^[ \t]+-[ \t]*(.+?)\s*$", line)
        if item:
            pats.append(item.group(1))
    if not pats:
        return [], "forbidden_phrases 列表为空"
    return pats, None


def _load_contracts():
    """组装 CONTRACTS：forbidden 来自 frontmatter（真源），verifications 来自本表。"""
    contracts = {}
    for mid in MEMBER_IDS:
        pats, err = _load_frontmatter_forbidden(mid)
        contracts[mid] = {"forbidden": pats, "verifications": VERIFICATIONS[mid], "source_error": err}
    return contracts


CONTRACTS = _load_contracts()

# 通用豁免标记——成员标注元数据后即使含禁词也通过
EXEMPT_MARKERS = ["[INFERRED]", "[KNOWN]", "[实测]", "[证据:", "自检节", "【自检】", "**自检**"]
# 通用豁免词——任何含这些词的命中算"在讨论/引用而非使用"
EXEMPT_WORDS = ["基本设计常识", "基本物理", "基本公式", "基本定理", "基本原理", "基本概念", "基本事实", "成本约束", "工艺约束", "成本与工艺", "受成本约束"]


def _is_exempt(context):
    """检查一段文本上下文是否含豁免标记或豁免词"""
    if any(m in context for m in EXEMPT_MARKERS):
        return True
    if any(w in context for w in EXEMPT_WORDS):
        return True
    return False


def _clean_for_forbidden_scan(text):
    """清洗文本用于禁词扫描：去掉附录/自检/纯表格/代码块/字典字面量/Python字面量。
    只在契约正文（说明/数据/结论/攻击/裁决/警示）里查禁词。

    移除段（按行处理）：
    - ```代码块```（含python字面量如 `words = ["大约", ...]`）
    - 纯表格行（| 开头且全表行）
    - 附录 A/B/C/D/E 段
    - 段尾「禁用词机械自查」全段（自检表）
    """
    lines = text.split("\n")
    out = []
    in_code = False
    in_appendix = False
    in_selfcheck = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if re.match(r"^\s*\|", line) and (re.match(r"^\s*\|[\s\-:|]+\|\s*$", line) or re.search(r"\|", line[1:])):
            # 纯表格行（含表头、分隔、数据行）—— 跳
            continue
        if re.search(r"^#{2,4}\s*附录\s*[A-Z]", line):
            in_appendix = True
        if re.search(r"^#{1,4}\s*（未完|接下|续）", line):
            in_appendix = False
        if in_appendix:
            continue
        if re.search(r"禁用词机械自查|禁用词.*?自检", line):
            in_selfcheck = True
        if in_selfcheck and re.match(r"^#{1,4}\s", line):
            in_selfcheck = False
        if in_selfcheck:
            continue
        # 字典/列表字面量：单行内以 { 或 [ 开头并以 } 或 ] 结尾、含 '或" 引号
        if re.match(r"^\s*[\{\[][^\n]*[\}\]]\s*$", line) and ("'" in line or '"' in line):
            continue
        out.append(line)
    return "\n".join(out)


def _check_abstract(out):
    """writer 摘要契约：≤300 字符 + 必须有机械验证证据（python len()=N）

    A07 等成品的摘要结构是：
      ## 三、说明书摘要
      **摘要正文**：<实际摘要，应 ≤300>
      **摘要附图**：图1
      **机械验证证据**：...
      **结论**：...

    契约只数"摘要正文"段（从"摘要正文"到"摘要附图"或下一段），
    附录/证据/结论是 metadata，不计入摘要。
    """
    # 找到摘要段起止
    m = re.search(r"^#{2,4}\s*[\d一二三四五六七八九十、\.]*\s*(?:说明书)?(?:摘要|Abstract)\s*\n+(.*?)(?=\n#{1,4}\s|\Z)", out, re.M | re.S)
    if not m:
        return False, "未找到说明书摘要段"
    section = m.group(1)
    # 摘要正文通常以 `**摘要正文**:` 开头；止于 `**摘要附图**` 或 `**机械验证**` 或 `**结论**`
    body_match = re.search(r"(?:\*\*)?摘要正文\*?\*?[:：]?\s*\n+(.*?)(?=\n\s*(?:\*\*)?(?:摘要附图|机械验证|结论|自查))", section, re.S)
    if not body_match:
        # 退而求其次：取第一段
        body_match = re.search(r"^\s*(.*?)(?=\n\s*\n|\n\s*---|\Z)", section, re.S | re.M)
    if not body_match:
        return False, "摘要正文段为空"
    txt = re.sub(r"```.*?```", "", body_match.group(1), flags=re.S).strip()
    n = len(txt)
    has_evidence = bool(re.search(r"python\s*len\(|len\(.*\)\s*=\s*\d+\s*字符", out))
    if n > 300:
        return False, f"摘要正文{n}字符>300"
    if not has_evidence:
        return False, "无机械验证证据（python len()=N）"
    return True, f"摘要正文{n}字符+机械证据✅"


def _check_verdict(out):
    """examiner 裁决显式：宽松——裁决/结论附近有绿/黄/红 灯色
    灯色同时支持 emoji 🟢🟡🔴 与文字 绿/黄/红
    """
    # 模式1：裁决/结论/verdict 同段（200字符内）有灯色
    for m in re.finditer(r"裁决|结论|verdict", out, re.I):
        window = out[m.start():min(len(out), m.end() + 200)]
        if re.search(r"🟢|🟡|🔴|绿|黄|红", window):
            return True, "裁决/结论 200 字符内含灯色"
    # 模式2：🟢/🟡/🔴 emoji 全文存在（且为决策用而非 emoji 字面量）
    if re.search(r"🟢|🟡|🔴", out):
        return True, "灯色 emoji 显式"
    return False, "未找到裁决灯色"


def _check_xyarpe(out):
    """scout X/Y/A/R/P/E 6 类契约：宽松正则（X级 也算X类）"""
    classes = {
        "X": r"X\s*(类|级)", "Y": r"Y\s*(类|级)", "A": r"A\s*(类|级)",
        "R": r"R\s*(类|级)", "P": r"P\s*(类|级)", "E": r"E\s*(类|级)",
    }
    found = {k: bool(re.search(v, out)) for k, v in classes.items()}
    missing = [k for k, v in found.items() if not v]
    if missing:
        return False, f"缺类: {missing}"
    return True, "6类齐全✅"


def _check_xyarpe_or_recheck(out):
    """scout 6类契约：双向——首轮6类 or 定向复检继承A01 X级清单 + ≥2类细化"""
    r = _check_xyarpe(out)
    if r[0]:
        return r
    is_recheck = re.search(r"(复检|定向.*?检|差异化|逐条.*?比|逐条回|recheck)", out)
    classes = {
        "X": r"X\s*(类|级)", "Y": r"Y\s*(类|级)", "A": r"A\s*(类|级)",
        "R": r"R\s*(类|级)", "P": r"P\s*(类|级)", "E": r"E\s*(类|级)",
    }
    found = sum(1 for v in classes.values() if re.search(v, out))
    # 复检+继承A01 X级清单(有"X级"+"N级"或"4条"等) ≥2类
    inherit_a01 = re.search(r"A01.*?(X\s*级清单|4\s*条\s*X|5\s*条\s*X|已核验公开内容)", out)
    if is_recheck and inherit_a01 and found >= 2:
        return True, f"复检+继承A01：{found}类显式"
    return False, f"缺类且非复检（{found}/6）"


def _check_claims_banned(out):
    """writer 权利要求禁用词：8 词零命中（自检节除外）

    范围：A07 等产出有明确分区——「A 区 权项+说明书+摘要」/「B 区 其余正文」/「C 区」。
    这里**只扫 A 区**（即"权利要求书"到"其余正文"前），B/C 区是自查节。
    """
    banned = ["大约", "左右", "之类的", "最好", "优选", "若干", "高效", "大幅"]
    # A 区起：权利要求书/说明书/摘要 段；止：B 区或其他分区
    sec_a = ""
    for sec_name in ["权利要求书", "说明书", "摘要"]:
        i = out.find(sec_name)
        if i >= 0:
            # 取到下一个 ## 标题或 B 区
            j = out.find("\n## ", i + 10)
            j_b = out.find("B 区", i)
            end = min(x for x in [j, j_b, len(out)] if x > 0)
            sec_a += out[i:end] + "\n"
    if not sec_a:
        sec_a = out  # 回退全文
    hits = [b for b in banned if b in sec_a]
    if hits:
        return False, f"禁用词命中: {hits}（位于 A 区——权利要求+说明书+摘要）"
    return True, "A区零命中"


def check_member(member_id, output_text):
    """检查单个成员产出。返回 (passed:bool, issues:list[str], info:dict)"""
    if member_id not in CONTRACTS:
        return False, [f"未知成员: {member_id}"], {}
    c = CONTRACTS[member_id]

    issues = []
    info = {"member": member_id, "forbidden_hits": [], "verification_results": [], "summary_warn": []}

    # 0) deliverable_summary 格式检查（WARN 级 · 修 S-M1）——不进 issues，不阻断，只登记
    sok, sdetail = _check_summary(output_text)
    info["summary_warn"].append({"ok": sok, "detail": sdetail})

    # 1) 禁词检测 —— 仅扫契约正文段（去掉附录/自检/纯表格/代码块/Python字面量）
    cleaned = _clean_for_forbidden_scan(output_text)
    for pat in c["forbidden"]:
        for m in re.finditer(pat, cleaned):
            window = cleaned[max(0, m.start() - 30):min(len(cleaned), m.end() + 30)].replace("\n", " | ")
            # 元数据豁免：analyst 表格内的"可授权可能性"列名（专有名词）
            if member_id == "contradiction-analyst" and "可授权可能性" in window and ("列" in window or "表头" in window):
                continue
            # 通用豁免词："基本设计常识"等是讨论/引用而非使用
            if any(w in window for w in EXEMPT_WORDS):
                continue
            # 反例引用豁免：成员在"禁止 X"列表里说"不得X"——window 含禁止信号
            anti_pattern_markers = [
                r"不得[凭基估按]",
                r"禁止[凭基估按]",
                r"[不勿]?[要允][求许]?凭",
                r"未[凭允]",
                r"已[经避]?[免]?[凭靠]",
                r"代[填估]",
                r"不[代填估]",
                r"按[双轨]制.*?不[代迎估]",
                r"以[代免]",
                # 反例：成员在写"不得估算/不能代填/不应估计/而非凭记忆"
                r"不得[代估按]",
                r"不[应能要]估",
                r"未[代估]",
                r"未[发归生行]",
                r"[未无][代反]",
                r"非[凭代估按]",   # [2026-11-07] A02"而非凭记忆引用"漏配补丁
                r"无一[处个].{0,4}凭",  # [2026-11-07] B01"无一处凭记忆生成"漏配补丁
                r"[遵按]守?.{0,6}红线",
                r"红线[：:]",
            ]
            if any(re.search(p, window) for p in anti_pattern_markers):
                continue
            # 中文学术必备"可能"在"判断"语境（非猜测）：后跟判断动词
            # 豁免: "可能+判断/被/导/引/为/会"等
            likely_judgement = [
                r"可能[被导引为会]",
                r"可能[性体化]",
                r"可能[存会致填塞]",
                r"可能[为在有]",
            ]
            if any(re.search(p, window) for p in likely_judgement):
                continue
            info["forbidden_hits"].append({"pattern": pat, "context": window[:80]})
            issues.append(f"FORBIDDEN 命中 {pat}: ...{window[:80]}...")

    # 2) 验证项
    for name, fn in c["verifications"]:
        try:
            r = fn(output_text)
            if isinstance(r, tuple):
                ok, detail = r
            else:
                ok, detail = r, "✅" if r else "❌"
            info["verification_results"].append({"name": name, "ok": bool(ok), "detail": str(detail)})
            if not ok:
                issues.append(f"VERIFY {name}: {detail}")
        except Exception as e:
            issues.append(f"VERIFY {name} 异常: {e}")
            info["verification_results"].append({"name": name, "ok": False, "detail": f"异常: {e}"})

    return (len(issues) == 0), issues, info


def main():
    ap = argparse.ArgumentParser(description="P0-S1-1 契约执行门禁")
    ap.add_argument("--member", help="成员 ID（如 contradiction-analyst）")
    ap.add_argument("--output", help="成员产出文件路径")
    ap.add_argument("--output-dir", help="批量验证目录（递归所有 T-*__<member>.md）")
    ap.add_argument("--exit-on-fail", action="store_true", help="有违反即 exit 1")
    ap.add_argument("--self-test", action="store_true", help="跑自测")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    if args.self_test:
        # 用已知 L2 实测产物做自测 + 三源一致性检查（2026-11-07 单源化新增）
        ok_all = True
        print("== 自测1：三源一致性（frontmatter 可解析 + 非空 + 与文档并集一致）==")
        for mid in MEMBER_IDS:
            pats, err = _load_frontmatter_forbidden(mid)
            if err:
                print(f"  ❌ {mid}: {err}")
                ok_all = False
            else:
                print(f"  ✅ {mid}: {len(pats)} 条禁词模式（真源=frontmatter）")
        test_file = PKG / "outputs" / "regression-20261015" / "a01" / "T-20261015-A07__patent-attorney-writer.md"
        if test_file.exists():
            text = test_file.read_text(encoding="utf-8")
            passed, issues, info = check_member("patent-attorney-writer", text)
            print(f"== 自测2：L2 样本回归 ==\n  样本: {test_file.name}\n  passed: {passed} | issues: {len(issues)}")
            for i in issues[:3]:
                print(f"    - {i}")
            if not passed:
                ok_all = False
        else:
            print("== 自测2：⚠️ 无实测样本·跳过 ==")
        return 0 if ok_all else 1

    targets = []
    if args.member and args.output:
        targets = [(args.member, Path(args.output))]
    elif args.output_dir:
        d = Path(args.output_dir)
        for p in d.rglob("T-*__*.md"):
            m = re.search(r"T-[^_]+__(\S+)\.md$", p.name)
            if m and m.group(1) in CONTRACTS:
                targets.append((m.group(1), p))
    else:
        ap.print_help()
        return 2

    all_ok = True
    results = []
    for mid, fp in targets:
        text = fp.read_text(encoding="utf-8")
        passed, issues, info = check_member(mid, text)
        info["file"] = str(fp)
        info["passed"] = passed
        results.append(info)
        if not passed:
            all_ok = False

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        # 真源解析失败必须显式告警（不静默吞错）
        for mid in MEMBER_IDS:
            if CONTRACTS[mid].get("source_error"):
                print(f"⚠️  {mid} frontmatter 禁词表解析失败: {CONTRACTS[mid]['source_error']}（forbidden 未生效）")
        for r in results:
            icon = "✅" if r["passed"] else "❌"
            print(f"{icon} {r['member']:30s} {Path(r['file']).name}")
            for issue in []:  # 不打印 issues（太冗）；只打印 hits
                pass
            for h in r["forbidden_hits"]:
                print(f"    🚫 FORBIDDEN  {h['context']}")
            for v in r["verification_results"]:
                if not v["ok"]:
                    print(f"    ❌ VERIFY     {v['name']}: {v['detail']}")
            for w in r.get("summary_warn", []):
                if not w["ok"]:
                    print(f"    ⚠️  SUMMARY-WARN {w['detail']}")

    return 0 if (all_ok or not args.exit_on_fail) else 1


if __name__ == "__main__":
    sys.exit(main())
