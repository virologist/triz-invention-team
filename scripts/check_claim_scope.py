#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_claim_scope.py — P1-3: 交底书必要特征 ⊆ 独立权项 机械校验
用法：
  python3 scripts/check_claim_scope.py --disclosure <交底书.md> --claims <申请文件.md>
  python3 scripts/check_claim_scope.py --l2   # 用 L2 回归默认路径
逻辑：从交底书取"必要特征"清单（逐条），在申请文件"独立权项 1"文本中做
最长公共子串匹配（阈值 ≥12 字符）；任一特征 <阈值 → 报"超范围风险"。
退出码：0=全覆盖 1=有缺失 2=参数错
"""
import argparse, re, sys
from pathlib import Path

def longest_common_substring(a, b):
    if not a or not b: return ""
    m = [[0]*(len(b)+1) for _ in range(len(a)+1)]
    best, bi = 0, 0
    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            if a[i-1] == b[j-1]:
                m[i][j] = m[i-1][j-1] + 1
                if m[i][j] > best:
                    best, bi = m[i][j], i
    return a[bi-best:bi]

def extract_features(text, section_pat, item_pat):
    """从段中提取特征清单（返回 [(特征名, 特征全文)]）。
    多处命中时取**特征条目最多**的段（信封JSON/引用段在前，正文§5.1条目最密）"""
    best = []
    for m in re.finditer(section_pat, text, re.S):
        sec = m.group(1)
        # 特征切分：以特征标记为界，取标记到下一标记之间的全文
        marks = list(re.finditer(item_pat, sec))
        items = []
        for k, im in enumerate(marks):
            start = im.start()
            end = marks[k+1].start() if k+1 < len(marks) else len(sec)
            chunk = re.sub(r"\s+", "", sec[start:end])[:600]
            items.append((im.group(1).strip()[:40], chunk))
        if len(items) > len(best):
            best = items
    return best

def _self_test():
    """判别力自测（S-E58）：LCS 匹配 + 特征提取。

    判别力验收标准（原则④）：改坏真源后本测试必须报错；还原后必须 PASS。
    """
    fails = []

    def chk(name, got, expect):
        okk = (got == expect)
        print("  %s %-46s 期望=%-20s 实得=%s"
              % ("✅" if okk else "❌", name, expect, got))
        if not okk:
            fails.append(name)

    print("🧪 check_claim_scope 判别力自测\n")

    # ── 1. 最长公共子串 ──
    print("  ── longest_common_substring ──")
    chk("完全相同", longest_common_substring("刮粪板拆卸连接", "刮粪板拆卸连接"),
        "刮粪板拆卸连接")
    chk("部分重叠取最长", longest_common_substring("abcdefg", "xxcdeyy"),
        "cde")
    chk("无公共子串 → 空串", longest_common_substring("abc", "xyz"), "")
    chk("空输入 → 空串", longest_common_substring("", "abc"), "")
    chk("另一方为空 → 空串", longest_common_substring("abc", ""), "")

    # ── 2. 特征提取（三种标记格式 + 取条目最多的段）──
    print("\n  ── extract_features ──")
    txt_star = "## 必要技术特征\n\n**F1 · 刮板本体**\n刮板本体包括…\n\n**F2 · 连接座**\n连接座…\n"
    f1 = extract_features(txt_star,
                          r"(?:必要(?:技术)?特征|独立权项素材)[^\n]*\n(.*?)(?=\n#{2,4}\s+[^#]|\Z)",
                          r"\*{0,2}(F\d+|N\d+)\*{0,2}\s*(?:·|[:：])\s*([^\n]+)")
    chk("**F1 · 名称** 形态提取条数", len(f1), 2)
    chk("**F1 · 名称** 首条特征名", f1[0][0] if f1 else None, "F1")

    txt_colon = "## 必要特征\n\nF1: 刮板本体\n说明…\nF2: 连接座\n说明…\nF3: 限位结构\n说明…\n"
    f2 = extract_features(txt_colon,
                          r"(?:必要(?:技术)?特征|独立权项素材)[^\n]*\n(.*?)(?=\n#{2,4}\s+[^#]|\Z)",
                          r"\*{0,2}(F\d+|N\d+)\*{0,2}\s*(?:·|[:：])\s*([^\n]+)")
    chk("F1: 冒号形态提取条数", len(f2), 3)

    txt_n = "## 独立权项素材\n\nN1: 特征一\n描述\nN2: 特征二\n描述\n"
    f3 = extract_features(txt_n,
                          r"(?:必要(?:技术)?特征|独立权项素材)[^\n]*\n(.*?)(?=\n#{2,4}\s+[^#]|\Z)",
                          r"\*{0,2}(F\d+|N\d+)\*{0,2}\s*(?:·|[:：])\s*([^\n]+)")
    chk("N1: 形态提取条数", len(f3), 2)

    # 无特征段 → 空列表（不能瞎编）
    f4 = extract_features("## 其它章节\n\n随便些内容",
                          r"(?:必要(?:技术)?特征|独立权项素材)[^\n]*\n(.*?)(?=\n#{2,4}\s+[^#]|\Z)",
                          r"\*{0,2}(F\d+|N\d+)\*{0,2}\s*(?:·|[:：])\s*([^\n]+)")
    chk("无特征段 → 空列表", f4, [])

    # ── 3. 真实基线可解析 ──
    print("\n  ── 真实基线 ──")
    base = Path(__file__).parent.parent / "tests/baselines/l2-full-a01"
    dpath = base / "T-20261015-A06__disclosure-architect.md"
    cpath = base / "T-20261015-A07__patent-attorney-writer.md"
    if dpath.is_file() and cpath.is_file():
        dtext = dpath.read_text(encoding="utf-8")
        ctext = cpath.read_text(encoding="utf-8")
        feats = extract_features(
            dtext,
            r"(?:必要(?:技术)?特征|独立权项素材)[^\n]*\n(.*?)(?=\n#{2,4}\s+[^#]|\Z)",
            r"\*{0,2}(F\d+|N\d+)\*{0,2}\s*(?:·|[:：])\s*([^\n]+)")
        chk("A06 交底书解析出必要特征", len(feats) > 0, True)
        claim_sec = ctext[ctext.find("权利要求书"):]
        import re as _re
        m = _re.search(r"\*{0,2}1[\.、．]\*{0,2}\s*(.*?)(?=\*{0,2}2[\.、．]\*{0,2})",
                       claim_sec, _re.S)
        chk("A07 申请文件解析出独立权项1", m is not None, True)
    else:
        chk("L2 基线文件存在", False, True)

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    print("\n✅ 自测全通过")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disclosure"); ap.add_argument("--claims")
    ap.add_argument("--l2", action="store_true")
    ap.add_argument("--threshold", type=int, default=12)
    ap.add_argument("--self-test", action="store_true", help="判别力自测")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    if args.l2:
        base = Path(__file__).parent.parent / "tests/baselines/l2-full-a01"
        args.disclosure = args.disclosure or str(base / "T-20261015-A06__disclosure-architect.md")
        args.claims = args.claims or str(base / "T-20261015-A07__patent-attorney-writer.md")
    if not (args.disclosure and args.claims):
        ap.print_help(); return 2

    dtext = Path(args.disclosure).read_text(encoding="utf-8")
    ctext = Path(args.claims).read_text(encoding="utf-8")

    # 交底书必要特征：兼容 **F1 · 名称** / F1: 描述 / N1: 等三种格式
    feats = extract_features(
        dtext,
        r"(?:必要(?:技术)?特征|独立权项素材)[^\n]*\n(.*?)(?=\n#{2,4}\s+[^#]|\Z)",
        r"\*{0,2}(F\d+|N\d+)\*{0,2}\s*(?:·|[:：])\s*([^\n]+)")
    if not feats:
        print("⚠️ 交底书未解析出必要特征清单（检查段名 F\\d/N\\d 格式）"); return 2

    # 独立权项 1：从"权利要求书"起到权项2
    claim_sec = ctext[ctext.find("权利要求书"):]
    m = re.search(r"\*{0,2}1[\.、．]\*{0,2}\s*(.*?)(?=\*{0,2}2[\.、．]\*{0,2})", claim_sec, re.S)
    if not m:
        print("⚠️ 申请文件未解析出独立权项1"); return 2
    claim1 = re.sub(r"\s+", "", m.group(1))

    print(f"必要特征 {len(feats)} 条 × 独立权项1（{len(claim1)}字符）· LCS阈值≥{args.threshold}")
    missing = []
    for name, full in feats:
        norm = re.sub(r"\s+", "", full)
        lcs = longest_common_substring(norm, claim1)
        ok = len(lcs) >= args.threshold
        print(f"  {'✅' if ok else '❌'} {name}: LCS={len(lcs)} 「{lcs[:30]}」")
        if not ok:
            missing.append(name)

    if missing:
        print(f"\n❌ 超范围风险：{len(missing)} 条必要特征未映射到独立权项: {missing}")
        return 1
    print(f"\n✅ 全部必要特征已映射到独立权项")
    return 0

if __name__ == "__main__":
    sys.exit(main())
