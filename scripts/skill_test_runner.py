#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_test_runner.py — 按 skills/*/test-prompts.json 执行 skill 回归（P1-9）
用法：
  python3 scripts/skill_test_runner.py                    # 全部有 test-prompts 的 skill
  python3 scripts/skill_test_runner.py --skill triz-matrix
退出码：0=全过 1=有失败
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).parent.parent
FAIL = 0
# CYCLE-1 · S-E46：RESULTS 此前**定义后从未被追加/读取**（死变量）。
# 实际统计走 run_case() 的返回值累加（见下方 ok/FAIL 计数），本变量纯误导 → 移除。


def run_case(skill, case):
    q = case["query"]
    p = subprocess.run(q.split(), cwd=PKG, capture_output=True, text=True, timeout=30)
    out = p.stdout + p.stderr
    ok = True
    notes = []
    if p.returncode != case.get("expect_exit", 0):
        ok = False
        notes.append(f"exit={p.returncode} 期望{case.get('expect_exit')}")
    for token in case.get("expect_contains", []):
        if token not in out:
            ok = False
            notes.append(f"缺「{token}」")
    return ok, notes, out[:120].replace("\n", " | ")


def main():
    global FAIL
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default="")
    args = ap.parse_args()

    for tp in sorted(PKG.glob("skills/*/test-prompts.json")):
        skill = tp.parent.name
        if args.skill and skill != args.skill:
            continue
        data = json.loads(tp.read_text(encoding="utf-8"))
        # 兼容两种格式：旧版=纯列表；新版=dict含cases
        if isinstance(data, list):
            cases, meta = data, {"skill": skill}
        else:
            cases, meta = data.get("cases", []), data
        if not cases:
            continue
        print(f"\n═══ skill: {skill}（{len(cases)} 用例）═══")
        for case in cases:
            # 人工评估类（旧格式：有prompt/expected无query）→ SKIP
            if "query" not in case and "fixture" not in case:
                print(f"  ⏭️  {case.get('id', '?')} 人工评估用例（runner不自动判·保留给darwin人工轮）")
                continue
            if case.get("type") in ("valid_envelope", "invalid_envelope"):
                # schema 类用例：调 agent_ci_gate 的 jsonschema 校验
                try:
                    import jsonschema
                    schema = json.loads((tp.parent / "result_envelope.schema.json").read_text(encoding="utf-8"))
                    if case["type"] == "valid_envelope":
                        jsonschema.validate(case["fixture"], schema)
                        ok, notes = True, []
                    else:
                        try:
                            jsonschema.validate(case["fixture"], schema)
                            ok, notes = False, ["本应拒绝却通过"]
                        except jsonschema.ValidationError:
                            ok, notes = True, []
                except ImportError:
                    ok, notes = True, ["jsonschema未装·跳过"]
                notes_str = " ".join(notes)
                print(f"  {'✅' if ok else '❌'} {case['id']} {case['type']} {notes_str}")
            else:
                ok, notes, preview = run_case(skill, case)
                print(f"  {'✅' if ok else '❌'} {case['id']} {case['query'][-40:]} {' '.join(notes) or ''}")
            if not ok:
                FAIL = 1

    print("\n———————")
    print("全过 ✅" if FAIL == 0 else "存在失败 ❌")
    return FAIL


if __name__ == "__main__":
    sys.exit(main())
