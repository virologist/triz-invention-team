#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triz_benchmark.py — A-Evolve BenchmarkAdapter 适配器（v2.6.0 Batch5B · S-Q3 升维）
=====================================================================
把 tests/cases/ 三用例（workflow-a/b/c）接入 A-Evolve 的 Benchmark 接口，
使专家团的「prompt/规则/脚本」可以走 solve-observe-evolve 闭环：
  - get_tasks(): 从 *.task.md 读任务包 → ae.Task
  - evaluate():  调 run_regression.py 断言引擎对产出求值 → ae.Feedback(0.0-1.0)

分层与成本（对齐 tests/README.md）：
  L1 workflow-b-01（analyst）/ workflow-c-01（scout）：分钟级，演化默认用
  L2 workflow-a-01（全链路 45min）：holdout / 发布验收用，默认不进训练批

用法：
  # 1) A-Evolve 闭环（已安装 a-evolve 时）
  import agent_evolve as ae
  from triz_benchmark import TrizBenchmark
  evolver = ae.Evolver(agent=<workspace>, benchmark=TrizBenchmark(level="L1"))
  results = evolver.run(cycles=5)

  # 2) 独立求值（不依赖 a-evolve，直接算分）
  python3 scripts/triz_benchmark.py --level L1 --run-dir tests/baselines/l1-analyst-b01
  python3 scripts/triz_benchmark.py --case workflow-b-01 --run-dir <dir> --json

评分映射：PASS 断言数 / 总断言数（0.0-1.0）；INFO 断言计 PASS；SKIP 不计分母。
退出码：0=正常 2=用法/环境错误
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, HERE)

CASE_LEVEL = {
    "workflow-b-01": "L1",
    "workflow-c-01": "L1",
    "workflow-a-01": "L2",
}

# A-Evolve success 线：单用例得分 ≥ 此值即视为该用例通过（S-E56 · 此前仅用于打印）
SUCCESS_LINE = 0.75

# CYCLE-1 · S-E57（用例 → 基线目录映射）：此前 `--level L1` 会把**同一个**
# `--run-dir` 同时用于 workflow-b-01（目标成员 contradiction-analyst）
# 与 workflow-c-01（目标成员 patent-search-scout）。
# 两者目标成员不同 → 同一目录必然只有一方能拿高分（实测 b=1.000 / c=0.500），
# 综合分被结构性拉低到 0.75（恰好等于 success 线）—— 这是**假绿/假红**，
# 与用例内容无关。
# 现改为：每个用例**声明自己的基线目录**，--run-dir 仅作显式覆盖。
#
# 基线目录选择依据（实测）：
#   workflow-b-01 → contradiction-analyst → tests/baselines/l1-analyst-b01
#   workflow-c-01 → patent-search-scout   → tests/baselines/l2-full-a01
#   workflow-a-01 → 全链路 6 成员          → tests/baselines/l2-full-a01
CASE_BASELINE = {
    "workflow-b-01": os.path.join("tests", "baselines", "l1-analyst-b01"),
    "workflow-c-01": os.path.join("tests", "baselines", "l2-full-a01"),
    "workflow-a-01": os.path.join("tests", "baselines", "l2-full-a01"),
}

# 用例目标成员（用于校验 --run-dir 覆盖是否与用例匹配，S-E57）
CASE_TARGET_MEMBER = {
    "workflow-b-01": "contradiction-analyst",
    "workflow-c-01": "patent-search-scout",
    "workflow-a-01": "full-team",
}


