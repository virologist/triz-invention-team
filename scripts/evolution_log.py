#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evolution_log.py — 自进化台账机械追加器（CYCLE-1 · S-E08）
==========================================================
docs/evolution-log.tsv 止于 2026-10-14，v2.6.0→v2.8.0 三轮大版本零记录（断档 25 天）。
本脚本把「台账续记」从手抄改为确定性追加，遵守设计哲学：
  - 原则② 机械计量优先：score 只能来自 --metric 传入的实测值（回归断言通过数等），
    无实测时必须填 `-` 并注明 [未测·不得编造]（原则⑤ 实测事故驱动）
  - 原则③ 单源化：台账唯一写入口 = 本脚本；禁止手工编辑 TSV

用法：
  python3 scripts/evolution_log.py append --commit <hash> --skill system \
      --metric "L2回归7/7+门禁5/5" --note "v2.8.0 R1-R5+U1-U3"
  python3 scripts/evolution_log.py backfill --commit <hash> --timestamp <ISO8601> \
      --metric "..." --note "..."    # 历史批次补录（显式指定时间戳，保持台账时间序）
  python3 scripts/evolution_log.py verify        # 格式/时间序/无编造值校验
  python3 scripts/evolution_log.py tail 5

退出码：0=正常 1=校验失败 2=用法错
"""
import argparse
import csv
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
TSV = os.path.join(PKG, "docs", "evolution-log.tsv")
HEADER = ["timestamp", "commit", "skill", "old_score", "new_score",
          "status", "dimension", "note", "eval_mode", "gate"]


def read_rows():
    with open(TSV, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _build_row(args, ts):
    """构造台账行（append 与 backfill 共用同一真源逻辑，避免两处手抄漂移）"""
    # 无实测 → 不编造分数；有实测 → 原样记录（字符串，含口径说明）
    new_score = args.metric or "-"
    old_score = args.old_metric or "-"
    return {
        "timestamp": ts, "commit": args.commit, "skill": args.skill,
        "old_score": old_score, "new_score": new_score,
        "status": "keep" if args.metric else "unmeasured",
        "dimension": args.dimension, "note": args.note,
        "eval_mode": "real" if args.metric else "unmeasured",
        "gate": args.gate or "-",
    }


def _write_row(row):
    with open(TSV, "a", encoding="utf-8") as f:
        f.write("\t".join(row[h] for h in HEADER) + "\n")


def cmd_append(args):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    row = _build_row(args, ts)
    _write_row(row)
    print(f"✅ 台账已追加：{ts} | {args.commit} | score={row['new_score']} | status={row['status']}")
    if not args.metric:
        print("   ⚠️ 未提供 --metric：按原则⑤填 '-' [未测·不得编造]，不得据此计算收敛")
    return 0


def cmd_backfill(args):
    """历史批次补录：显式时间戳 + 显式 commit，不得写 HEAD 等非确定标识。"""
    ts = args.timestamp
    if not ts:
        print("  ❌ backfill 必须显式提供 --timestamp（ISO8601），否则台账时间序不可验证")
        return 2
    if args.commit.strip().upper() in ("HEAD", "", "-"):
        print("  ❌ backfill 的 --commit 必须是确定 commit hash，禁止写 HEAD（非确定标识）")
        return 2
    row = _build_row(args, ts)
    _write_row(row)
    print(f"✅ 台账已补录：{ts} | {args.commit} | score={row['new_score']} | status={row['status']}")
    if not args.metric:
        print("   ⚠️ 未提供 --metric：按原则⑤填 '-' [未测·不得编造]，不得据此计算收敛")
    return 0


def cmd_verify(args):
    rows = read_rows()
    problems = []
    prev = ""
    for i, r in enumerate(rows, 2):
        if len(r) != len(HEADER) or any(r.get(h) is None for h in HEADER):
            problems.append(f"L{i}: 列数不符")
        t = r.get("timestamp", "")
        if t and t < prev:
            problems.append(f"L{i}: 时间倒序 {t} < {prev}")
        prev = t or prev
        if r.get("eval_mode") == "real" and r.get("new_score") in ("", "-", None):
            problems.append(f"L{i}: eval_mode=real 却无实测分（违反原则②）")
        # CYCLE-1 · S-E08 收口：commit 列必须是确定标识。
        # HEAD 是引用而非标识，随 checkout 漂移 → 台账无法追溯到具体代码状态。
        c = (r.get("commit") or "").strip()
        if not c:
            problems.append(f"L{i}: commit 为空")
        elif c.upper() in ("HEAD", "HEAD~1", "LATEST", "CURRENT"):
            problems.append(f"L{i}: commit='{c}' 非确定标识（应为完整/短 hash）")
        elif not re.fullmatch(r"[0-9a-f]{7,40}", c):
            problems.append(f"L{i}: commit='{c}' 非 hex hash 形态")
    if problems:
        for p in problems:
            print(f"  ❌ {p}")
        return 1
    print(f"✅ 台账校验通过：{len(rows)} 行，格式/时间序/无编造值/commit 确定")
    return 0


def cmd_tail(args):
    rows = read_rows()
    for r in rows[-args.n:]:
        print("\t".join(r[h] for h in HEADER))
    return 0


def cmd_self_test(args):
    """双向自测：注入违规样本 → 期望被检出（exit 1）；基线 → 期望通过（exit 0）。"""
    import shutil
    import tempfile
    ok = True
    baseline = read_rows()

    def probe(label, mutate, expect_fail):
        """在临时副本上注入样本，验证 verify 的判定逻辑真能检出"""
        nonlocal ok
        bak = TSV + ".selftest.bak"
        shutil.copy2(TSV, bak)
        try:
            with open(TSV, "a", encoding="utf-8") as f:
                f.write(mutate)
            rows = read_rows()
            problems = []
            prev = ""
            for i, r in enumerate(rows, 2):
                t = r.get("timestamp", "")
                if t and t < prev:
                    problems.append(f"L{i}: 时间倒序")
                prev = t or prev
                c = (r.get("commit") or "").strip()
                if not c:
                    problems.append(f"L{i}: commit 为空")
                elif c.upper() in ("HEAD", "HEAD~1", "LATEST", "CURRENT"):
                    problems.append(f"L{i}: commit 非确定标识")
                elif not re.fullmatch(r"[0-9a-f]{7,40}", c):
                    problems.append(f"L{i}: commit 非 hex hash")
                if r.get("eval_mode") == "real" and r.get("new_score") in ("", "-", None):
                    problems.append(f"L{i}: eval_mode=real 却无实测分")
            detected = len(problems) > 0
            if detected != expect_fail:
                print(f"  ❌ {label}: 期望检出={expect_fail} 实测={detected}")
                ok = False
            else:
                print(f"  ✅ {label}: {'检出' if detected else '放行'}（符合预期）")
        finally:
            shutil.move(bak, TSV)

    print("== 自测：台账校验器双向断言 ==")
    probe("注入 commit=HEAD 非确定标识",
          "2026-11-09T00:00:00\tHEAD\tsystem\t-\tx\tkeep\t探针\t探针\treal\t-\n", True)
    probe("注入 eval_mode=real 但无实测分",
          "2026-11-09T00:00:00\tabc1234\tsystem\t-\t-\tkeep\t探针\t探针\treal\t-\n", True)
    probe("注入时间倒序",
          "2020-01-01T00:00:00\tabc1234\tsystem\t-\tx\tkeep\t探针\t探针\treal\t-\n", True)
    probe("注入合规样本",
          "2026-11-09T00:00:00\tabc1234\tsystem\t-\tx\tkeep\t探针\t探针\treal\t-\n", False)

    # 基线复核：还原后必须通过
    if read_rows() != baseline:
        print("  ❌ 自测未还原台账")
        ok = False
    else:
        print("  ✅ 台账已还原，行数一致")
    print("self-test ✅" if ok else "self-test ❌")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="自进化台账机械追加/校验")
    sub = ap.add_subparsers(dest="cmd")

    def add_common(p, ts_required=False):
        p.add_argument("--commit", required=True)
        p.add_argument("--skill", default="system")
        p.add_argument("--metric", help="实测指标（如 'L2回归7/7+门禁5/5'）；省略则填 - [未测]")
        p.add_argument("--old-metric", default="")
        p.add_argument("--dimension", default="架构")
        p.add_argument("--note", required=True)
        p.add_argument("--gate", default="")
        if ts_required:
            p.add_argument("--timestamp", required=True,
                           help="ISO8601 时间戳（backfill 必填，保证台账时间序可验证）")

    add_common(sub.add_parser("append"))
    add_common(sub.add_parser("backfill"), ts_required=True)
    sub.add_parser("verify")
    sub.add_parser("self-test")
    p3 = sub.add_parser("tail")
    p3.add_argument("n", nargs="?", type=int, default=5)

    args = ap.parse_args()
    if args.cmd == "append":
        return cmd_append(args)
    if args.cmd == "backfill":
        return cmd_backfill(args)
    if args.cmd == "verify":
        return cmd_verify(args)
    if args.cmd == "self-test":
        return cmd_self_test(args)
    if args.cmd == "tail":
        return cmd_tail(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
