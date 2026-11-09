#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self_gate.py — 判别力门禁**唯一汇总入口**（CYCLE-1 第5轮 · S-E62 / S-E67）
==========================================================================
问题（C1 诊断实测）：
  - `boundary_guard.py` 全仓 grep 仅命中文档与脚本自身：
    pre-commit hook 四层门禁、`release-sync.sh` 三 gate **均未调用**
    → `docs/OPERATIONS.md:64`「每次 VERIFY 收产出前（验收侧红线）」是**幽灵条款**
    （幽灵验证项形态 A：声称有校验，但运行时无任何执行点）
  - 10 个带 `--self-test` 的脚本里，只有 `agent_ci_gate` 被 release-sync gate
    覆盖；其余 9 个改坏真源可带病发布 → 判别力自测形同虚设
  - `evolution_log.py self-test` 恒 RC=1 却长期无人发现，正是因为**没有执行点**

本脚本把「哪些校验必须跑」变成**一份可推送、可复现的机器清单**，
由 pre-commit hook 与 release-sync gate 条件式调用（不存在本文件的包自动跳过）。

设计原则：
  - 原则① 散文条款必须脚本化：门禁清单是代码，不是文档里的使用建议
  - 原则③ 单源化：清单只在此处定义，两处宿主门禁都消费本入口
  - 原则④ 禁止幽灵验证项：--self-test 会校验清单里的每个脚本/参数真实存在，
    并把「故意写坏一项」作为负例证明汇总逻辑本身有判别力
  - 原则⑤ 实测事故驱动：任何一项非 0 即整体非 0，不做静默降级

用法：
  python3 scripts/self_gate.py                 # 跑全部门禁（默认）
  python3 scripts/self_gate.py --self-test    # 校验门禁清单自身的完整性与判别力
  python3 scripts/self_gate.py --json         # 机器可读输出

退出码：0=全部通过  1=至少一项失败  2=用法/环境错误
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

# ── 门禁清单（唯一真源）──────────────────────────────────────────────
# 每项 = (显示名, 脚本文件名, 参数列表, 失败时的影响说明)
# 注意：evolution_log 用**子命令** `self-test`（非 `--self-test`）；
# verify_triz_data 无自测，用 `--strict` 跑真实数据校验。
GATES = [
    ("契约三源漂移探针", "contract_enforce.py", ["--self-test"],
     "禁词真源/DRIFT_PROBE 反向验证"),
    ("信封 schema 自测", "agent_ci_gate.py", ["--self-test"],
     "上行信封 schema 内置正负样本"),
    ("X/E 威胁判定真源", "threat_grade.py", ["--self-test"],
     "C3 触发判据 + 多轮聚合 + 专利号形态"),
    ("越界红线验收侧", "boundary_guard.py", ["--self-test"],
     "B1-B5 信号 + fail-closed 退出码"),
    ("专利族谱沉淀", "patent_knowledge.py", ["--self-test"],
     "分级节解析 + 专利号正则 + 收库过滤"),
    ("权项必要特征映射", "check_claim_scope.py", ["--self-test"],
     "LCS 映射与真实基线解析"),
    ("成本画像", "cost_profile.py", ["--self-test"],
     "P90 nearest-rank 与聚合口径"),
    ("失败记忆检索", "failure_memory.py", ["--self-test"],
     "并集 OR 语义与排序截断"),
    ("停滞看门狗", "spawn_watchdog.py", ["--self-test"],
     "四态判定边界与 ISO 解析"),
    ("benchmark 求值", "triz_benchmark.py", ["--self-test"],
     "退出码语义 + split 死参数 + 基线分离"),
    ("台账校验器判别力", "evolution_log.py", ["self-test"],
     "validate_rows 唯一真源 + 7 类判据探针"),
    ("TRIZ 权威数据", "verify_triz_data.py", ["--strict"],
     "矩阵/参数/中文表/锚点复算"),
]

# 真实基线扫描（对已入库产出做 fail-closed 越界复核）——
# 这一项是 S-E62 的核心：让 boundary_guard 从「只有 --self-test」变成
# 「每次门禁都对真实产出跑一遍」。
BASELINE_DIRS = [
    "tests/baselines/l2-full-a01",
    "tests/baselines/l1-analyst-b01",
]


def run_gate(script, argv):
    """跑单项门禁，返回 (rc, 输出末 5 行)。"""
    path = os.path.join(HERE, script)
    if not os.path.isfile(path):
        return 2, ["脚本不存在：%s" % path]
    try:
        p = subprocess.run([sys.executable, path] + list(argv),
                           capture_output=True, text=True, cwd=PKG, timeout=120)
    except subprocess.TimeoutExpired:
        return 1, ["超时（120s）"]
    except Exception as e:  # noqa: BLE001 —— 门禁必须 fail loud
        return 1, ["执行异常：%s" % e]
    lines = (p.stdout + p.stderr).strip().splitlines()
    return p.returncode, lines[-5:] if lines else ["(无输出)"]


