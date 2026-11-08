#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spawn_watchdog.py — 成员停滞看门狗（简版 · 2026-11-08 残留清偿 #5 / P2-15 落地）
================================================================================
背景：H4「成员超时/停滞」规则（>10min 未落盘且无进度信号 → 催办→TaskStop→紧凑brief重试）
此前为纯散文条款，靠主理人人工计时。本脚本把"检测"部分机械化：

  主理人 spawn 成员后记录 spawn 时刻，等待窗口内随时调用：
      python3 scripts/spawn_watchdog.py --run-dir <RUN_DIR> --member <member-id> --spawned-at "<ISO时间>"
  输出四态判定 + H4 对应处置建议（催办/TaskStop/brief重试/升级），供主理人照单执行。

判定口径（与 H4 硬规则一致）：
  - 落盘文件 = <run-dir>/<task_id 或 T-*>__<member>.md（任一即算交付，无需等 SendMessage）
  - 产出文件 mtime > spawned_at → 已落盘 → OK
  - 等待 <10min → WATCH（继续等）
  - 10-30min 未落盘 → STALL（催办：SendMessage 限时+可 partial 落盘）
  - >30min 未落盘 → TIMEOUT（TaskStop 取消 + 紧凑 brief 重试，Loop 预算 ≤3）

退出码：0=OK/WATCH/STALL（不阻断） 1=TIMEOUT（提醒主理人处置） 2=用法错
设计边界：只做确定性时间/文件判定，"是否有进度信号"的语义判断仍归主理人。
"""
import argparse
import datetime
import glob
import os
import sys

WARN_MIN = 10      # H4：>10min 未落盘且无进度信号 → 催办
STOP_MIN = 30      # 实测教训（2026-10-15 A02 30m18s）：30min 仍无产出 → 取消重试


def _parse_iso(s):
    return datetime.datetime.fromisoformat(s)


def main():
    ap = argparse.ArgumentParser(description="spawn 停滞看门狗（H4 检测机械化）")
    ap.add_argument("--run-dir", required=True, help="成员落盘运行目录")
    ap.add_argument("--member", required=True, help="成员 ID（如 contradiction-analyst）")
    ap.add_argument("--spawned-at", required=True, help='spawn 时刻 ISO（如 "2026-11-08T10:00:00"）')
    ap.add_argument("--task-id", default=None, help="可选：精确 task_id（默认匹配任意 T-*__member.md）")
    args = ap.parse_args()

    try:
        spawned = _parse_iso(args.spawned_at)
    except ValueError as e:
        print(f"❌ --spawned-at 格式错误: {e}（示例 2026-11-08T10:00:00）")
        return 2

    now = datetime.datetime.now()
    elapsed_min = (now - spawned).total_seconds() / 60

    # 落盘检测：T-*__<member>.md（可选限定 task_id），mtime 晚于 spawn 时刻才算新产出
    pattern = os.path.join(args.run_dir, f"{args.task_id or 'T-*'}__{args.member}.md")
    candidates = [p for p in glob.glob(pattern)
                  if datetime.datetime.fromtimestamp(os.path.getmtime(p)) > spawned]

    if candidates:
        latest = max(candidates, key=os.path.getmtime)
        size = os.path.getsize(latest)
        waited = (datetime.datetime.fromtimestamp(os.path.getmtime(latest)) - spawned).total_seconds() / 60
        print(f"✅ OK — 已落盘：{os.path.basename(latest)}（{size} bytes，spawn 后 {waited:.1f}min）")
        print("   → 走正常 VERIFY 流程（墙钟回填 + contract_enforce + token_budget_check --meter）")
        return 0

    if elapsed_min < WARN_MIN:
        print(f"👀 WATCH — 等待 {elapsed_min:.1f}min（<{WARN_MIN}min 正常窗口）")
        print(f"   → 继续等待；利用窗口做预装配（下一位成员 preflight / spawn 文案 / 上游预读，P2-10）")
        return 0
    if elapsed_min < STOP_MIN:
        print(f"⏰ STALL — {elapsed_min:.1f}min 未落盘（≥{WARN_MIN}min 触发催办）")
        print(f"   → H4 步骤①：SendMessage 催办（限时 N 分钟 + 『可 partial 落盘』指令）")
        print(f"   → 提示：确认产出路径契约是否清晰（{pattern}）；成员可能在读超大上游文件")
        return 0
    print(f"🔴 TIMEOUT — {elapsed_min:.1f}min 未落盘（≥{STOP_MIN}min）")
    print(f"   → H4 步骤②：TaskStop 取消该成员 → 步骤③：按 H1 大产出压缩规则重建紧凑 brief 重试")
    print(f"     （禁读超大文件 / 查询数上限 / 限时；Loop 预算 ≤3；实测 30min 停滞→brief 重试 2m40s 通过）")
    print(f"   → 3 次仍失败：按 H4 Loop 降级路径分类处置（检索/撰写→代执行标注；创意/分析→partial 落盘；终评→升级用户）")
    print(f"   → 记 failure-xxx（fail_type: spawn_stall）+ routing-log 补 retry_loop 决策行")
    return 1


if __name__ == "__main__":
    sys.exit(main())
