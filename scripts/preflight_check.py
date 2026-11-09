#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight_check.py — 团队启动前检查清单脚本化（2026-10-14 建立，P1-5）

问题：主理人 MD 有「团队启动前检查清单」4 项，但它是**散文条款**——
靠主理人每次自觉逐条过。可执行性差 = 实际上没人跑（与 9-30 诊断"协议上线但零落盘"
同一失效模式）。本脚本把 4 项里**可机械判定**的部分变成一次命令，
并把 failure-007 教训（权威数据未经校验就注入上下文）也纳入必检。

检查项（共 15 项，S-E34 补全至与实现一致，S-E48 补第 14 项，S-E49 补第 15 项）：
  1. 失败索引可查（expert-failures 目录 + index.md 可读 + 按关键词命中相关记录）
  2. docs/routing-log.md 可写（路由决策落盘点）
  3. 预算估算：成员数 × 单成员预估 token ≤ 全局预算 120K
  4. Phase 0 需求卡五参数：从 --task-file 解析（缺则列出缺项，不阻断但必须显式确认）
  5. 权威数据自检：调 scripts/verify_triz_data.py（防 failure-001/007 复发）
  6. 装配器可用：scripts/assemble_spawn_prompt.py 存在且可执行（shared-core 可达）
  7. 成员声明的预加载 skills 在磁盘上确实存在（防"声明了但路径是编的"）
  8. 成员信封 schema 契约版本可解析（agent-protocol / result_envelope）
  9. 成员数口径核对（6 成员 + 1 主理人 = 7，防派单漏人/多派人）
  10. docs/diagnosis-protocol.md §六 诊断登记表结构完整（表头 + 数据行列数一致）
  11. README.zh.md 结构图与 git 实际入库顶层项一致（按 .gitignore 解析后比对）
  12. Workflow D 入口前置闸：G1/G2/G3 全关 + 查新与裁决证据文件真实落盘
  13. state 模板三处真源一致性：代码真源（state_store.STATE_TEMPLATE）↔ 文档真源
      （architecture.md §3.2）↔ SOP 真源（主理人 MD 状态块模板）——双向差集必须为空
  14. routing-log 表头列数 ↔ 数据行列数 ↔ SOP RoutingDecision 字段数三者一致
      （契约漂移检测：表头漏列 → Markdown 渲染错位，「结果」列失效）
  15. task_id 契约一致性：信封 schema ↔ 任务包 schema pattern 字面相同，
      且能匹配实测基线的 task_id 形态 + 任务包 schema 至少被一处代码消费（反幽灵契约）

用法：
  python3 scripts/preflight_check.py [--expert-dir DIR] [--members a,b,c] [--task-file F] [--keywords 词1,词2]
  python3 scripts/preflight_check.py --members contradiction-analyst,patent-search-scout --task-file /tmp/task.md
  python3 scripts/preflight_check.py --state-path outputs/moheng-state-<task_id>.json   # 派 Workflow D 前必传

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


def check_diagnosis_registry():
    """10. 诊断登记表结构完整性（CYCLE-1 · S-E05 断表修复的复发检测）
    判据：§六 登记表内数据行不得夹空行（断表 = 表格被空行切断，Markdown 渲染断裂），
    且每行列数须与表头一致。"""
    p = os.path.join(PKG, "docs", "diagnosis-protocol.md")
    if not os.path.isfile(p):
        wrn("10. docs/diagnosis-protocol.md 不存在——跳过登记表结构校验")
        return
    lines = open(p, encoding="utf-8").read().split("\n")
    # 定位 §六 登记表区间
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("## 六"):
            start = i
            break
    if start is None:
        wrn("10. 未找到 §六 诊断登记表小节——跳过结构校验")
        return
    # 表头行 = 区间内第一条含「日期」且以 | 开头的行
    header_idx = None
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if s.startswith("|") and "日期" in s and "触发器" in s:
            header_idx = i
            break
    if header_idx is None:
        wrn("10. §六 未找到登记表表头行——跳过结构校验")
        return
    ncol = lines[header_idx].strip().strip("|").count("|") + 1
    problems = []
    data_rows = 0
    for i in range(header_idx + 2, len(lines)):
        s = lines[i].strip()
        if not s:
            # 空行：允许在表格末尾之后（遇到非表格内容即止），表格内部空行 = 断表
            # 判定方式：向下找下一条非空行，若仍是表行 → 中间断表
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip().startswith("|"):
                problems.append(f"L{i+1}: 表内空行（表格断裂）")
            break
        if s.startswith("|"):
            data_rows += 1
            c = s.strip("|").count("|") + 1
            if c != ncol:
                problems.append(f"L{i+1}: 列数 {c} ≠ 表头 {ncol}")
    if problems:
        for pr in problems:
            blk(f"10. 诊断登记表结构异常——{pr}")
    else:
        ok(f"10. 诊断登记表结构完整（{data_rows} 行数据·{ncol} 列）")