def evaluate_case(case_id, run_dir):
    """调 run_regression.py 断言引擎，返回 (score 0-1, detail, report)。

    CYCLE-1 · S-E58（求值污染）：bench 是**只读求值**场景，反复求值不应
    改写入库的基线报告（checked_at 每次刷新 → git 工作树脏 → diff 全是噪音）。
    故传 --no-report-write。
    """
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "run_regression.py"),
         "--case", case_id, "--dir", run_dir, "--json", "--no-report-write"],
        capture_output=True, text=True, timeout=120)
    try:
        report = json.loads(r.stdout)
    except Exception:
        # 退路：从文本报告解析
        out = r.stdout + r.stderr
        import re
        m = re.search(r"结果：(\d+)/(\d+) PASS.*?(\d+) FAIL", out)
        if m:
            passed, total, _ = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return passed / total if total else 0.0, f"{passed}/{total} PASS（文本解析）", None
        return 0.0, f"断言引擎无输出 exit={r.returncode}", None
    # JSON 报告：优先顶层 passed/total（run_regression 权威口径），INFO 计 PASS
    total = report.get("total") or 0
    passed = report.get("passed") or 0
    info = report.get("info") or 0
    if total:
        score = (passed + info) / total
        return score, f"{passed}+{info}INFO / {total} 断言", report
    # 兜底：逐条 results[].pass
    results = report.get("results") or []
    n_total = n_pass = 0
    for item in results:
        n_total += 1
        if item.get("pass") is True:
            n_pass += 1
    score = n_pass / n_total if n_total else 0.0
    return score, f"{n_pass}/{n_total} 断言 PASS", report


class TrizBenchmark:
    """A-Evolve BenchmarkAdapter 实现（鸭子类型：不硬依赖 agent_evolve 包也可独立运行）。

    与 a-evolve 的接口对齐：
      get_tasks(split, limit) -> list[Task-like(id, input, metadata)]
      evaluate(task, trajectory) -> Feedback-like(success, score, detail)
    trajectory 约定：solve 侧（主理人或演化引擎）把成员产出落盘到 trajectory.output_dir
    （即 run_regression 的 --dir 运行目录），evaluate 即对该目录求值。
    """

    def __init__(self, level="L1", pkg_dir=None):
        self.level = level
        self.pkg = pkg_dir or PKG
        self.cases = [c for c, lv in CASE_LEVEL.items() if lv == level]

    def get_tasks(self, split="train", limit=None):
        """返回本层用例列表。

        CYCLE-1 · S-E57（死参数清偿）：`split` 参数此前**定义后从未被读取**
        —— 签名里有、docstring 里有、调用方传了，但函数体完全没用它。
        这属于「死参数」：看起来像支持 train/val/test 切片，实际不区分，
        任何 split 返回完全相同的任务列表 → A-Evolve 若按 split 划分
        训练/评测集，会**数据泄漏**（holdout 用例被当成训练用例）。

        现语义明确：
          - split="train"  → 返回本层**全部**用例（当前 L1 两例均为训练用）
          - split="holdout" → 返回 holdout 用例（当前仅 L2 workflow-a-01，
            按 tests/README.md「L2 默认不进训练批」的约定）
          - 其它 split 值 → 抛错（不静默忽略，避免调用方误以为生效）
        """
        if split not in ("train", "holdout"):
            raise ValueError(
                "split 只支持 'train' / 'holdout'，收到 %r（S-E57：此前该参数"
                "从未被读取，任何 split 返回相同任务列表 → holdout 泄漏）" % split)
        cases = self.cases
        if split == "holdout":
            # holdout = L2 用例（tests/README.md：L2 默认不进训练批）
            cases = [c for c in cases if CASE_LEVEL.get(c) == "L2"]
        tasks = []
        for case_id in cases:
            task_path = os.path.join(self.pkg, "tests", "cases", case_id + ".task.md")
            text = open(task_path, encoding="utf-8").read() if os.path.isfile(task_path) else ""
            tasks.append({
                "id": case_id,
                "input": text,
                "metadata": {
                    "level": self.level,
                    "task_file": task_path,
                    "split": split,
                    "baseline_dir": os.path.join(self.pkg, CASE_BASELINE.get(case_id, "")),
                    "target_member": CASE_TARGET_MEMBER.get(case_id, ""),
                },
            })
        return tasks[:limit] if limit else tasks

    def evaluate(self, task, trajectory):
        """trajectory 需带 output_dir（solve 侧落盘的运行目录）。"""
        run_dir = getattr(trajectory, "output_dir", None) or (
            trajectory.get("output_dir") if isinstance(trajectory, dict) else None)
        if not run_dir or not os.path.isdir(run_dir):
            return {"success": False, "score": 0.0,
                    "detail": "trajectory 缺 output_dir（solve 侧须落盘成员产出目录）"}
        score, detail, _ = evaluate_case(task["id"] if isinstance(task, dict) else task.id, run_dir)
        return {"success": score >= 0.75, "score": score, "detail": detail}


