#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_triz_data.py — TRIZ 权威数据自检（2026-10-14 建立，防 failure-001/007 类复发）

背景：本专家团两次栽在"权威数据表被写错但无人发现"——
  - failure-001：速查表 12 条全部与权威矛盾矩阵不符（0/12），实测才发现；
  - failure-007：39 参数中文表的 #34/#35 译名错填为 #36/#37 的译名，
    且 query_triz_matrix.py 会把译名直接打进查询结果，错误一路注入成员上下文。
两者共同点：数据表无自动化校验，错误只能靠"某次运行时碰巧撞上"暴露。

本脚本把"数据表自身成立"变成可机械校验的不变量，供改数据后与 CI 门禁调用。

检查项：
  A. 矛盾矩阵 CSV：行数 == 1521（39×39），行号 1..39，列数正确
  B. 39 参数英文 CSV：39 行，编号 1..39 连续无缺
  C. 39 参数中文表：39 行，编号 1..39 连续无缺；英文列与 CSV 逐行一致；
     中文译名不得重复（重复 = 错位/复制粘贴的典型指纹）
  D. 抽样锚点：已知权威交叉点复算（01×03 → IP 15,8,29,34；14×02 → IP 40,26,27,1）

用法：
  python3 scripts/verify_triz_data.py [--expert-dir DIR] [--strict]
退出码：0=全通过  1=存在错误

CYCLE-1 第2轮交叉验证发现：--strict 此前是**死参数**（解析后从未被读取，存在错误时
无论是否 strict 都返回 1）。现明确其语义：
  - 默认模式：errors → exit 1；仅有 warns → exit 0（warn 不阻断）
  - --strict：errors 或 warns 任一非空 → exit 1（warn 也阻断·CI 口径）
