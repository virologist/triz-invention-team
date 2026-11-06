#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
state_store.py — TASK_STATE 持久化与断点续接（v2.6.0 Batch2 · 修 S-X3/S-A2/J1）
=====================================================================
问题（S-X3）：H2 状态只存在于主理人会话内存——长链路（L2 45min）中断后
无恢复点，续接靠重读全部产出人工重建状态。

本脚本提供确定性状态读写：
  init      初始化 run 目录的 state.json（从 --task-id/--members 起步）
  update    更新一个字段（phase/gates/verdicts/retry_counts/...）
  show      打印当前状态（人类可读）
  resume    断点续接评估：打印已完成阶段、未关门禁、下一动作建议
  self-test 内置自检

state.json 结构 = architecture.md §3.2（单一权威 schema，H2 与本文档一致），
并在 v2.6.0 补齐：metrics.duration_ms_wall / conflicts / verdicts.score（S-A2/J1）。

用法：
  python3 scripts/state_store.py init --run-dir outputs/<run> --task-id T-20261107-001 \
      --members contradiction-analyst,patent-search-scout,...
  python3 scripts/state_store.py update --run-dir outputs/<run> --set phase=3 \
      --set gates.G1=true --set verdicts.examiner.result=yellow --set verdicts.examiner.score=4
  python3 scripts/state_store.py show --run-dir outputs/<run>
  python3 scripts/state_store.py resume --run-dir outputs/<run>
  python3 scripts/state_store.py self-test