def check_state_template_consistency():
    """13. state 模板三处真源一致性（CYCLE-1 · S-E43）。

    **根因**：state 模板此前在**三处手抄**——`scripts/state_store.py` 的 `STATE_TEMPLATE`
    （代码真源）· `docs/architecture.md` §3.2（文档真源）· `agents/*-team-lead.md`
    （主理人 SOP 的状态块模板）。三处**无任何机械校验** → 任一处漏字段都静默漂移。

    **实测事故（S-E42）**：主理人 MD 的状态块模板写 `metrics: {duration_ms, agent_calls}`，
    **漏掉 `duration_ms_wall` + `duration_source`** → 成员照此输出 → 墙钟永远缺失 →
    `agent_ci_gate.check_wall_clock()` 只能永远发 WARN，收不到回填后的墙钟。
    即 S-E25「墙钟双轨制」**未真正下沉到 SOP**，只在架构文档里存在。

    **本项判据**（机械比对三处字段集合，双向差集必须为空）：
      T1 代码真源 `state_store.STATE_TEMPLATE` 的 gates/evidence/metrics 键集合
      T2 文档真源 `docs/architecture.md` §3.2 JSON 代码块的同名键集合
      T3 SOP 真源 主理人 MD 状态块模板中的字段名
    任一缺失 → BLOCK（这是**契约漂移**，不是文档整洁度问题，必须阻断）。
    """
    import json as _json
    import re as _re

    def _read_text(path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    # --- T1 代码真源 ---
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import state_store as _ss
        tpl = _ss.STATE_TEMPLATE
        code_gates = set(tpl.get("gates", {}).keys())
        code_evidence = set(tpl.get("evidence", {}).keys())
        code_metrics = set(tpl.get("metrics", {}).keys())
    except Exception as e:
        blk("13. 无法载入 state_store.STATE_TEMPLATE（代码真源）：%s" % e)
        return

    # --- T2 文档真源：architecture.md §3.2 的 JSON 代码块 ---
    arch = os.path.join(PKG, "docs", "architecture.md")
    if not os.path.isfile(arch):
        blk("13. docs/architecture.md 不存在——无法校验文档真源（state 模板契约漂移）")
        return
    atext = _read_text(arch)
    blocks = _re.findall(r"```json\s*(.*?)```", atext, _re.S)
    doc = None
    for b in blocks:
        if '"gates"' in b and '"metrics"' in b:
            doc = b
            break
    if doc is None:
        blk("13. architecture.md 中未找到含 gates+metrics 的 JSON 模板代码块——"
            "文档真源无法解析（契约漂移）")
        return

    def _keys_in(section, text):
        """从文本中取某 section 的键名集合（括号配平，不依赖 JSON 可解析性）。

        架构文档的模板含 `"phase": 0-5` 这类**示意值**（非法 JSON），
        故不能用 json.loads —— 改用括号配平 + 正则提键。
        """
        m = _re.search(r'"%s"\s*:\s*\{' % section, text)
        if not m:
            return None
        i = m.end() - 1
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    inner = text[i + 1:j]
                    return set(_re.findall(r'"([^"]+)"\s*:', inner))
        return None

    doc_gates = _keys_in("gates", doc)
    doc_evidence = _keys_in("evidence", doc)
    doc_metrics = _keys_in("metrics", doc)
    for nm, kv in (("gates", doc_gates), ("evidence", doc_evidence),
                   ("metrics", doc_metrics)):
        if kv is None:
            blk("13. architecture.md 模板中未找到 %s 段——文档真源无法解析（契约漂移）" % nm)
            return

    # --- T3 SOP 真源：主理人 MD 状态块模板 ---
    md = os.path.join(PKG, "agents", "triz-invention-team-team-lead.md")
    if not os.path.isfile(md):
        blk("13. 主理人 MD 不存在——无法校验 SOP 真源（state 模板契约漂移）")
        return
    mtext = _read_text(md)
    # 括号配平提取 TASK_STATE 块（正则 `\{[^}]*\}` 会在**内层** `}` 处截断，
    # 导致 evidence/metrics 等嵌套段被误判为缺失 —— 必须配平）
    _mi = mtext.find("TASK_STATE:")
    sop = ""
    if _mi >= 0:
        _bs = mtext.find("{", _mi)
        if _bs >= 0:
            depth = 0
            for _j in range(_bs, len(mtext)):
                if mtext[_j] == "{":
                    depth += 1
                elif mtext[_j] == "}":
                    depth -= 1
                    if depth == 0:
                        sop = mtext[_bs:_j + 1]
                        break
    if not sop:
        blk("13. 主理人 MD 中未找到 TASK_STATE 状态块模板——SOP 真源无法解析（契约漂移）")
        return

    # --- 双向差集比对（缺一即漂移）---
    problems = []
    for name, code_set, doc_set in (
        ("gates", code_gates, doc_gates),
        ("evidence", code_evidence, doc_evidence),
        ("metrics", code_metrics, doc_metrics),
    ):
        miss_doc = sorted(code_set - doc_set)
        extra_doc = sorted(doc_set - code_set)
        if miss_doc:
            problems.append("文档缺 %s：%s" % (name, "、".join(miss_doc)))
        if extra_doc:
            problems.append("文档多 %s：%s" % (name, "、".join(extra_doc)))

    # SOP 侧：逐个代码真源字段名必须在状态块模板中出现
    for name, keys in (("gates", code_gates), ("evidence", code_evidence),
                       ("metrics", code_metrics)):
        for k in sorted(keys):
            if k not in sop:
                problems.append("SOP 状态块模板缺 %s.%s" % (name, k))

    if problems:
        blk("13. state 模板三处真源漂移（代码真源 = state_store.STATE_TEMPLATE）："
            + "；".join(problems) + " —— 以代码真源为准修文档/SOP，不得反向放宽真源")
        return
    ok("13. state 模板三处真源一致（gates %d / evidence %d / metrics %d 键·"
       "代码↔文档↔SOP 双向差集为空）"
       % (len(code_gates), len(code_evidence), len(code_metrics)))


def check_routing_log_columns():
    """14. routing-log 表头列数 ↔ 数据行列数一致性（CYCLE-1 · S-E48）。

    **根因（S-E43 同型：契约漂移）**：`RoutingDecision` 契约在**三处手抄**——
      T1 SOP 真源：`agents/triz-invention-team-team-lead.md` 的 `RoutingDecision` JSON 块
      T2 落盘真源：`docs/routing-log.md` 的 Markdown 表头
      T3 数据行：routing-log 的每一条实际记录
    T1 定义了 **8 个字段**（含 `rationale_class`），T2 表头只声明 **7 列**
    （漏 `rationale_class`），T3 实际数据行写 **8 列** → 三处不对齐。

    **实测事故**：R-20261108-001（已入库于 7b6ffb8）与 R-20261108-002 两行均含
    `rule_match` 尾列，而表头无此列声明 → Markdown 渲染时该列**溢出表头**，
    读者按表头解读会误判第 6 列「结果」实为「理由」、第 7 列「理由」实为「未声明列」。
    这不是排版问题：**「结果」列是本表唯一可复盘字段（P1-4 规范）**，
    列错位等于让审计链失去可复盘性。

    **本项判据**（纯机械，不依赖人眼）：
      - 表头列数 = **所有**数据行列数（逐行核对）
      - 表头列名 ↔ 头部说明「字段：」声明行**逐位**对齐（数量 + 顺序）
      - 表头**不得**漏声明任何数据行实际存在的列

    **口径澄清**：SOP `RoutingDecision` JSON 有 8 字段（含 `rationale_class`），
    但 SOP「强制落盘规则」写明落盘只需「decision_id + target + confidence + 简述」——
    落盘表是**精简投影**，故对齐真源是**头部「字段：」行**，不是 SOP JSON 全字段。

    任一不满足 → BLOCK（契约漂移必须阻断，不是文档整洁度问题）。
    """
    p = os.path.join(PKG, "docs", "routing-log.md")
    if not os.path.isfile(p):
        wrn("14. docs/routing-log.md 不存在——跳过表头/数据行列数一致性校验")
        return

    lines = open(p, encoding="utf-8").read().split("\n")

    # --- 定位表头行与分隔行 ---
    hdr_idx = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("|") and "decision_id" in s and "timestamp" in s:
            hdr_idx = i
            break
    if hdr_idx is None:
        blk("14. routing-log 未找到表头行（含 decision_id+timestamp）——"
            "无法校验列契约（契约漂移）")
        return
    if hdr_idx + 1 >= len(lines) or not re.match(r"^\|[\s\-:|]+\|?$",
                                                 lines[hdr_idx + 1].strip()):
        blk("14. routing-log 表头下方缺 Markdown 分隔行——表格结构损坏")
        return

    def _cells(ln):
        s = ln.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    hdr_cells = _cells(lines[hdr_idx])
    n_hdr = len(hdr_cells)

    # --- 收集数据行 ---
    data_rows = []
    for i in range(hdr_idx + 2, len(lines)):
        s = lines[i].strip()
        if not s.startswith("|"):
            continue
        cells = _cells(lines[i])
        if not cells or not re.match(r"^R-\d{8}-\d{3}$", cells[0]):
            continue
        data_rows.append((i + 1, cells))

    if not data_rows:
        wrn("14. routing-log 无数据行——跳过列数一致性校验")
        return

    # --- 判据 1：所有数据行列数必须等于表头列数 ---
    bad = [(ln_no, len(c)) for ln_no, c in data_rows if len(c) != n_hdr]
    if bad:
        blk("14. routing-log 数据行列数与表头不一致（表头 %d 列）：%s"
            % (n_hdr, "；".join("第%d行=%d列" % (n, c) for n, c in bad)))
        return

    # --- 判据 2：表头列名集合 ↔ 头部说明「字段：」行声明的字段集合，双向差集为空 ---
    #
    # **口径澄清（重要）**：SOP 的 `RoutingDecision` JSON 有 8 个字段，但 SOP「强制落盘规则」
    # 明确写的是「一次任务一行，含 decision_id + target + confidence + 简述」——
    # 即落盘表是**精简投影**（7 列），**不要求全字段落盘**。
    # 故本项对齐的落盘契约真源是**头部说明「字段：」行**，而非 SOP JSON 全字段。
    # SOP JSON 只用于交叉参考（字段名出处），不作为列数判据。
    head_field_line = ""
    for ln in lines[:40]:
        if ln.strip().startswith("> 字段："):
            head_field_line = ln
            break
    if not head_field_line:
        wrn("14. routing-log 头部未找到「字段：」声明行——"
            "跳过落盘契约交叉核对（仅完成列数自洽校验）")
        ok("14. routing-log 表头 %d 列 ↔ %d 数据行列数自洽"
           % (n_hdr, len(data_rows)))
        return

    declared = head_field_line.split("：", 1)[1]
    declared = declared.replace("**", "")
    declared = [x.strip() for x in declared.split("/") if x.strip()]

    # 头部用中英混写（confidence / 结果 / 理由），表头同序 → 按位置对齐
    if len(declared) != n_hdr:
        blk("14. routing-log 头部「字段：」声明 %d 个（%s）↔ 表头 %d 列，数量不符"
            "（契约漂移）" % (len(declared), "/".join(declared), n_hdr))
        return
    pos_mismatch = []
    for i, (d, h) in enumerate(zip(declared, hdr_cells)):
        dn = d.replace("*", "").strip()
        hn = h.replace("*", "").strip()
        if dn != hn:
            pos_mismatch.append("第%d列 声明=%s 表头=%s" % (i + 1, dn, hn))
    if pos_mismatch:
        blk("14. routing-log 头部「字段：」与表头逐位不符：%s（契约漂移）"
            % "；".join(pos_mismatch))
        return

    ok("14. routing-log 表头 %d 列 ↔ %d 数据行列数自洽 ↔ 头部「字段：」声明 "
       "%d 字段逐位对齐（无漂移）"
       % (n_hdr, len(data_rows), len(declared)))


def check_task_id_contract():
    """15. task_id 契约四处真源一致（CYCLE-1 · S-E49 建，S-E54/S-E55 扩）。

    **根因（S-E43 同型：契约漂移）**：`task_id` 的取值格式在**多处手抄**——
      T1 信封真源：`skills/agent-protocol/result_envelope.schema.json`
      T2 任务包真源：`skills/agent-protocol/task_payload.schema.json`
      T3 文档真源：`skills/agent-protocol/SKILL.md` 字段规范表（S-E55 补入）
      T4 派生真源：`scripts/token_budget_check.py` 的文件名正则（S-E54 改为派生）

    **实测事故（S-E49）**：T1 = `^T-[0-9]{8}-[A-Za-z0-9]{1,8}$`（允许字母后缀），
    T2 = `^T-[0-9]{8}-[0-9]{3,}$`（**只允许纯数字**），T3 示例写 `T-YYYYMMDD-NNN`
    （纯数字口径）。而**实测基线全部采用字母后缀**（`T-20261015-A01` … `A07`，
    7 份成员信封 + 9 份 spawn 文档）→ 主理人按实测形态派单时，
    **若下游按 task_payload schema 校验任务包，必被拒绝**；而 payload schema
    **全仓零代码消费**（无人校验）→ 该冲突从未被任何门禁暴露（幽灵契约）。

    **实测事故（S-E55）**：S-E49 统一了两个 schema，却**漏掉 T3 文档真源**——
    SKILL.md 仍写旧 pattern。而 SKILL.md 是 agent **加载时就读**的真源 → agent
    按文档理解 task_id 口径（字母后缀非法），与代码强制的 schema 口径冲突。
    → 本项判据 4 把文档纳入机械校验，漂移立即暴露。

    **实测事故（S-E54）**：T4 `token_budget_check.FILENAME_RE` 是 pattern 的
    **第三份手抄**，schema 改了不跟随 → 文件名匹配静默失效，预算计量漏算产出。
    → 改为**从 schema 派生**（单一真源，schema 改了自动跟随），并由判据 5 反向校验。

    **本项判据**（纯机械）：
      - 判据 1：T1 与 T2 的 task_id pattern 必须**字面相同**（上行/下行契约必须同形）
      - 判据 2：两者必须能**实际匹配**实测基线中出现的 task_id 形态（用基线文件做样本）
      - 判据 3：task_payload.schema.json 至少被**本脚本以外**一处代码消费（反幽灵契约）
      - 判据 4：T3（SKILL.md）声明的 pattern 必须与 schema **字面相同**
      - 判据 5：T4 不得再手抄 pattern —— 必须是**从 schema 派生**（读 schema 的代码路径存在）
    """
    ap_dir = os.path.join(PKG, "skills", "agent-protocol")
    env_p = os.path.join(ap_dir, "result_envelope.schema.json")
    pay_p = os.path.join(ap_dir, "task_payload.schema.json")
    for p, nm in ((env_p, "result_envelope"), (pay_p, "task_payload")):
        if not os.path.isfile(p):
            blk("15. %s.schema.json 不存在——task_id 契约真源缺失" % nm)
            return

    def _pattern_of(path):
        try:
            obj = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            blk("15. %s 解析失败：%s" % (os.path.basename(path), e))
            return None
        props = obj.get("properties", {})
        t = props.get("task_id")
        if not isinstance(t, dict) or "pattern" not in t:
            blk("15. %s 未定义 task_id.pattern——契约字段缺失"
                % os.path.basename(path))
            return None
        return t["pattern"]

    env_re_p = _pattern_of(env_p)
    pay_re_p = _pattern_of(pay_p)
    if env_re_p is None or pay_re_p is None:
        return

    # --- 判据 1：两个 schema 的 pattern 必须字面相同 ---
    if env_re_p != pay_re_p:
        blk("15. task_id pattern 双真源冲突：信封 schema=`%s` ↔ 任务包 schema=`%s`"
            "（契约漂移，以信封 schema 为准）" % (env_re_p, pay_re_p))
        return

    # --- 判据 2：pattern 必须能匹配实测基线的 task_id 形态 ---
    samples = set()
    base = os.path.join(PKG, "tests", "baselines")
    for root, _dirs, files in os.walk(base):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            try:
                txt = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in re.finditer(r"\bT-\d{8}-[A-Za-z0-9]{1,8}\b", txt):
                samples.add(m.group(0))
    if not samples:
        wrn("15. 基线中未取到 task_id 样本——跳过样本匹配校验")
    else:
        try:
            rx = re.compile(env_re_p)
        except Exception as e:
            blk("15. task_id pattern 非法正则：%s" % e)
            return
        bad = sorted(s for s in samples if not rx.match(s))
        if bad:
            blk("15. task_id pattern 拒绝实测基线样本 %d 个（例 %s）——"
                "契约与实测形态脱节" % (len(bad), bad[0]))
            return

    # --- 判据 3（附加）：task_payload.schema.json 至少被**本脚本以外**一处代码消费 ---
    # 反幽灵契约：若零消费，下行任务契约无任何强制校验点，与信封 schema 的冲突无法被拦截。
    #
    # **判别力注意（S-E49 自查修正）**：本项若把 `preflight_check.py` 自身也算作消费方，
    # 则本脚本「自己给自己作证」——即使全仓其他代码都不消费，本项仍 PASS（假绿）。
    # 故**必须排除自身**，只认其它脚本的真实消费。
    consumed = []
    self_name = os.path.basename(__file__)
    for root, _dirs, files in os.walk(os.path.join(PKG, "scripts")):
        if "__pycache__" in root:
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            if f == self_name:
                continue          # 排除自身（反自指）
            fp = os.path.join(root, f)
            txt = open(fp, encoding="utf-8", errors="ignore").read()
            if "task_payload.schema.json" in txt:
                consumed.append(f)
    if not consumed:
        blk("15. task_payload.schema.json 全仓零代码消费（幽灵契约）——"
            "下行任务契约无任何强制校验点，与信封 schema 的冲突无法被拦截"
            "（注：本项已排除 preflight_check.py 自身，避免自证）")
        return

    # --- 判据 4（附加 · S-E55）：SKILL.md 文档真源的 task_id pattern 必须同步 ---
    # **实测事故（S-E55）**：S-E49 修复了「两个 schema pattern 冲突」，
    # 却**漏掉了第三处手抄**——skills/agent-protocol/SKILL.md 的字段规范表
    # 仍写旧 pattern `^T-[0-9]{8}-[0-9]{3,}$`（只允许纯数字）。
    # SKILL.md 是 agent **加载时就读**的真源 → agent 按文档理解 task_id 口径，
    # 与代码强制的 schema 口径不一致（字母后缀被判非法）。
    # 三处已统一（两 schema）而文档未同步 = 契约漂移复发。
    # 本判据把文档纳入机械校验，漂移立即暴露。
    skill_md = os.path.join(ap_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        blk("15. skills/agent-protocol/SKILL.md 不存在——文档真源缺失")
        return
    try:
        md_txt = open(skill_md, encoding="utf-8").read()
    except Exception as e:
        blk("15. SKILL.md 读取失败：%s" % e)
        return
    md_pats = set(re.findall(r"`(\^T-\[0-9\]\{8\}-[^`]+)`", md_txt))
    if not md_pats:
        blk("15. SKILL.md 中未找到 task_id pattern（`^T-[0-9]{8}-…` 形态）——"
            "文档真源缺失，无法校验一致性")
        return
    if md_pats != {env_re_p}:
        blk("15. task_id pattern 文档真源漂移：SKILL.md 声明 %s ↔ schema 声明 `%s`"
            "（契约漂移，以 schema 为准；SKILL.md 是 agent 加载时读的真源）"
            % ("/".join(sorted(md_pats)), env_re_p))
        return

    # --- 判据 5（附加 · S-E54）：全仓不得再出现 task_id pattern 的手抄 ---
    # 语义：任何**硬编码** task_id pattern 字面量的脚本 = 一份新真源 = 漂移源。
    # 合法写法只有两种：
    #   (a) 从 schema 读取（json.load(...)["properties"]["task_id"]["pattern"]）
    #   (b) 从 schema 派生（正则以 schema pattern 为原料拼装）
    # 出现形如 `T-\d{8}` / `T-[0-9]{8}` 的**裸字面量正则**即判为手抄。
    # 排除本脚本自身（判据文本内含该字面量）。
    handwritten = []
    self_name2 = os.path.basename(__file__)
    for root, _dirs, files in os.walk(os.path.join(PKG, "scripts")):
        if "__pycache__" in root:
            continue
        for f in sorted(files):
            if not f.endswith(".py") or f == self_name2:
                continue
            fp = os.path.join(root, f)
            try:
                txt = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            # 命中「手抄特征」：正则里直接写了 task_id 的日期段字面量
            if re.search(r'T-\\d\{8\}|T-\[0-9\]\{8\}', txt):
                # 排除从 schema 派生的实现（它必然含 schema 读取路径）
                reads_schema = ("result_envelope.schema.json" in txt
                                or "load_task_id_pattern" in txt
                                or "_load_task_id_pattern" in txt)
                if not reads_schema:
                    handwritten.append(f)
    if handwritten:
        blk("15. task_id pattern 出现新的一份手抄：%s——"
            "必须改为从 result_envelope.schema.json 读取或派生（S-E54 纪律）"
            % "/".join(handwritten))
        return

    ok("15. task_id 契约五处一致（pattern=%s·基线样本 %d 个全匹配·"
       "任务包 schema 消费方 %s·SKILL.md 文档真源已同步·全仓零手抄）"
       % (env_re_p, len(samples), "/".join(consumed)))


def check_workflow_d_gate(state_path):
    """12. Workflow D 入口前置闸（S-E02 · CYCLE-1 第2轮交叉验证落地）

    主理人 MD:359 声称「由 preflight_check.py 第9项机械校验」——CYCLE-1 第2轮交叉验证
    实测 preflight 全文不含 G1/G2/G3/search_3rounds/trinity 任一字符串，即该机械校验
    **从未存在**（幽灵验证项 · 违反哲学④）。本项落地真实校验代码。

    判据（Workflow D 派单前置闸，主理人 MD:353-359）：
      G1(search_3rounds_complete) ∧ G2(trinity_verdict_pass) ∧ G3(c1_c8_confirmed) 全为 true
      且能给出三轮查新报告与三性裁决的**落盘文件路径**（文件缺失 = 视为未查新）。

    真源：state_store.GATE_ALIASES（别名表唯一真源，S-E01）。
    语义：
      - 未提供 --state-path → WARN（无 state 可校验；不得据此判定闸通过）
      - state 存在但门禁未全关 → BLOCK（Workflow D 禁止派单）
      - state 门禁全关但落盘证据缺失 → BLOCK（文件缺失 = 视为未查新）
    """
    if not state_path:
        wrn("12. 未传 --state-path，跳过 Workflow D 前置闸校验"
            "（Workflow D 派单前必须提供 state.json 路径）")
        return
    p = os.path.abspath(state_path)
    if not os.path.isfile(p):
        blk("12. Workflow D 前置闸：state 文件不存在 %s——无法证明已查新/已裁决，"
            "禁止直接进 Phase 5" % p)
        return
    try:
        state = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        blk("12. Workflow D 前置闸：state 文件解析失败 %s：%s" % (p, e))
        return
    try:
        sys.path.insert(0, HERE)
        from state_store import GATE_ALIASES
    except Exception as e:
        blk("12. Workflow D 前置闸：无法载入门禁别名真源（state_store.GATE_ALIASES）：%s" % e)
        return

    # D 闸只校验 G1/G2/G3（G4/G5 是 Phase5 内的门禁，D 入口不要求）
    d_gates = ["G1", "G2", "G3"]
    g = state.get("gates") or {}
    closed, open_g = [], []
    for gn in d_gates:
        sem = GATE_ALIASES.get(gn, gn)
        (closed if g.get(sem) else open_g).append(gn)
    if open_g:
        blk("12. Workflow D 前置闸未通过：%s 未关闭（state=%s）——"
            "禁止直接进 Phase 5，须转 Workflow C 或升级用户裁决（L4）"
            % ("、".join(open_g), p))
        return
    # 门禁全关 → 校验落盘证据（文件缺失 = 视为未查新）
    ev = state.get("evidence") or {}
    missing_ev = [k for k in ("search_report", "verdict_report") if not ev.get(k)]
    if missing_ev:
        blk("12. Workflow D 前置闸：门禁已全关但落盘证据缺失 %s"
            "（state.evidence 键；文件缺失 = 视为未查新）" % "、".join(missing_ev))
        return
    # 证据路径必须真实存在（防登记了假路径）
    fake = []
    for k in ("search_report", "verdict_report"):
        fp = ev.get(k)
        if fp and not os.path.isfile(os.path.abspath(fp)):
            fake.append(f"{k}={fp}")
    if fake:
        blk("12. Workflow D 前置闸：证据路径不存在 %s" % "；".join(fake))
        return
    ok("12. Workflow D 前置闸通过：G1/G2/G3 全关 + 查新与裁决证据均已落盘")


def _gitignore_dirs(root):
    """解析 .gitignore 中的目录型排除项（CYCLE-1 · S-E23）。

    只取形如 `name/` 的行（目录递归排除）与 `*.ext`（文件型，不影响目录集）。
    返回 set。.gitignore 不存在 → 空集。
    """
    gi = os.path.join(root, ".gitignore")
    if not os.path.isfile(gi):
        return set()
    dirs = set()
    for ln in open(gi, encoding="utf-8"):
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("!"):
            continue
        if s.endswith("/"):
            dirs.add(s.rstrip("/"))
    return dirs


def check_readme_structure():
    """11. README 结构图与实际目录一致（CYCLE-1 · S-E09 失效引用修复的复发检测）
    判据：README.zh.md 结构图代码块中的一级目录/文件项 与 实际 ls -1 的差集必须为空。
    只校验一级项（子目录内部结构不展开，避免过度约束文档排版）。"""
    import re
    p = os.path.join(PKG, "README.zh.md")
    if not os.path.isfile(p):
        wrn("11. README.zh.md 不存在——跳过结构图一致性校验")
        return
    text = open(p, encoding="utf-8").read()
    m = re.search(r"```\n(triz-invention-team/.*?)```", text, re.S)
    if not m:
        wrn("11. README.zh.md 未找到结构图代码块——跳过结构图一致性校验")
        return
    block = m.group(1)
    documented = set()
    for ln in block.split("\n"):
        s = ln.strip()
        # 一级项行：以 ├── 或 └── 开头（前面可能有 │ 或空格）
        if not (s.startswith("├── ") or s.startswith("└── ")):
            continue
        item = s[4:].split("#")[0].strip().rstrip("/")
        if item:
            documented.add(item)
    actual = set()
    # CYCLE-1 · S-E23：实际集应与 **git 实际入库内容** 对齐，而非磁盘全部条目——
    # .gitignore 排除的项（.claude-plugin/ / outputs/ / __pycache__/）本地存在但不入库，
    # 不应要求 README 结构图收录。判据：解析 .gitignore 的目录型条目（前缀匹配）。
    ignored_dirs = _gitignore_dirs(PKG)
    for name in os.listdir(PKG):
        if name in (".git", "__pycache__"):
            continue
        if name in ignored_dirs:
            continue
        actual.add(name)
    # README 结构图是「精选视图」：允许 README 自身多出 .gitignore/.learnings 之外的
    # 未列项 → 实际多出的项记为文档缺失（需在图中补齐）
    missing_in_doc = sorted(actual - documented)
    extra_in_doc = sorted(documented - actual)
    if missing_in_doc:
        blk(f"11. README 结构图缺失实际存在的顶层项：{missing_in_doc}")
    if extra_in_doc:
        blk(f"11. README 结构图列出了不存在的顶层项：{extra_in_doc}")
    if not missing_in_doc and not extra_in_doc:
        ok(f"11. README 结构图与实际目录一致（{len(actual)} 项·diff=0）")


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
    r = subprocess.run([sys.executable, v, "--expert-dir", PKG, "--strict"],
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
    # S-E39：明确口径——白名单 = 6 个**执行成员**（不含主理人）。
    # 全仓「7」口径 = 1 主理人 + 6 成员，两者并列易生歧义，此处显式标注。
    ok("6. 装配器可用，成员白名单 %d 个（= 6 执行成员，不含主理人；"
       "全仓 7 = 1 主理人 + 6 成员）" % n)


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
    elif checked == 0:
        # CYCLE-1 · S-E16：此前 checked=0 也输出「全部存在」= 未检查却报通过（假绿）
        wrn("7. 成员 MD 中未发现 `skills/.../SKILL.md` 形态引用（checked=0）——"
            "本项实际未校验任何路径；成员技能声明真源在 frontmatter `skills:`，"
            "请核对 assemble_spawn_prompt.py 的 resolve_skill_paths 结果")
    else:
        ok("7. 成员声明的 %d 处 skill 路径全部存在于磁盘" % checked)


def check_c3_trigger(member_id, outputs_dir, x_count, c3_path, e_count=0):
    """P0-S3-1: C3 检查点自动触发

    当指定成员（默认 patent-search-scout）在 outputs_dir 下的最新产出信封
    含 X 级（或 E 级）文献时，必须提供 c3_path（指向 C3 确认文件）；
    无该文件则 exit 1（阻断）。

    CYCLE-1 · S-E53：触发条件此前只认 X 级，与 skills/patent-law/SKILL.md §四
    「对比文件分级出现 X **或** E 时」的权威定义漂移 → E 类命中时漏触发。
    现按权威定义补齐 E。
    """
    if member_id != "patent-search-scout":
        return
    trig_x, trig_e = x_count or 0, e_count or 0
    if trig_x <= 0 and trig_e <= 0:
        return
    detail = []
    if trig_x > 0:
        detail.append("X 级 %d 条" % trig_x)
    if trig_e > 0:
        detail.append("E 级 %d 条" % trig_e)
    if not c3_path:
        BLOCK.append("8. C3 检查点：%s出现但未提供 --c3-confirmation-path"
                     % "、".join(detail))
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
    OK.append("8. C3 检查点：%s已确认（%s）" % ("、".join(detail), c3_path))


def scan_x_grade(member_id, outputs_dir):
    """扫指定成员最新产出，统计 X 级 / E 级威胁条数。

    CYCLE-1 · S-E53：此前本函数用宽松正则 `X\\s*[\\W_]*\\s*(\\d+)`，
    对 7 个真实场景误判 4 例，最严重「本产出无 X 级威胁」被判 1 条 →
    **假触发 C3 阻断**，scout 正常流程被无端阻断；且与 patent_knowledge
    的结构化判据构成契约双源漂移。

    现改为消费 scripts/threat_grade.py 的**唯一真源**（结构化判据：
    JSON `xyape_grades` 数组 / Markdown 分级表节 + 专利号正则 + 否定值过滤
    + 跨载体专利号去重），本函数保留为兼容包装，返回 (x_count, e_count, detail)。
    """
    import threat_grade as TG
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    path = TG.latest_scout_output(member_id, outputs_dir)
    if not path:
        return 0, 0, {"verdict": "no_file"}
    x, e, detail = TG.scan_grade_counts(path)
    return x, e, detail


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
    ap.add_argument("--state-path", default="",
                    help="[CYCLE-1/S-E02] state.json 路径——启用第12项 Workflow D 前置闸机械校验")
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
    check_diagnosis_registry()
    check_readme_structure()
    check_workflow_d_gate(args.state_path)
    check_state_template_consistency()
    check_routing_log_columns()
    check_task_id_contract()

    # CYCLE-1 · S-E04：诊断触发器 T1-T3 机械判定（散文条款脚本化，原则①）
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import diagnosis_trigger as DT
        checks = {"T1": DT.check_t1(), "T2": DT.check_t2(), "T3": DT.check_t3()}
        fired = [k for k, (t, _, _) in checks.items() if t]
        if fired:
            wrn("9. 诊断触发器命中 %s → 建议本轮收尾执行一次 C1 诊断（见 docs/diagnosis-protocol.md）"
                % ",".join(fired))
        else:
            ok("9. 诊断触发器 T1/T2/T3 均未命中（%s）"
               % "; ".join(f"{k}:{d[:38]}" for k, (_, d, _) in checks.items()))
    except Exception as e:
        wrn("9. 诊断触发器不可用：%s（[暂缓·人工执行]：主理人按 protocol §一 自行判定）" % e)

    # P0-S3-1: C3 自动触发
    if args.outputs_dir:
        after_member = args.after_search or "patent-search-scout"
        x_count, e_count, detail = scan_x_grade(after_member, args.outputs_dir)
        verdict = detail.get("verdict", "no_carrier")
        if verdict == "no_carrier":
            # S-E53：count=0 有两种含义——「确实无威胁」与「未识别到分级载体」。
            # 二者不可混同：恒返回 0 = 幽灵验证项形态 B。此处显式 WARN，
            # 提示人工确认产出结构，而非静默当作「无威胁」放行。
            wrn("8. C3 检查点：未在 %s 的产出中识别到分级载体"
                "（JSON xyape_grades / Markdown 分级表节）——"
                "**无法机械判定 X/E 级计数**，请人工确认该产出是否含威胁清单"
                % after_member)
        elif x_count > 0 or e_count > 0:
            check_c3_trigger(after_member, args.outputs_dir, x_count,
                             args.c3_confirmation_path, e_count)

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
