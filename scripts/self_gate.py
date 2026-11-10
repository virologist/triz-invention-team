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
    ("宿主门禁接入", "install_gate_hooks.py", ["--self-test"],
     "新机器可移植性 + 漂移/幂等/元判别力"),
    ("统一工作入口", "harness.py", ["--self-test"],
     "阶段验收不假绿 + 门禁真值 + 反馈护栏 + 元判别力"),
    ("版本号一致性", "version_consistency.py", ["--self-test"],
     "4 个版本位必须相等（历史漂移 2.10.0 vs 2.11.2 的根因护栏）"),
]

# 真实基线扫描（对已入库产出做 fail-closed 越界复核）——
# 这一项是 S-E62 的核心：让 boundary_guard 从「只有 --self-test」变成
# 「每次门禁都对真实产出跑一遍」。
# TRIZ_GATE_BASELINE_ROOT 可覆盖包根（换机路径不同 / 判别力测试制造
# 「基线缺失」场景）——S-E70 可移植性 + 让 self_test 的基线非空校验
# 有可触发的判别力场景（变异 S4 靶点）。
BASELINE_SUBDIRS = [
    "tests/baselines/l2-full-a01",
    "tests/baselines/l1-analyst-b01",
]


def baseline_dirs():
    root = os.environ.get("TRIZ_GATE_BASELINE_ROOT") or PKG
    return [os.path.join(root, d) for d in BASELINE_SUBDIRS]


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
    for full in baseline_dirs():
        d = os.path.relpath(full, os.environ.get("TRIZ_GATE_BASELINE_ROOT") or PKG)
        if not os.path.isdir(full):
            results.append({"name": "基线越界复核", "script": "boundary_guard.py",
                            "argv": ["--run-dir", d], "rc": 2,
                            "tail": ["基线目录不存在：%s" % full],
                            "desc": "真实产出 fail-closed 复核"})
            continue
        rc, tail = run_gate("boundary_guard.py", ["--run-dir", full])
        results.append({"name": "基线越界复核·%s" % os.path.basename(full),
                        "script": "boundary_guard.py", "argv": ["--run-dir", full],
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


def discover_selftest_scripts():
    """机械发现**所有**接受 `--self-test` 的脚本（用于双向差集）。

    S-E69（第5轮 C4 再诊断实测）：原 --self-test 只校验「清单里的脚本存在」
    （单向），实测注入一个带 --self-test 的新脚本 `__canary_gate.py` 后，
    self_gate --self-test 仍 RC=0、输出完全不提 canary → **漏挂不会被发现**。
    这与第4轮 S-E54 的「契约手抄无机械校验」同型，解法同为双向差集。
    注：以 `--help` 输出是否含 `--self-test` 作为判据（不 import、不执行主流程）。
    """
    import glob
    found = set()
    for path in glob.glob(os.path.join(HERE, "*.py")):
        name = os.path.basename(path)
        if name == os.path.basename(__file__):
            continue  # 自身是汇总入口，不是被汇总的门禁
        p = subprocess.run([sys.executable, path, "--help"],
                           capture_output=True, text=True)
        if "--self-test" in (p.stdout + p.stderr):
            found.add(name)
    return found


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
        flag_arg = argv[0]
        help_txt = p.stdout + p.stderr
        if flag_arg.startswith("--"):
            ok = flag_arg in help_txt
        else:
            # 子命令形态：也要真校验（旧实现直接跳过 → 形态 A 缺口）
            ok = flag_arg in help_txt
        if not ok:
            print("  ❌ %-30s %s 不接受 %s" % (name, script, flag_arg))
            fails.append(name)
        else:
            print("  ✅ %-30s %s %s" % (name, script, " ".join(argv)))

    # 1b) 双向差集：清单 ↔ 全仓真实自测脚本，差集必须为空（S-E69）
    print("\n  ── 清单双向差集（S-E69 防漏挂）──")
    discovered = discover_selftest_scripts()
    # verify_triz_data 用 --strict 而非 --self-test，属**显式例外**，
    # 在清单里但不在 discovered 里是预期行为，不算差集。
    EXPLICIT_NON_SELFTEST = {"verify_triz_data.py"}
    listed_selftest = {s for _, s, argv, _ in GATES
                       if argv and argv[0] == "--self-test"}
    missing = discovered - listed_selftest          # 有自测但没挂进门禁用
    stale = listed_selftest - discovered - EXPLICIT_NON_SELFTEST  # 挂了但已无自测
    print("  %s 全仓发现 %d 个 --self-test 脚本 / 清单收录 %d 个"
          % ("✅" if not missing and not stale else "❌",
             len(discovered), len(listed_selftest)))
    if missing:
        print("  ❌ 漏挂（有自测但不在门禁清单）：%s" % sorted(missing))
        fails.append("漏挂:%s" % sorted(missing))
    if stale:
        print("  ❌ 陈旧（清单收录但已无自测）：%s" % sorted(stale))
        fails.append("陈旧:%s" % sorted(stale))
    if not missing and not stale:
        print("  ✅ 双向差集为空")

    # 2) 基线目录必须存在（否则越界复核会恒为空集 → 形态 B）
    print("\n  ── 基线扫描目标非空 ──")
    for full in baseline_dirs():
        d = os.path.relpath(full, os.environ.get("TRIZ_GATE_BASELINE_ROOT") or PKG)
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

    # 5) 宿主接入自检（S-E71：消除「自测全绿但门禁没人调用」的假绿）
    # 实测：干净 `git clone . /tmp/fresh-clone` 里 --self-test 报「✅ 全通过」，
    # 但宿主 pre-commit / release-sync 根本没接 self_gate → 门禁链退回 3 gate。
    # 现消费 install_gate_hooks.verify_host() 唯一判据，未接入/漂移即自测失败。
    # CI 环境（无宿主工具链）可显式 --skip-host-check 跳过，但默认严格。
    print("\n  ── 宿主接入自检（S-E71 防幽灵执行点）──")
    if os.environ.get("TRIZ_GATE_SKIP_HOST_CHECK") == "1":
        print("  ⏭  已按 TRIZ_GATE_SKIP_HOST_CHECK=1 显式跳过（CI 环境）")
    else:
        sys.path.insert(0, HERE)
        try:
            import install_gate_hooks as IH
            host_root = os.environ.get("TRIZ_GATE_HOST_ROOT") or \
                os.path.expanduser("~/.workbuddy")
            host_ok, host_res = IH.verify_host(host_root)
            for k, v in sorted(host_res.items()):
                flag = "✅" if v["status"] in ("installed", "legacy") else "❌"
                print("  %s %-14s %-18s %s" %
                      (flag, k, v["status"], v["detail"]))
            if not host_ok:
                print("  ❌ 宿主门禁未接入或已漂移 → 判别力门禁**不会自动运行**")
                print("     修复：python3 scripts/install_gate_hooks.py --install")
                fails.append("宿主接入")
            else:
                print("  ✅ 宿主门禁已接入（pre-commit + release-sync）")
        except Exception as e:  # noqa: BLE001 —— 门禁必须 fail loud
            print("  ❌ 宿主接入自检异常：%s" % e)
            fails.append("宿主接入自检异常")

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    # 基线数取自 BASELINE_SUBDIRS（唯一真源），不写死数字——
    # 否则增删基线目录时本行会漂移（S-E72 同型问题，此处一并根治）
    print("\n✅ 自测全通过（%d 门禁清单 + %d 基线 + 2 项元判别力 + 宿主接入）"
          % (len(GATES), len(BASELINE_SUBDIRS)))
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