def _dir_has_member(run_dir, case_id):
    """检查 run_dir 内是否含该用例目标成员的落盘产出（用于覆盖校验）。"""
    target = CASE_TARGET_MEMBER.get(case_id)
    if not target or target == "full-team":
        return True, ""
    if not os.path.isdir(run_dir):
        return False, "目录不存在"
    for f in os.listdir(run_dir):
        if f.endswith("__%s.md" % target):
            return True, f
    return False, "无 %s 产出" % target


# ─────────────────────────────────────────────────────────────────────
# 判别力自测（S-E56 / S-E57）
# ─────────────────────────────────────────────────────────────────────
def _self_test():
    """判别力自测：映射正确性 + 退出码语义 + split 语义。"""
    fails = []

    def chk(name, got, expect):
        okk = (got == expect)
        print("  %s %-42s 期望=%-18s 实得=%s"
              % ("✅" if okk else "❌", name, expect, got))
        if not okk:
            fails.append(name)

    print("🧪 triz_benchmark 判别力自测\n")

    # ── 1. 用例 → 基线目录映射（目标成员必须与基线目录匹配）──
    print("  ── 用例→基线映射（目标成员必须在场）──")
    for case_id, target in CASE_TARGET_MEMBER.items():
        d = os.path.join(PKG, CASE_BASELINE[case_id])
        if target == "full-team":
            present = os.path.isdir(d)
        else:
            okd, _why = _dir_has_member(d, case_id)
            present = okd
        chk("%s 基线含 %s" % (case_id, target), present, True)

    # ── 2. 不同用例的基线目录必须不同（S-E57 根因）──
    b = CASE_BASELINE["workflow-b-01"]
    c = CASE_BASELINE["workflow-c-01"]
    chk("b 与 c 的基线目录不同", b != c, True)
    chk("b 目标=analyst", CASE_TARGET_MEMBER["workflow-b-01"], "contradiction-analyst")
    chk("c 目标=scout", CASE_TARGET_MEMBER["workflow-c-01"], "patent-search-scout")

    # ── 3. split 语义（S-E57 死参数）──
    print("\n  ── split 语义 ──")
    bm = TrizBenchmark(level="L1")
    tr = bm.get_tasks(split="train")
    ho = bm.get_tasks(split="holdout")
    chk("L1 train 用例数", len(tr), 2)
    chk("L1 holdout 用例数", len(ho), 0)
    chk("L1 train 全部标记 split=train",
        all(t["metadata"]["split"] == "train" for t in tr), True)
    try:
        bm.get_tasks(split="val")
        chk("非法 split 抛错", "未抛错", "抛错")
    except ValueError:
        chk("非法 split 抛错", "抛错", "抛错")
    bm2 = TrizBenchmark(level="L2")
    chk("L2 holdout 用例数", len(bm2.get_tasks(split="holdout")), 1)

    # ── 4. 退出码语义（S-E56）──
    print("\n  ── 退出码语义（success 线 %.2f）──" % SUCCESS_LINE)
    chk("SUCCESS_LINE 常量", SUCCESS_LINE, 0.75)
    # evaluate 的 success 判定必须与 SUCCESS_LINE 一致
    for sc, expect in [(0.80, True), (0.75, True), (0.74, False), (0.0, False)]:
        chk("score=%.2f → success=%s" % (sc, expect), sc >= SUCCESS_LINE, expect)

    # ── 4b. 退出码**真的**随分数变化（S-E56 判别力靶点）────────────
    # 首轮变异测试发现：本自测只验证了 SUCCESS_LINE 与 success 判定，
    # **没验证 main() 的退出码**——把 `return 1` 改回 `return 0` 时自测仍 PASS
    # （假绿，形式化验证）。本用例改为**实跑 main()** 并读真实退出码。
    print("\n  ── 退出码实跑验证（main() 真实返回值）──")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rc = _run_main(["--level", "L1", "--run-dir", td])
        chk("空目录（低分）→ 退出码", rc, 1)
    rc_ok = _run_main(["--level", "L1"])
    chk("用例自带基线（全过）→ 退出码", rc_ok, 0)
    with tempfile.TemporaryDirectory() as td:
        rc_bad = _run_main(["--case", "workflow-c-01", "--run-dir", td])
        chk("单用例低分 → 退出码", rc_bad, 1)

    if fails:
        print("\n❌ 自测失败 %d 项：%s" % (len(fails), fails))
        return 1
    print("\n✅ 自测全通过")
    return 0