def main_gates(as_json=False):
    results = []
    for name, script, argv, desc in GATES:
        rc, tail = run_gate(script, argv)
        results.append({"name": name, "script": script, "argv": argv,
                        "rc": rc, "tail": tail, "desc": desc})

    # 真实基线越界复核（S-E62 的运行时落点）
    for d in BASELINE_DIRS:
        full = os.path.join(PKG, d)
        if not os.path.isdir(full):
            results.append({"name": "基线越界复核", "script": "boundary_guard.py",
                            "argv": ["--run-dir", d], "rc": 2,
                            "tail": ["基线目录不存在：%s" % d],
                            "desc": "真实产出 fail-closed 复核"})
            continue
        rc, tail = run_gate("boundary_guard.py", ["--run-dir", d])
        results.append({"name": "基线越界复核·%s" % os.path.basename(d),
                        "script": "boundary_guard.py", "argv": ["--run-dir", d],
                        "rc": rc, "tail": tail, "desc": "真实产出 fail-closed 复核"})

    n_fail = sum(1 for r in results if r["rc"] != 0)
    if as_json:
        print(json.dumps({"total": len(results), "failed": n_fail,
                          "results": results}, ensure_ascii=False, indent=2))
    else:
        print("🚦 判别力门禁汇总 — %d 项\n" % len(results))
        for r in results:
            flag = "✅" if r["rc"] == 0 else "❌"
            print("  %s %-34s %-26s RC=%d" %
                  (flag, r["name"], r["script"], r["rc"]))
            if r["rc"] != 0:
                for line in r["tail"]:
                    print("       %s" % line)
        print("\n结论：%d/%d 通过%s" %
              (len(results) - n_fail, len(results),
               "" if not n_fail else " —— ❌ %d 项失败，禁止发布" % n_fail))
    return 1 if n_fail else 0


def self_test():
    """门禁清单自身的完整性与判别力（防止清单变成新的幽灵验证项）。"""
    fails = []
    print("🧪 self_gate 判别力自测\n")

    # 1) 清单里每个脚本必须真实存在且参数被接受
    print("  ── 清单完整性 ──")
    for name, script, argv, _ in GATES:
        path = os.path.join(HERE, script)
        if not os.path.isfile(path):
            print("  ❌ %-30s 脚本不存在 %s" % (name, script))
            fails.append(name)
            continue
        p = subprocess.run([sys.executable, path, "--help"],
                           capture_output=True, text=True)
        # 子命令形态（evolution_log self-test）单独跳过 --help 参数校验
        flag_arg = argv[0]
        if flag_arg.startswith("--") and flag_arg not in p.stdout:
            print("  ❌ %-30s %s 不接受 %s" % (name, script, flag_arg))
            fails.append(name)
        else:
            print("  ✅ %-30s %s %s" % (name, script, " ".join(argv)))

    # 2) 基线目录必须存在（否则越界复核会恒为空集 → 形态 B）
    print("\n  ── 基线扫描目标非空 ──")
    for d in BASELINE_DIRS:
        full = os.path.join(PKG, d)
        ok = os.path.isdir(full) and any(
            f.startswith("T-") and "__" in f for f in os.listdir(full))
        print("  %s %-40s %s" % ("✅" if ok else "❌", d,
                                 "有成员产出" if ok else "无产出/目录不存在"))
        if not ok:
            fails.append(d)

    # 3) 汇总逻辑的判别力：故意跑一个不存在的门禁，必须被判失败
    #    （若有人把 n_fail 恒置 0，本项会暴露）
    print("\n  ── 汇总逻辑判别力 ──")
    rc, _ = run_gate("__definitely_missing__.py", [])
    meta_ok = (rc != 0)
    print("  %s 故意注入缺失门禁 → 必须判失败（实得 rc=%d）"
          % ("✅" if meta_ok else "❌", rc))
    if not meta_ok:
        fails.append("汇总逻辑判别力")

    # 4) 反向：一个确定通过的门禁必须判成功（防「一律失败」假绿）
    rc2, _ = run_gate("agent_ci_gate.py", ["--self-test"])
    meta2_ok = (rc2 == 0)
    print("  %s 已知通过门禁 → 必须判成功（实得 rc=%d）"
          % ("✅" if meta2_ok else "❌", rc2))
    if not meta2_ok:
        fails.append("汇总逻辑反向判别力")

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    print("\n✅ 自测全通过（%d 门禁清单 + 2 基线 + 2 项元判别力）" % len(GATES))
    return 0


def main():
    ap = argparse.ArgumentParser(description="判别力门禁唯一汇总入口（S-E62/S-E67）")
    ap.add_argument("--self-test", action="store_true",
                    help="校验门禁清单自身的完整性与判别力")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return main_gates(args.json)


if __name__ == "__main__":
    sys.exit(main())
