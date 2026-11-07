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
  python3 scripts/triz_benchmark.py --level L1 --run-dir outputs/regression-20261015
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


def evaluate_case(case_id, run_dir):
    """调 run_regression.py 断言引擎，返回 (score 0-1, detail, report)。"""
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "run_regression.py"),
         "--case", case_id, "--dir", run_dir, "--json"],
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
        tasks = []
        for case_id in self.cases:
            task_path = os.path.join(self.pkg, "tests", "cases", case_id + ".task.md")
            text = open(task_path, encoding="utf-8").read() if os.path.isfile(task_path) else ""
            tasks.append({
                "id": case_id,
                "input": text,
                "metadata": {"level": self.level, "task_file": task_path},
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


def main():
    ap = argparse.ArgumentParser(description="TRIZ 用例 → A-Evolve benchmark 适配/独立求值")
    ap.add_argument("--level", default="L1", choices=["L1", "L2"], help="用例层级")
    ap.add_argument("--case", help="单用例求值（覆盖 --level）")
    ap.add_argument("--run-dir", required=True, help="成员产出运行目录")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cases = [args.case] if args.case else [c for c, lv in CASE_LEVEL.items() if lv == args.level]
    out = []
    for case_id in cases:
        score, detail, report = evaluate_case(case_id, args.run_dir)
        out.append({"case": case_id, "score": round(score, 3), "detail": detail})
        if not args.json:
            print(f"  {'✅' if score >= 0.75 else '❌'} {case_id}: score={score:.3f} ({detail})")
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        avg = sum(o["score"] for o in out) / len(out) if out else 0.0
        print(f"\n{args.case or args.level} 综合分：{avg:.3f}（success 线 0.75 = A-Evolve gate）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