def _run_main(argv):
    """实跑 main() 并返回真实退出码（供自测断言用）。"""
    old_argv = sys.argv
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.argv = ["triz_benchmark.py"] + list(argv)
    try:
        import io
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            rc = main()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        return rc
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def main():
    ap = argparse.ArgumentParser(description="TRIZ 用例 → A-Evolve benchmark 适配/独立求值")
    ap.add_argument("--level", default="L1", choices=["L1", "L2"], help="用例层级")
    ap.add_argument("--case", help="单用例求值（覆盖 --level）")
    ap.add_argument("--run-dir", default="",
                    help="成员产出运行目录（显式覆盖各用例自带基线目录）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true",
                    help="判别力自测（用例→基线映射 / 退出码语义 / split 语义）")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()

    cases = [args.case] if args.case else [c for c, lv in CASE_LEVEL.items() if lv == args.level]
    out = []
    for case_id in cases:
        # S-E57：默认用该用例**自己的**基线目录；--run-dir 仅作显式覆盖
        if args.run_dir:
            run_dir = args.run_dir
            src = "显式覆盖(--run-dir)"
            ok_dir, why = _dir_has_member(run_dir, case_id)
            if not ok_dir:
                print("⚠️  %s：%s 内无该用例目标成员的产出（%s）——"
                      "该用例得分不可信（同一目录评不同目标成员的用例必然失真）"
                      % (case_id, run_dir, why), file=sys.stderr)
        else:
            run_dir = os.path.join(PKG, CASE_BASELINE.get(case_id, ""))
            src = "用例自带基线"
            if not os.path.isdir(run_dir):
                print("❌ %s：用例自带基线目录不存在：%s" % (case_id, run_dir),
                      file=sys.stderr)
                out.append({"case": case_id, "score": 0.0, "detail": "基线目录缺失",
                            "run_dir": run_dir, "source": src, "pass": False})
                continue
        score, detail, report = evaluate_case(case_id, run_dir)
        passed = score >= SUCCESS_LINE
        out.append({"case": case_id, "score": round(score, 3), "detail": detail,
                    "run_dir": run_dir, "source": src, "pass": passed})
        if not args.json:
            print(f"  {'✅' if passed else '❌'} {case_id}: score={score:.3f} "
                  f"({detail}) · 目录={os.path.relpath(run_dir, PKG)} [{src}]")

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        avg = sum(o["score"] for o in out) / len(out) if out else 0.0
        print(f"\n{args.case or args.level} 综合分：{avg:.3f}（success 线 {SUCCESS_LINE} = A-Evolve gate）")

    # ── CYCLE-1 · S-E56（退出码语义化）──────────────────────────────
    # 此前无论分数高低都 `return 0` → 「success 线 0.75 = A-Evolve gate」
    # 这句话在 CLI 层**语义空转**（幽灵验证项形态 D：判定结果不影响退出码）。
    # shell / CI 无法据此 gate —— 分数再低也照样绿灯通过。
    # 现改为：任一用例未达 success 线 → 退出码 1（可被 shell/CI 消费）。
    if not out:
        return 2
    n_fail = sum(1 for o in out if not o.get("pass"))
    if n_fail:
        print("❌ %d/%d 用例未达 success 线 %.2f —— gate 未通过"
              % (n_fail, len(out), SUCCESS_LINE), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
