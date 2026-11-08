#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight_check.py — 团队启动前检查清单脚本化（2026-10-14 建立，P1-5）

问题：主理人 MD 有「团队启动前检查清单」4 项，但它是**散文条款**——
靠主理人每次自觉逐条过。可执行性差 = 实际上没人跑（与 9-30 诊断"协议上线但零落盘"
同一失效模式）。本脚本把 4 项里**可机械判定**的部分变成一次命令，
并把 failure-007 教训（权威数据未经校验就注入上下文）也纳入必检。

检查项：
  1. 失败索引可查（expert-failures 目录 + index.md 可读 + 按关键词命中相关记录）
  2. docs/routing-log.md 可写（路由决策落盘点）
  3. 预算估算：成员数 × 单成员预估 token ≤ 全局预算 120K
  4. Phase 0 需求卡五参数：从 --task-file 解析（缺则列出缺项，不阻断但必须显式确认）
  5. 权威数据自检：调 scripts/verify_triz_data.py（防 failure-001/007 复发）
  6. 装配器可用：scripts/assemble_spawn_prompt.py 存在且可执行（shared-core 可达）
  7. 成员声明的预加载 skills 在磁盘上确实存在（防"声明了但路径是编的"）

用法：
  python3 scripts/preflight_check.py [--expert-dir DIR] [--members a,b,c] [--task-file F] [--keywords 词1,词2]
  python3 scripts/preflight_check.py --members contradiction-analyst,patent-search-scout --task-file /tmp/task.md

退出码：0=可启动（含 warn）  1=存在阻断项（BLOCK）  2=用法/环境错误
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

GLOBAL_TOKEN_BUDGET = 120_000          # H3.5 全流程 token 上限
# 经验值（2026-11-07 Batch3 · 修 S-R1）：按 L2 实测 83.8K 校准（原值偏差 ~1.3×，
# 6 成员常态触 92% 预警，信噪比下降）。校准口径：tests/baselines/l2-full-a01 metrics.jsonl 汇总。
DEFAULT_MEMBER_TOKENS = {
    # 与成员 MD 的 maxTurns 量级对应（L2 实测均值·仅用于预算估算，非计量）
    "patent-search-scout": 19_000,      # maxTurns 80，检索型最重
    "contradiction-analyst": 17_000,    # maxTurns 50（含 RED 回退迭代余量）
    "patent-examiner-sim": 15_000,      # maxTurns 40
    "second-opinion-reviewer": 13_000,  # maxTurns 40
    "disclosure-architect": 10_000,     # maxTurns 30
    "patent-attorney-writer": 10_000,   # maxTurns 30
}
FALLBACK_TOKENS = 15_000

# Phase 0 需求卡·工程实施参数清单（装置/系统类发明必填）
PHASE0_PARAMS = [
    ("安装/埋置方式", ["埋地", "埋于", "埋置", "明装", "架空", "吊装", "敷设", "可拆卸", "安装方式"]),
    ("可接受改造成本量级", ["改造成本", "成本量级", "≤", "%", "总投资"]),
    ("维护频次预期", ["维护频次", "免维护", "季检", "年检"]),
    ("失效后果容忍度", ["失效后果", "容忍度", "最坏", "可接受"]),
    ("已有部件清单", ["已有部件", "可复用", "必换", "部件清单"]),
]

BLOCK, WARN, OK = [], [], []


def blk(m):
    BLOCK.append(m)


def wrn(m):
    WARN.append(m)


def ok(m):
    OK.append(m)


def check_failure_index(keywords):
    """1. 失败索引可查 + 命中相关记录"""
    base = os.path.expanduser("~/.workbuddy/expert-failures")
    if not os.path.isdir(base):
        blk("1. 失败索引目录不存在：%s（无法走防重复犯路径）" % base)
        return
    idx = os.path.join(base, "index.md")
    if not os.path.isfile(idx):
        blk("1. 失败索引 index.md 缺失")
        return
    ok("1. 失败索引可读：%s" % base)
    if not keywords:
        wrn("1. 未传 --keywords，只验证了索引可读，未检索相关失败记录（建议按任务域传入关键词）")
        return
    hits = []
    for f in sorted(os.listdir(base)):
        if not (f.startswith("failure-") and f.endswith(".json")):
            continue
        try:
            d = json.load(open(os.path.join(base, f), encoding="utf-8"))
        except Exception:
            continue
        blob = json.dumps(d, ensure_ascii=False)
        if any(k in blob for k in keywords):
            hits.append((f, d.get("id"), d.get("fail_type"),
                         (d.get("learned_rule") or "")[:70]))
    if hits:
        ok("1. 命中相关失败记录 %d 条（任务前必读其 learned_rule）：" % len(hits))
        for f, i, t, lr in hits:
            print("       - %s [%s] %s…" % (i or f, t, lr))
    else:
        ok("1. 无相关失败记录命中（关键词：%s）" % "、".join(keywords))


