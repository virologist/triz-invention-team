#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cost_profile.py — 成本画像：聚合 metrics.jsonl → 成员×阶段经验表（U1 · 2026-11-07 升维）
================================================================================
把散落在 tests/baselines/**/metrics.jsonl（及未来 outputs/ 运行目录） 的逐次计量聚合成「成员维度成本经验表」，
供 preflight 预算估算与主理人路由决策引用（贵的成员少派 / 快的路径优先 / P90 做预算线）。

设计约定：
  - 输入只认 metrics.jsonl（token_budget_check --meter --ledger 的台账，机械计量口径）
  - 同 (task_id, member) 多行时取**最后一次** metered_at（重试会重复计量，以最新为准）
  - phase 从 task_id 无法推导（A01/A02 是 Phase1-2/迭代），phase 维度仅按需展示，主维度=成员
  - 墙钟缺失（flags 含「墙钟未回填」）不计入耗时统计，单独登记覆盖率

用法：
  python3 scripts/cost_profile.py                     # 聚合全部 outputs/**/metrics.jsonl
  python3 scripts/cost_profile.py --run-dir tests/baselines
  python3 scripts/cost_profile.py --json              # 机器可读（preflight 可消费）
  python3 scripts/cost_profile.py --member patent-search-scout   # 单成员明细

退出码：0=正常 1=无数据 2=用法错
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)


def _pct(sorted_vals, p):
    """P90 等分位数（nearest-rank 简化实现）"""
    if not sorted_vals:
        return None
    idx = max(0, min(len(sorted_vals) - 1, round(p / 100 * (len(sorted_vals) + 1)) - 1))
    return sorted_vals[idx]


def load_ledgers(run_dir=None):
    """读全部 metrics.jsonl，按 (task_id, member) 去重取最新。"""
    if run_dir:
        paths = glob.glob(os.path.join(run_dir, "**", "metrics.jsonl"), recursive=True)
    else:
        # 默认扫描归档基线 + 未来运行目录（2026-11-08 outputs→baselines 迁移跟随）
        paths = glob.glob(os.path.join(PKG, "tests", "baselines", "**", "metrics.jsonl"), recursive=True)
        paths += glob.glob(os.path.join(PKG, "outputs", "**", "metrics.jsonl"), recursive=True)
    latest = {}  # (task, member) -> row
    for path in sorted(paths):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            key = (row.get("task_id", "?"), row.get("member", "?"))
            prev = latest.get(key)
            if prev is None or str(row.get("metered_at", "")) >= str(prev.get("metered_at", "")):
                row["_src"] = os.path.relpath(path, PKG)
                latest[key] = row
    return list(latest.values())


def build_profile(rows):
    """按成员聚合：n / out_tokens 均值·中位·P90 / wall 均值·P90 / 成功率 / 墙钟覆盖率。"""
    by_member = {}
    for r in rows:
        by_member.setdefault(r["member"], []).append(r)
    profile = {}
    for member, items in sorted(by_member.items()):
        tokens = sorted(x.get("out_tokens_est") or 0 for x in items)
        walls = sorted(x.get("duration_ms_wall") or 0 for x in items)
        wall_valid = [w for w in walls if w > 0]
        n = len(items)
        ok = sum(1 for x in items if x.get("status") == "success")
        profile[member] = {
            "n": n,
            "success_rate": round(ok / n, 2) if n else None,
            "out_tokens": {
                "mean": int(sum(tokens) / n) if n else None,
                "median": tokens[n // 2] if n else None,
                "p90": _pct(tokens, 90),
            },
            "wall_s": {
                "mean": int(sum(wall_valid) / len(wall_valid) / 1000) if wall_valid else None,
                "p90": int(_pct(wall_valid, 90) / 1000) if wall_valid else None,
                "coverage": f"{len(wall_valid)}/{n}",
            },
            "tasks": sorted({x.get("task_id") for x in items}),
        }
    return profile


def main():
    ap = argparse.ArgumentParser(description="成员成本画像（metrics.jsonl 聚合）")
    ap.add_argument("--run-dir", help="限定单个运行目录")
    ap.add_argument("--member", help="单成员明细（含逐任务行）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = load_ledgers(args.run_dir)
    if not rows:
        print("无 metrics.jsonl 台账可聚合（先跑 token_budget_check --meter --ledger）")
        return 1

    profile = build_profile(rows)

    if args.json:
        print(json.dumps(profile, ensure_ascii=False, indent=2))
        return 0

    print(f"📊 成员成本画像（{len(rows)} 条计量 · 去重后按最新）\n")
    print(f"{'成员':<26}{'n':>3}{'成功率':>7}{'tokens均值':>10}{'tokens P90':>11}{'墙钟均值s':>10}{'墙钟P90s':>9}{'墙钟覆盖':>9}")
    for m, p in profile.items():
        print(f"{m:<26}{p['n']:>3}{p['success_rate'] or 0:>7}"
              f"{p['out_tokens']['mean'] or 0:>10}{p['out_tokens']['p90'] or 0:>11}"
              f"{p['wall_s']['mean'] or 0:>10}{p['wall_s']['p90'] or 0:>9}"
              f"{p['wall_s']['coverage']:>9}")
    total_p90 = sum((p['out_tokens']['p90'] or p['out_tokens']['mean'] or 0) for p in profile.values())
    print(f"\nΣ 成员 tokens P90 合计 ≈ {total_p90 / 1000:.1f}K"
          f"（对照 H3.5 弹性上限 120K / L2 实测基线 84K——超限则裁剪范围或降级 Workflow）")

    if args.member:
        print(f"\n—— {args.member} 逐任务明细 ——")
        for r in sorted((x for x in rows if x['member'] == args.member), key=lambda x: str(x.get('metered_at'))):
            wall = r.get('duration_ms_wall')
            print(f"  {r['task_id']}  tokens={r.get('out_tokens_est')}  "
                  f"wall={'%.0fs' % (wall / 1000) if wall else '—'}  status={r.get('status')}"
                  f"  flags={','.join(r.get('flags') or []) or '无'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
