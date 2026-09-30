#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRIZ 矛盾矩阵查询器（确定性工程 · 防幻觉）
============================================
用途：用 Altshuller 39×39 完整矩阵（1521 交叉点）做确定性查询，
      替代 LLM 凭训练记忆生成原理编号（后者是 failure-001 的根因）。

权威数据源：
  skills/triz-matrix/references/Altshuller_Contradiction_Matrix.csv (1521行)
  skills/triz-matrix/references/Altshuller_39_Parameters.csv (39参数)
  来源：jenson500/triz-prompt-engineering（与 deepwiki/studyraid 独立交叉验证一致）

用法：
  # 列出39参数（编号+英文+中文对照）
  python3 query_triz_matrix.py --list-params

  # 按编号查询（推荐·零歧义）
  python3 query_triz_matrix.py --improve 14 --worsen 2

  # 按关键词查询（英文匹配参数名）
  python3 query_triz_matrix.py --improve strength --worsen weight

  # 批量查询（每行 "改善,恶化" 编号）
  python3 query_triz_matrix.py --batch pairs.txt

退出码：
  0 = 查到推荐原理
  1 = 查到但该交叉点无推荐原理（no preferred / see physical contradiction）
  2 = 参数无法识别
  3 = 数据文件缺失
"""

import argparse
import csv
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERT_DIR = os.path.dirname(SCRIPT_DIR)
REF_DIR = os.path.join(EXPERT_DIR, "skills", "triz-matrix", "references")
MATRIX_CSV = os.path.join(REF_DIR, "Altshuller_Contradiction_Matrix.csv")
PARAMS_CSV = os.path.join(REF_DIR, "Altshuller_39_Parameters.csv")
ZH_MD = os.path.join(REF_DIR, "Altshuller_39_Parameters_zh.md")


def log(msg: str) -> None:
    print(f"[query_triz_matrix] {msg}", file=sys.stderr)


def load_params():
    """返回 {编号(int): 英文名} 与 {编号: 中文名}"""
    if not os.path.isfile(PARAMS_CSV):
        log(f"❌ 参数表缺失：{PARAMS_CSV}")
        sys.exit(3)
    en, zh = {}, {}
    with open(PARAMS_CSV, encoding="utf-8") as f:
        for r in list(csv.reader(f))[1:]:
            if len(r) >= 2 and r[0].strip():
                n = int(re.sub(r"\D", "", r[0]))
                en[n] = r[1].strip()
    if os.path.isfile(ZH_MD):
        for line in open(ZH_MD, encoding="utf-8"):
            m = re.match(r"\|\s*(\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
            if m:
                zh[int(m.group(1))] = m.group(3)
    return en, zh


def load_matrix():
    """返回 {(improve:int, worsen:int): (raw_str, [ip:int,...])}"""
    if not os.path.isfile(MATRIX_CSV):
        log(f"❌ 矩阵数据缺失：{MATRIX_CSV}")
        sys.exit(3)
    m = {}
    with open(MATRIX_CSV, encoding="utf-8") as f:
        for r in list(csv.reader(f))[1:]:
            if len(r) < 3:
                continue
            ni = re.match(r"(\d+)", r[0])
            nw = re.match(r"(\d+)", r[1])
            if not ni or not nw:
                continue
            ips = [int(x) for x in re.findall(r"IP #(\d+)", r[2])]
            m[(int(ni.group(1)), int(nw.group(1)))] = (r[2].strip(), ips)
    return m


def resolve_param(token: str, en: dict):
    """编号或英文关键词 → 编号(int)；失败返回 None"""
    t = token.strip()
    if t.isdigit():
        n = int(t)
        return n if n in en else None
    # 关键词匹配（大小写无关·子串）
    hits = [n for n, name in en.items() if t.lower() in name.lower()]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        log(f"⚠️ '{token}' 匹配多个参数：{[(h, en[h]) for h in hits]}，请用编号")
        return None
    return None


def query(matrix, ni, nw, en, zh):
    raw, ips = matrix.get((ni, nw), (None, []))
    imp = f"#{ni} {en.get(ni,'?')}" + (f"（{zh[ni]}）" if ni in zh else "")
    wor = f"#{nw} {en.get(nw,'?')}" + (f"（{zh[nw]}）" if nw in zh else "")
    print(f"矛盾：改善 {imp}  ↔  恶化 {wor}")
    if raw is None:
        print("  查询结果：该组合不在矩阵范围内（编号须在1-39）")
        return 2
    if ips:
        print(f"  推荐原理：{', '.join('#%d' % i for i in ips)}")
        print(f"  （原文：{raw}）")
        return 0
    print(f"  本交叉点无推荐原理：{raw}")
    print("  → 按 skill 降级路径：转物理矛盾+四大分离原理处理")
    return 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--list-params", action="store_true", help="列出39工程参数")
    ap.add_argument("--improve", help="改善参数（编号或英文关键词）")
    ap.add_argument("--worsen", help="恶化参数（编号或英文关键词）")
    ap.add_argument("--batch", help="批量查询文件（每行 '改善,恶化'）")
    args = ap.parse_args()

    en, zh = load_params()

    if args.list_params:
        print(f"{'#':<4}{'English':<42}中文对照")
        print("-" * 78)
        for n in sorted(en):
            print(f"{n:<4}{en[n]:<42}{zh.get(n,'')}")
        return 0

    matrix = load_matrix()

    if args.batch:
        if not os.path.isfile(args.batch):
            log(f"❌ 批量文件不存在：{args.batch}")
            return 3
        rc = 0
        for line in open(args.batch, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            ni = resolve_param(parts[0], en)
            nw = resolve_param(parts[1], en)
            if ni is None or nw is None:
                print(f"跳过（参数无法识别）：{line}")
                rc = max(rc, 2)
                continue
            r = query(matrix, ni, nw, en, zh)
            rc = max(rc, r)
            print()
        return rc

    if not args.improve or not args.worsen:
        log("❌ 需同时提供 --improve 与 --worsen（或用 --list-params / --batch）")
        return 2

    ni = resolve_param(args.improve, en)
    nw = resolve_param(args.worsen, en)
    if ni is None:
        log(f"❌ 无法识别改善参数：{args.improve}")
        return 2
    if nw is None:
        log(f"❌ 无法识别恶化参数：{args.worsen}")
        return 2
    return query(matrix, ni, nw, en, zh)


if __name__ == "__main__":
    sys.exit(main())