def check_routing_log():
    """2. routing-log 可写"""
    p = os.path.join(PKG, "docs", "routing-log.md")
    if not os.path.isfile(p):
        blk("2. docs/routing-log.md 不存在——路由决策无落盘点")
        return
    if not os.access(p, os.W_OK):
        blk("2. docs/routing-log.md 不可写——本轮所有派单无法落盘")
        return
    ok("2. docs/routing-log.md 可写")
    # 顺带检查表头是否已含「结果」列（P1-4 新增）
    # 注意：不能取文件前 N 行——文件开头是标题与填写规范引用块，取到的是说明文字而非表头
    header_line = ""
    for line in open(p, encoding="utf-8"):
        if line.strip().startswith("|") and "decision_id" in line:
            header_line = line
            break
    if not header_line:
        wrn("2. routing-log 未找到含 decision_id 的表头行")
    elif "结果" not in header_line:
        wrn("2. routing-log 表头未含「结果」列——派单后无法回填，可复盘性受损")


def check_budget(members):
    """3. 预算估算"""
    if not members:
        wrn("3. 未传 --members，跳过预算估算（建议在派单前明确成员清单）")
        return
    est = sum(DEFAULT_MEMBER_TOKENS.get(m, FALLBACK_TOKENS) for m in members)
    ratio = est / GLOBAL_TOKEN_BUDGET
    flag = "OK  " if ratio <= 0.8 else ("WARN" if ratio <= 1.0 else "OVER")
    msg = ("3. 预算估算：%d 成员 × 经验值 = %s token，占全局预算 %.0f%%（上限 %s）"
           % (len(members), f"{est:,}", ratio * 100, f"{GLOBAL_TOKEN_BUDGET:,}"))
    if ratio > 1.0:
        blk(msg + " —— 超全局预算，必须裁剪成员或降级 Workflow 后再启动")
    elif ratio > 0.8:
        wrn(msg + " —— 超 80%，H3.5 要求向用户预警")
    else:
        ok(msg + " [估算口径：经验值，非实测；实测计量见 P1-8]")
    unknown = [m for m in members if m not in DEFAULT_MEMBER_TOKENS]
    if unknown:
        wrn("3. 成员 %s 无经验值，按 %s 兜底估算" % (unknown, FALLBACK_TOKENS))


def check_phase0(task_file):
    """4. Phase 0 需求卡五参数"""
    if not task_file:
        wrn("4. 未传 --task-file，跳过 Phase 0 五参数检查（装置/系统类发明必须补齐）")
        return
    if not os.path.isfile(task_file):
        blk("4. --task-file 不存在：%s" % task_file)
        return
    t = open(task_file, encoding="utf-8").read()
    missing = [name for name, kws in PHASE0_PARAMS if not any(k in t for k in kws)]
    if missing:
        wrn("4. Phase 0 工程实施参数缺失 %d/5：%s —— 需在需求卡补齐或显式标注「待定」"
            % (len(missing), "、".join(missing)))
    else:
        ok("4. Phase 0 工程实施参数 5/5 齐全")


def check_authoritative_data():
    """5. 权威数据自检（防 failure-001/007 复发）"""
    v = os.path.join(HERE, "verify_triz_data.py")
    if not os.path.isfile(v):
        wrn("5. verify_triz_data.py 缺失，权威数据未校验")
        return
    r = subprocess.run([sys.executable, v, "--expert-dir", PKG],
                       capture_output=True, text=True)
    if r.returncode == 0:
        ok("5. 权威数据自检通过（矩阵1521 / 参数39 / 中文表一致无重复 / 锚点复算）")
    else:
        blk("5. 权威数据自检未通过——错误会经查询器注入成员上下文：\n       %s"
            % (r.stdout or r.stderr).strip().replace("\n", "\n       "))


