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


def validate_rows(rows):
    """台账行校验的**唯一真源**（CYCLE-1 · S-E64）。

    此前 cmd_verify() 与 cmd_self_test().probe() 各自复刻了一份判定逻辑：
      - 自测那份**少检了**「列数不符」「commit 为空」两条判据
      - 且它自己算自己、**从不调用真实判定函数** → 幽灵验证项形态 C（自指模拟）
      - 真实校验器改了，自测不跟随，仍报「全绿」
    现把判定抽为纯函数，verify 与 self-test 共同消费；改坏任一条判据，
    自测的对应探针必然失败（判别力验收见 cmd_self_test）。
    """
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
    return problems


def cmd_verify(args):
    problems = validate_rows(read_rows())
    if problems:
        for p in problems:
            print(f"  ❌ {p}")
        return 1
    print(f"✅ 台账校验通过：{len(read_rows())} 行，格式/时间序/无编造值/commit 确定")
    return 0


def cmd_tail(args):
    rows = read_rows()
    for r in rows[-args.n:]:
        print("\t".join(r[h] for h in HEADER))
    return 0


def cmd_self_test(args):
    """判别力自测（CYCLE-1 · S-E64 重写）。

    旧实现有**两个**缺陷，均由本轮第5轮排查实测暴露：
      1) 探针把违规样本 append 到真实 TSV 再自己复刻一份判定逻辑算 problems
         → **从未调用真实判定函数**（幽灵验证项形态 C）；且复刻版漏了两条判据。
      2) 四个探针都用固定时间戳 `2026-11-09T00:00:00`，而台账末行是
         `2026-11-09T14:06:52` → 每一行都触发「时间倒序」：
         · 合规样本被误判为违规 → **自测恒 FAIL（RC=1）**
         · 三个违规探针其实全靠「时间倒序」被检出，**没测到各自声称的判据**
           → 判别力假绿（把对应判据删掉，自测照样 PASS）

    现改为：
      - 判定统一走 `validate_rows()` 唯一真源（含 verify 的全部 5 类判据）
      - 纯内存构造行，**不写盘**（旧实现会临时污染真实台账）
      - 探针时间戳动态取「台账末行 + 1 秒」，保证不误触发时间倒序
      - 每个探针必须检出**自己那一条判据关键词**（不是「有问题就算过」）
      - 合规样本必须 `problems == []`
    """
    ok = True
    baseline = read_rows()

    # 基线本身必须干净，否则所有探针都会被既有问题污染 → 假绿
    base_problems = validate_rows(baseline)
    if base_problems:
        print("  ❌ 台账基线本身不合规，自测前提不成立：%s" % base_problems[:2])
        return 1
    print("  ✅ 台账基线干净（%d 行，validate_rows 零问题）" % len(baseline))

    # 动态时间戳：严格大于台账末行，避免「时间倒序」把探针全带走
    last_ts = baseline[-1]["timestamp"] if baseline else ""
    stamp = datetime.datetime.now().replace(microsecond=0)
    if last_ts:
        try:
            last = datetime.datetime.fromisoformat(last_ts)
            if stamp <= last:
                stamp = last + datetime.timedelta(seconds=1)
        except ValueError:
            pass
    ts = stamp.isoformat(timespec="seconds")

    def compliant_row(**overrides):
        """构造一行**完全合规**的台账行；overrides 只改被测的那一个字段。"""
        row = {"timestamp": ts, "commit": "abc1234", "skill": "system",
               "old_score": "-", "new_score": "实测分", "status": "keep",
               "dimension": "探针", "note": "探针", "eval_mode": "real",
               "gate": "全套门禁"}
        row.update(overrides)
        return row

    def probe(label, row, expect_fragment=None):
        """注入一行，断言**特定判据**被（或不被）检出。"""
        nonlocal ok
        problems = validate_rows(baseline + [row])
        # 只关心注入行产生的问题（基线已断言干净）
        hits = [p for p in problems if expect_fragment and expect_fragment in p]
        if expect_fragment:
            passed = bool(hits)
            print("  %s %-38s 期望命中「%s」 | 实得 %s"
                  % ("✅" if passed else "❌", label, expect_fragment,
                     hits[0] if hits else "未命中（problems=%s）" % problems[:2]))
        else:
            passed = (len(problems) == 0)
            print("  %s %-38s 期望零问题 | 实得 %s"
                  % ("✅" if passed else "❌", label,
                     "零问题" if passed else problems[:2]))
        if not passed:
            ok = False

    print("== 自测：台账校验器判别力（唯一真源 validate_rows）==")
    probe("合规样本（动态时间戳 %s）" % ts, compliant_row())
    probe("注入 commit=HEAD 非确定标识",
          compliant_row(commit="HEAD"), "非确定标识")
    probe("注入 commit 为空",
          compliant_row(commit=""), "commit 为空")
    probe("注入 commit 非 hex hash",
          compliant_row(commit="XYZ-NOT-HEX"), "非 hex hash")
    probe("注入 eval_mode=real 却无实测分",
          compliant_row(new_score="-"), "却无实测分")
    probe("注入时间倒序",
          compliant_row(timestamp="2000-01-01T00:00:00"), "时间倒序")
    probe("注入列数不符（缺 gate 列）",
          {k: v for k, v in compliant_row().items() if k != "gate"}, "列数不符")

    # 不写盘复核：自测全程未触碰台账
    if read_rows() != baseline:
        print("  ❌ 自测污染了台账")
        ok = False
    else:
        print("  ✅ 台账未被写盘（纯内存探针）")
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
