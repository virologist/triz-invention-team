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

# 门禁别名表（CYCLE-1 · S-E01/S-E02 修复，唯一真源）
# 历史缺陷：SOP（主理人 MD H2 示例）让主理人写 gates.G1..G5，而本模板用语义键 →
# 实测写入后 state.json 出现 9 键（4 语义 false + 5 编号 true），run_regression.check_gates
# 按 dict 插入序取前 5 值 = [false×4,true] → 门禁断言必然 FAIL，Phase5 永远卡死。
# 修复：G1-G5 作为别名，在 set_nested 时归一到语义键；G2 补齐三性通过落点。
GATE_ALIASES = {
    "G1": "search_3rounds_complete",
    "G2": "trinity_verdict_pass",
    "G3": "c1_c8_confirmed",
    "G4": "disclosure_gap_scan",
    "G5": "g5_format_compliant",
}

# 与 architecture.md §3.2 对齐的 state 模板（单一权威；v2.6.0 字段补齐版）
STATE_TEMPLATE = {
    "schema_version": "1.2.0",
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
        "trinity_verdict_pass": False,     # G2：examiner∈{green,yellow} ∧ second_opinion≠disagree
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
        "loopback_count": 0,          # S-E10/S-E18：Phase2↔3/4 回流累计，上限 2
    },
    "history": [],             # 每次 update 的追加轨迹（断点续接的时间线）
    "updated_at": None,
}

LOOPBACK_MAX = 2               # S-E10：全局回流上限，超限升级 L4 用户裁决

PHASE_NEXT = {
    0: "Phase 1: TRIZ问题建模（contradiction-analyst）",
    1: "Phase 2: 原理引导与创意生成（contradiction-analyst）",
    2: "Phase 3: 三轮查新（patent-search-scout，≥3轮）",
    2.5: "Phase 2.5: 汇聚校准（R1结果×Phase1-2方向比对，主理人亲执）",  # S-E19
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
    """支持点路径赋值：phase / gates.G1 / verdicts.examiner.result / conditions.K1

    CYCLE-1 · S-E01：gates.G1..G5 为别名，自动归一到语义标准键（唯一真源 GATE_ALIASES），
    防止编号键与语义键双轨并存导致门禁永远关不掉。
    """
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
    # 门禁别名归一（仅 gates.Gn 形态）
    if len(keys) == 2 and keys[0] == "gates" and keys[1] in GATE_ALIASES:
        keys[1] = GATE_ALIASES[keys[1]]
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
    # CYCLE-1 · S-E01/S-E02：门禁按 G1-G5 契约逐项显示标准键真值（含 G2 三性通过）
    g = state.get("gates", {})
    gate_line = " | ".join(
        f"{gn}={'✅' if g.get(sem) else '⛔'}" for gn, sem in GATE_ALIASES.items())
    print(f"   G1-G5：{gate_line}")
    print(f"   回流计数：{state.get('metrics', {}).get('loopback_count', 0)}/{LOOPBACK_MAX}"
          + (" ⛔ 已达上限→升级 L4 用户裁决" if state.get('metrics', {}).get('loopback_count', 0) >= LOOPBACK_MAX else ""))
    # S-E18：查新未完成时禁止推进 Phase 4/5（机械拦截，非散文）
    if phase >= 3 and not g.get("search_3rounds_complete"):
        print("   ⛔ 阻断：三轮查新未完成（G1=false），禁止进入 Phase 4/5；须重跑 R1-R3")
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


def cmd_reset_for_rework(args):
    """CYCLE-1 · S-E18 硬闸门：Phase 3/4 裁决→退回 Phase 2 二次改进时，
    机械重置查新进度与全部门禁（防止改后方案未经重新三轮查新即进 Phase4/5），
    并累计 loopback_count；超 LOOPBACK_MAX 时 exit 2 要求升级 L4 用户裁决。

    用法：python3 scripts/state_store.py reset_for_rework --run-dir <RUN_DIR> --reason "查新红/4条X级"
    """
    state, err = load_state(args.run_dir)
    if err:
        print(f"❌ {err}")
        return 1
    n = state.get("metrics", {}).get("loopback_count", 0)
    if n >= LOOPBACK_MAX:
        print(f"⛔ 回流已达上限 {n}/{LOOPBACK_MAX}——按 H3/S-E10 升级 L4 用户裁决，"
              f"禁止再次退回 Phase 2（防无限循环与预算耗尽）")
        return 2
    state["phase"] = 2
    state["search_rounds"] = 0
    for sem in GATE_ALIASES.values():
        state["gates"][sem] = False
    state["metrics"]["loopback_count"] = n + 1
    state["conflicts"].append({
        "type": "rework_reset", "reason": args.reason, "loopback": n + 1,
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    })
    save_state(args.run_dir, state, note=f"reset_for_rework（{args.reason}）→ 重跑 R1-R3")
    print(f"✅ 已重置：phase=2 / search_rounds=0 / G1-G5 全 false / loopback={n+1}/{LOOPBACK_MAX}")
    print("   ⚠ 下一动作强制：Phase 2 二次改进 → **重跑 Phase 3 三轮查新（R1-R3）** → 重新 Phase 4")
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
        # 2) update 嵌套键（用 G1 别名，验证归一）
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
            ("G1别名归一→标准键", state["gates"]["search_3rounds_complete"] is True),
            ("无G1野键", "G1" not in state["gates"]),
            ("G2落点存在", "trinity_verdict_pass" in state["gates"]),
            ("loopback_count=0", state["metrics"]["loopback_count"] == 0),
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
        # 5) CYCLE-1：G1-G5 全别名写入 → 标准键全 true（S-E01 回归防线）
        r = subprocess_run([sys.executable, os.path.abspath(__file__), "update",
                            "--run-dir", td] + sum([["--set", f"gates.G{i}=true"] for i in range(1, 6)], []))
        ok &= (r == 0)
        state, _ = load_state(td)
        all_closed = all(state["gates"].get(sem) is True for sem in GATE_ALIASES.values())
        no_wild = not any(k in state["gates"] for k in GATE_ALIASES)
        print(f"  {'✅' if all_closed else '❌'} G1-G5 别名写入→5 标准键全 true")
        print(f"  {'✅' if no_wild else '❌'} 无编号野键")
        ok &= all_closed and no_wild
        # 6) CYCLE-1：reset_for_rework 机械重置（S-E18）
        r = subprocess_run([sys.executable, os.path.abspath(__file__), "reset_for_rework",
                            "--run-dir", td, "--reason", "self-test 探针"])
        ok &= (r == 0)
        state, _ = load_state(td)
        reset_ok = (state["phase"] == 2 and state["search_rounds"] == 0
                    and all(not state["gates"].get(sem) for sem in GATE_ALIASES.values())
                    and state["metrics"]["loopback_count"] == 1)
        print(f"  {'✅' if reset_ok else '❌'} reset_for_rework：phase=2/查新清零/G全false/回流+1")
        ok &= reset_ok
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

    p6 = sub.add_parser("reset_for_rework", help="退回Phase2二次改进：机械重置查新与门禁（S-E18）")
    p6.add_argument("--run-dir", required=True)
    p6.add_argument("--reason", required=True, help="退回原因（如 查新红/4条X级/审查红）")

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
    if args.cmd == "reset_for_rework":
        return cmd_reset_for_rework(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
