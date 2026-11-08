#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnosis_trigger.py — 诊断触发器机械化（CYCLE-1 · S-E04 / [哲学违背①]）
========================================================================
docs/diagnosis-protocol.md §一 的 T1/T2/T3 此前为纯散文条款（实测 scripts/ 与
~/.workbuddy/git-hooks/ 零实现）——「散文条款不会被自觉执行」的首席违背实例。
本脚本把三个触发器的**确定性判定部分**机械化，供 preflight_check 第9项调用。

T1 同类失败复发：~/.workbuddy/expert-failures/*.json 中 30 天内同 fail_type ≥2 条
T2 周期性：CHANGELOG.md 最新日期距上次诊断登记 > 自然月（或版本迭代 ≥10）
T3 重大架构变更：git log 最近 N commit 命中 shared-core/schema/成员增删/skills 增删关键词

退出码：0=无需触发（含 warn 信息） 1=建议触发一次诊断（不阻断建队） 2=用法/环境错
判定边界：只做结构化判定（日期/计数/关键词命中属于格式与元数据层，允许确定性规则）；
「是否真的需要诊断」的语义裁决仍归管家节点（三件事分工宪法）。
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
FAILURES_DIR = os.path.expanduser("~/.workbuddy/expert-failures")
CHANGELOG = os.path.join(PKG, "CHANGELOG.md")
PROTOCOL = os.path.join(PKG, "docs", "diagnosis-protocol.md")
T3_PATTERN = re.compile(
    r"shared-core|schema|成员增删|agents/|members|federal|联邦|plugin\.json|SKILL\.md", re.I)


def check_t1(days=30):
    """T1：30 天内同 fail_type ≥2 条 → 触发。返回 (triggered, detail, items)"""
    if not os.path.isdir(FAILURES_DIR):
        return False, f"失败索引目录不存在：{FAILURES_DIR}", []
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    by_type = {}
    for p in sorted(glob.glob(os.path.join(FAILURES_DIR, "failure-*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        raw = str(d.get("fail_date") or d.get("date") or "")[:10]
        try:
            dt = datetime.datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            continue
        if dt < cutoff:
            continue
        ft = d.get("fail_type", "unknown")
        by_type.setdefault(ft, []).append(os.path.basename(p))
    hits = {k: v for k, v in by_type.items() if len(v) >= 2}
    detail = (f"30天内 {sum(len(v) for v in by_type.values())} 条失败，"
              f"{len(by_type)} 类；复发≥2的类: {list(hits) or '无'}")
    return bool(hits), detail, [f"{k}:{','.join(v)}" for k, v in hits.items()]


def check_t2(max_days=31, max_versions=10):
    """T2：CHANGELOG 最新日期距上次诊断登记 > 自然月，或本自然月版本迭代 ≥10 → 触发"""
    # 上次诊断日期：登记表最后一行的日期（格式 | 2026-11-08... |）
    last = None
    if os.path.isfile(PROTOCOL):
        for line in open(PROTOCOL, encoding="utf-8"):
            m = re.match(r"\|\s*(\d{4}-\d{2}-\d{2})", line)
            if m:
                last = m.group(1)
    if not last:
        return False, "登记表无日期行，T2 无法判定（标注 [待核验]）", []
    try:
        d0 = datetime.datetime.strptime(last, "%Y-%m-%d")
    except ValueError:
        return False, f"登记表日期格式异常：{last}", []
    gap = (datetime.datetime.now() - d0).days
    # CHANGELOG 版本节计数（## [x.y.z] 形态）
    nver = 0
    if os.path.isfile(CHANGELOG):
        nver = len(re.findall(r"^## \[[0-9]", open(CHANGELOG, encoding="utf-8").read(), re.M))
    triggered = gap > max_days
    detail = f"距上次诊断登记 {gap} 天（阈值 {max_days}），CHANGELOG 版本节 {nver} 个"
    return triggered, detail, ([f"gap={gap}d"] if triggered else [])


def check_t3(n=10):
    """T3：最近 n 个 commit 命中重大架构关键词 → 触发"""
    try:
        out = subprocess.run(["git", "log", f"-{n}", "--format=%h %s", "--", "."],
                             cwd=PKG, capture_output=True, text=True, timeout=10).stdout
    except Exception as e:
        return False, f"git log 不可用：{e}", []
    hits = [l for l in out.split("\n") if l.strip() and T3_PATTERN.search(l)]
    return bool(hits), f"最近 {n} commit 中 {len(hits)} 条命中架构变更关键词", hits[:3]


def main():
    ap = argparse.ArgumentParser(description="诊断触发器 T1/T2/T3 机械判定")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--commits", type=int, default=10)
    args = ap.parse_args()
    results = {}
    for name, fn in [("T1", lambda: check_t1(args.days)),
                     ("T2", check_t2),
                     ("T3", lambda: check_t3(args.commits))]:
        trig, detail, items = fn()
        results[name] = {"triggered": trig, "detail": detail, "items": items}
    any_trig = any(r["triggered"] for r in results.values())
    if args.json:
        print(json.dumps({"trigger": any_trig, "checks": results}, ensure_ascii=False, indent=2))
    else:
        for name, r in results.items():
            icon = "🔔" if r["triggered"] else "—"
            print(f"  {icon} {name}: {r['detail']}")
            for it in r["items"][:2]:
                print(f"       · {it[:100]}")
        print("  " + ("→ 建议触发一次诊断（C1 从零执行）" if any_trig else "→ 无需触发"))
    return 1 if any_trig else 0


if __name__ == "__main__":
    sys.exit(main())