退出码：0=正常 1=状态文件缺失或损坏 2=用法错误
"""
import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

# 与 architecture.md §3.2 对齐的 state 模板（单一权威；v2.6.0 字段补齐版）
STATE_TEMPLATE = {
    "schema_version": "1.1.0",
    "task_id": "",
    "phase": 0,
    "domain": "",
    "invention_name": "",
    "search_rounds": 0,
    "verdicts": {
        "examiner": {"result": None, "score": None, "confidence": None},
        "second_opinion": {"result": None, "score": None, "confidence": None},
    },
    "gates": {
        "search_3rounds_complete": False,
        "c1_c8_confirmed": False,
        "disclosure_gap_scan": False,
        "g5_format_compliant": False,
    },
    "conditions": {},          # 二审条件清单（K1..K7/M1..M7 → closed/open）· J2 对账数据源
    "retry_counts": {},
    "confirmed_items": {},
    "conflicts": [],           # L3 仲裁记录
    "metrics": {
        "total_duration_ms": 0,
        "total_duration_ms_wall": 0,   # 权威墙钟累计（H5 双轨制）
        "agent_calls": 0,
        "duration_source": "lead_measured",
    },
    "history": [],             # 每次 update 的追加轨迹（断点续接的时间线）
    "updated_at": None,
}

PHASE_NEXT = {
    0: "Phase 1: TRIZ问题建模（contradiction-analyst）",
    1: "Phase 2: 原理引导与创意生成（contradiction-analyst）",
    2: "Phase 3: 三轮查新（patent-search-scout，≥3轮）",
    3: "Phase 4: 对抗式三性确认（examiner → second-opinion 串行）",
    4: "Phase 5: 专利文件撰写（disclosure → attorney 串行）",
    5: "最终交付：主理人汇编打包",
}


def state_path(run_dir):
    return os.path.join(run_dir, "state.json")


def load_state(run_dir):
    p = state_path(run_dir)
    if not os.path.isfile(p):
        return None, f"状态文件不存在：{p}（先跑 init）"
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, f"状态文件损坏：{e}"


def save_state(run_dir, state, note=""):
    state["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    if note:
        state["history"].append({"ts": state["updated_at"], "note": note})
    os.makedirs(run_dir, exist_ok=True)
    with open(state_path(run_dir), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def set_nested(state, dotted_key, raw_value):
    """支持点路径赋值：phase / gates.G1 / verdicts.examiner.result / conditions.K1"""
    # 布尔/整数/浮点/JSON 自动转型
    v = raw_value
    if isinstance(v, str):
        if v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        else:
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass  # 保持字符串
    keys = dotted_key.split(".")
    cur = state
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = v


def cmd_init(args):
    members = [m.strip() for m in (args.members or "").split(",") if m.strip()]
    state = json.loads(json.dumps(STATE_TEMPLATE))  # 深拷贝
    state["task_id"] = args.task_id
    state["retry_counts"] = {m: 0 for m in members}
    save_state(args.run_dir, state, note=f"init（task={args.task_id}，{len(members)} 成员）")
    print(f"✅ 状态已初始化：{state_path(args.run_dir)}")
    print(f"   task_id={args.task_id}  members={len(members)}")
    return 0


def cmd_update(args):
    state, err = load_state(args.run_dir)
    if err:
        print(f"❌ {err}")
        return 1
    for kv in args.set or []:
        if "=" not in kv:
            print(f"❌ --set 格式应为 key=value：{kv}")
            return 2
        k, v = kv.split("=", 1)
        set_nested(state, k.strip(), v.strip())
    save_state(args.run_dir, state, note="; ".join(args.set or []))
    print(f"✅ 已更新 {len(args.set or [])} 项 → {state_path(args.run_dir)}")
    return 0


def cmd_show(args):
    state, err = load_state(args.run_dir)
    if err:
        print(f"❌ {err}")
        return 1
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def _gates_open(state):
    return [g for g, v in state.get("gates", {}).items() if not v]


def _conditions_open(state):
    return [k for k, v in state.get("conditions", {}).items() if not v]


def cmd_resume(args):
    """断点续接评估：给主理人一张'从哪里继续'的确定性清单。"""
    state, err = load_state(args.run_dir)
    if err:
        print(f"❌ {err}")
        return 1
    phase = state.get("phase", 0)
    open_gates = _gates_open(state)
    open_conds = _conditions_open(state)
    v = state.get("verdicts", {})

    print(f"📋 断点续接评估 — {state.get('task_id') or '(未命名任务)'}")
    print(f"   运行目录：{os.path.abspath(args.run_dir)}")
    print(f"   最后更新：{state.get('updated_at')}")
    print(f"   当前阶段：Phase {phase}")
    if phase < 5:
        print(f"   下一动作：{PHASE_NEXT.get(phase, '?')}")
    else:
        print("   下一动作：汇编交付包")
    print(f"   查新进度：{state.get('search_rounds', 0)}/3 轮")
    print(f"   未关门禁：{open_gates or '无'}")
    print(f"   一审裁决：{v.get('examiner', {}).get('result') or '未产出'}"
          f"（score={v.get('examiner', {}).get('score')}）")
    print(f"   二审表态：{v.get('second_opinion', {}).get('result') or '未产出'}"
          f"（score={v.get('second_opinion', {}).get('score')}）")
    if open_conds:
        print(f"   ⚠ 二审条件未关闭 {len(open_conds)} 项：{open_conds}（进 Phase 5 前须兑现或登记待办）")
    print(f"   重试计数：{state.get('retry_counts') or '{}'}")
    print(f"   冲突记录：{len(state.get('conflicts', []))} 条")
    hist = state.get("history", [])
    if hist:
        print(f"   最近轨迹：{hist[-1]['ts']} — {hist[-1]['note'][:60]}")
    return 0


def cmd_self_test(args):
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        # 1) init
        r = subprocess_run([sys.executable, os.path.abspath(__file__), "init",
                            "--run-dir", td, "--task-id", "T-20261107-TEST",
                            "--members", "contradiction-analyst,patent-search-scout"])
        ok &= (r == 0)
        # 2) update 嵌套键
        r = subprocess_run([sys.executable, os.path.abspath(__file__), "update",
                            "--run-dir", td, "--set", "phase=3",
                            "--set", "gates.G1=true",
                            "--set", "verdicts.examiner.result=yellow",
                            "--set", "verdicts.examiner.score=4",
                            "--set", "conditions.K1=true"])
        ok &= (r == 0)
        # 3) 读回断言
        state, err = load_state(td)
        if err:
            print(f"  ❌ 读回失败: {err}")
            return 1
        checks = [
            ("task_id", state["task_id"] == "T-20261107-TEST"),
            ("phase=3", state["phase"] == 3),
            ("gates.G1", state["gates"]["G1"] is True),
            ("examiner.result", state["verdicts"]["examiner"]["result"] == "yellow"),
            ("examiner.score(int)", state["verdicts"]["examiner"]["score"] == 4),
            ("conditions.K1", state["conditions"]["K1"] is True),
            ("history追加", len(state["history"]) == 2),
        ]
        for name, passed in checks:
            print(f"  {'✅' if passed else '❌'} {name}")
            ok &= passed
        # 4) resume 可执行
        r = subprocess_run([sys.executable, os.path.abspath(__file__), "resume", "--run-dir", td])
        ok &= (r == 0)
    print("self-test ✅" if ok else "self-test ❌")
    return 0 if ok else 1


def subprocess_run(cmd):
    import subprocess
    return subprocess.run(cmd, capture_output=True, text=True).returncode


def main():
    ap = argparse.ArgumentParser(description="TASK_STATE 持久化与断点续接")
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("init")
    p1.add_argument("--run-dir", required=True)
    p1.add_argument("--task-id", required=True)
    p1.add_argument("--members", default="")

    p2 = sub.add_parser("update")
    p2.add_argument("--run-dir", required=True)
    p2.add_argument("--set", action="append", default=[])

    p3 = sub.add_parser("show")
    p3.add_argument("--run-dir", required=True)

    p4 = sub.add_parser("resume")
    p4.add_argument("--run-dir", required=True)

    p5 = sub.add_parser("self-test")
    p5.add_argument("--run-dir", default="")

    args = ap.parse_args()
    if args.cmd == "init":
        return cmd_init(args)
    if args.cmd == "update":
        return cmd_update(args)
    if args.cmd == "show":
        return cmd_show(args)
    if args.cmd == "resume":
        return cmd_resume(args)
    if args.cmd == "self-test":
        return cmd_self_test(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