def check_assembler():
    """6. 装配器可用（shared-core 可达）"""
    a = os.path.join(HERE, "assemble_spawn_prompt.py")
    if not os.path.isfile(a):
        blk("6. assemble_spawn_prompt.py 缺失——无法做确定性人设注入")
        return
    r = subprocess.run([sys.executable, a, "--list-members"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        blk("6. 装配器不可运行（shared-core 未找到？）：%s"
            % (r.stderr or r.stdout).strip()[:200])
        return
    n = len([x for x in r.stdout.split("\n") if x.strip()])
    ok("6. 装配器可用，成员白名单 %d 个" % n)


def check_declared_skills():
    """7. 成员声明的预加载 skills 是否存在（防声明了但路径是编的）"""
    agents = os.path.join(PKG, "agents")
    if not os.path.isdir(agents):
        blk("7. agents/ 目录缺失")
        return
    missing = []
    checked = 0
    for f in sorted(os.listdir(agents)):
        if not f.endswith(".md"):
            continue
        txt = open(os.path.join(agents, f), encoding="utf-8").read()
        for m in re.finditer(r"`(skills/[^`]+/SKILL\.md)`", txt):
            rel = m.group(1)
            checked += 1
            if not os.path.isfile(os.path.join(PKG, rel)):
                missing.append((f, rel))
    if missing:
        blk("7. 成员 MD 声明了 %d 个不存在的 skill 路径：" % len(missing)
            + "; ".join("%s→%s" % x for x in missing))
    else:
        ok("7. 成员声明的 %d 处 skill 路径全部存在于磁盘" % checked)


def check_c3_trigger(member_id, outputs_dir, x_grade_count, c3_path):
    """P0-S3-1: C3 检查点自动触发

    当指定成员（默认 patent-search-scout）在 outputs_dir 下的最新产出信封
    含 X 级文献时，必须提供 c3_path（指向 C3 确认文件）；
    无该文件则 exit 1（阻断）。
    """
    if member_id != "patent-search-scout" or x_grade_count == 0:
        return
    if not c3_path:
        BLOCK.append("8. C3 检查点：X 级出现 %d 条但未提供 --c3-confirmation-path" % x_grade_count)
        return
    if not os.path.isfile(c3_path):
        BLOCK.append("8. C3 检查点：%s 文件不存在" % c3_path)
        return
    # 校验确认文件含必要字段（C3_CONFIRMATION 模板）
    text = open(c3_path, encoding="utf-8").read()
    for marker in ["C3 检查点确认", "同意按"]:
        if marker not in text:
            BLOCK.append("8. C3 检查点：%s 缺关键标记「%s」" % (c3_path, marker))
            return
    OK.append("8. C3 检查点：%d 条 X 级已确认（%s）" % (x_grade_count, c3_path))


def scan_x_grade(member_id, outputs_dir):
    """扫指定成员最新产出，统计 X 级文献数（从 threat_list 段）"""
    if not member_id or not os.path.isdir(outputs_dir):
        return 0
    # 找最新落盘
    pattern = os.path.join(outputs_dir, "T-*__" + member_id + ".md")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        return 0
    text = open(files[0], encoding="utf-8").read()
    # 找 threat_list 段（scout A01 风格：X 1, Y 12, A 12 等）
    # 简易：X 后跟数字
    import re as _re
    m = _re.search(r"X\s*[\W_]*\s*(\d+)", text)
    if m:
        return int(m.group(1))
    # 备用：从"X 级"统计
    return len(_re.findall(r"X\s*级", text))


def main():
    global PKG, HERE, args
    ap = argparse.ArgumentParser(description="团队启动前检查（preflight）")
    ap.add_argument("--expert-dir", default=PKG)
    ap.add_argument("--members", default="", help="逗号分隔的成员 ID 清单，用于预算估算")
    ap.add_argument("--task-file", default="", help="Phase 0 需求卡/任务包路径")
    ap.add_argument("--keywords", default="", help="逗号分隔关键词，用于检索失败索引")
    ap.add_argument("--after-search", help="[P0-S3-1] 上一阶段查新成员的 member_id（默认 patent-search-scout）")
    ap.add_argument("--outputs-dir", default="", help="[P0-S3-1] 查新产出所在目录")
    ap.add_argument("--c3-confirmation-path", default="", help="[P0-S3-1] C3 确认文件路径（X 级出现时强制要求）")
    args = ap.parse_args()

    PKG = os.path.abspath(args.expert_dir)
    HERE = os.path.join(PKG, "scripts")

    members = [m.strip() for m in args.members.split(",") if m.strip()]
    kws = [k.strip() for k in args.keywords.split(",") if k.strip()]

    print("🚦 preflight check — %s" % PKG)
    check_failure_index(kws)
    check_routing_log()
    check_budget(members)
    check_phase0(args.task_file)
    check_authoritative_data()
    check_assembler()
    check_declared_skills()

    # P0-S3-1: C3 自动触发
    if args.outputs_dir:
        after_member = args.after_search or "patent-search-scout"
        x_count = scan_x_grade(after_member, args.outputs_dir)
        if x_count > 0:
            check_c3_trigger(after_member, args.outputs_dir, x_count, args.c3_confirmation_path)

    print("\n———— 结果 ————")
    for m in OK:
        print("  ✅ %s" % m)
    for m in WARN:
        print("  ⚠️  %s" % m)
    for m in BLOCK:
        print("  ❌ %s" % m)
    if BLOCK:
        print("\n结论：存在 %d 项阻断，禁止建队。先修复再启动。" % len(BLOCK))
        return 1
    print("\n结论：可启动（警告 %d 项，需主理人显式确认后继续）。" % len(WARN))
    return 0


if __name__ == "__main__":
    args = None  # 让 check_c3_trigger 能访问
    sys.exit(main())