"""

import argparse
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
REF = os.path.join(PKG, "skills", "triz-matrix", "references")

MATRIX_CSV = os.path.join(REF, "Altshuller_Contradiction_Matrix.csv")
PARAMS_CSV = os.path.join(REF, "Altshuller_39_Parameters.csv")
PARAMS_ZH = os.path.join(REF, "Altshuller_39_Parameters_zh.md")

# 已知权威锚点（(improve, worsen) -> 期望原理编号集合），来源：Altshuller 原版矩阵交叉核对
ANCHORS = [
    (1, 3, {15, 8, 29, 34}),
    (14, 2, {40, 26, 27, 1}),
]

errors = []
warns = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warns.append(msg)


def check_matrix():
    """矩阵 CSV 为长表格式：Improving Parameter, Worsening Parameter, Inventive Principles
    （表头 1 行 + 39×39 = 1521 数据行）。不做网格假设——按实际格式校验。"""
    if not os.path.isfile(MATRIX_CSV):
        err("A. 矛盾矩阵 CSV 缺失：%s" % MATRIX_CSV)
        return {}
    with open(MATRIX_CSV, encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        err("A. 矩阵 CSV 为空")
        return {}
    head = [c.strip().lower() for c in rows[0]]
    if "inventive principles" not in head:
        err("A. 矩阵 CSV 表头异常，未找到 Inventive Principles 列：%s" % rows[0])
        return {}
    data = [r for r in rows[1:] if r and re.match(r"^\s*\d{1,2}\b", r[0])]
    if len(data) != 1521:
        err("A. 矩阵数据行 %d ≠ 1521（39×39）" % len(data))
    # 每个改善参数必须恰好出现 39 次
    cnt = {}
    for r in data:
        n = int(re.match(r"\s*(\d+)", r[0]).group(1))
        cnt[n] = cnt.get(n, 0) + 1
    bad = {k: v for k, v in cnt.items() if v != 39}
    missing = sorted(set(range(1, 40)) - set(cnt))
    if missing:
        err("A. 改善参数缺号：%s" % missing)
    if bad:
        err("A. 改善参数出现次数≠39：%s" % bad)
    # 建索引：(improve, worsen) -> 原理单元格文本
    idx = {}
    for r in data:
        i = int(re.match(r"\s*(\d+)", r[0]).group(1))
        w = int(re.match(r"\s*(\d+)", r[1]).group(1))
        idx[(i, w)] = r[2] if len(r) > 2 else ""
    dup = len(idx)
    if dup != 1521:
        err("A. 交叉点去重后 %d ≠ 1521（存在重复交叉点）" % dup)
    return idx


def check_params_en():
    if not os.path.isfile(PARAMS_CSV):
        err("B. 参数英文 CSV 缺失：%s" % PARAMS_CSV)
        return {}
    out = {}
    for r in csv.reader(open(PARAMS_CSV, encoding="utf-8")):
        if r and r[0].strip().isdigit():
            out[int(r[0])] = r[1].strip()
    if len(out) != 39:
        err("B. 参数英文 CSV 行数 %d ≠ 39" % len(out))
    missing = sorted(set(range(1, 40)) - set(out))
    if missing:
        err("B. 参数编号缺失：%s" % missing)
    return out


def check_params_zh(en_map):
    if not os.path.isfile(PARAMS_ZH):
        err("C. 参数中文表缺失：%s" % PARAMS_ZH)
        return
    zh = {}
    for line in open(PARAMS_ZH, encoding="utf-8"):
        m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line.strip())
        if m:
            zh[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip())
    if len(zh) != 39:
        err("C. 中文表行数 %d ≠ 39" % len(zh))
    missing = sorted(set(range(1, 40)) - set(zh))
    if missing:
        err("C. 中文表编号缺失：%s" % missing)
    # 英文列必须与 CSV 一致（failure-007 的入口就是编号与译名脱钩）
    for i in sorted(zh):
        if i in en_map and zh[i][0].lower() != en_map[i].lower():
            err("C. #%d 英文列不一致：表=%r  CSV=%r" % (i, zh[i][0], en_map[i]))
    # 中文译名重复 = 错位/复制粘贴指纹（failure-007 直接命中）
    seen = {}
    for i, (_, cn) in sorted(zh.items()):
        seen.setdefault(cn, []).append(i)
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    if dup:
        err("C. 中文译名重复（疑似错位）：%s" % dup)


def check_anchors(matrix):
    """用已知权威交叉点复算，防整表被替换/错位而行数仍对得上。"""
    if not matrix:
        return
    for imp, wor, expect in ANCHORS:
        cell = matrix.get((imp, wor))
        if cell is None:
            err("D. 锚点 %d×%d 交叉点缺失" % (imp, wor))
            continue
        got = {int(n) for n in re.findall(r"\d+", cell)}
        if not expect.issubset(got):
            err("D. 锚点 %d×%d 不匹配：期望含 %s，实际 %r" % (imp, wor, sorted(expect), cell))


def main():
    global PKG, REF, MATRIX_CSV, PARAMS_CSV, PARAMS_ZH
    ap = argparse.ArgumentParser(description="TRIZ 权威数据自检")
    ap.add_argument("--expert-dir", default=PKG)
    ap.add_argument("--strict", action="store_true", help="有错即非 0 退出（CI 用）")
    args = ap.parse_args()

    if args.expert_dir != PKG:
        PKG = os.path.abspath(args.expert_dir)
        REF = os.path.join(PKG, "skills", "triz-matrix", "references")
        MATRIX_CSV = os.path.join(REF, "Altshuller_Contradiction_Matrix.csv")
        PARAMS_CSV = os.path.join(REF, "Altshuller_39_Parameters.csv")
        PARAMS_ZH = os.path.join(REF, "Altshuller_39_Parameters_zh.md")

    print("🔍 TRIZ 权威数据自检 — ref=%s" % REF)
    matrix = check_matrix()
    en_map = check_params_en()
    check_params_zh(en_map)
    check_anchors(matrix)

    for w in warns:
        print("  ⚠️  %s" % w)
    if errors:
        print("  ❌ 发现 %d 项错误：" % len(errors))
        for e in errors:
            print("     - %s" % e)
        print("\n结论：权威数据不通过。改动数据表后必须修复到 0 错误再提交。")
        return 1
    # CYCLE-1 第2轮交叉验证：--strict 此前是死参数（从未被读取）。现赋予明确语义——
    # strict 下 warn 也阻断（CI 口径），默认模式 warn 不阻断。
    if args.strict and warns:
        print("\n结论：--strict 严格模式——无错误但有 %d 项警告，按严格口径拒绝放行。" % len(warns))
        return 1
    print("  ✅ A 矩阵1521行 / B 参数39行 / C 中文表编号+译名一致无重复 / D 权威锚点复算通过")
    print("结论：权威数据全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
