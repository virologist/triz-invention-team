# TRIZ发明专家团 · 多代理编排架构规范 v2.0

> 对齐前沿agent工程标准：Harness（执行外壳）+ Agentic Loop（代理循环）+ Contract（接口契约）+ Arbitration（冲突仲裁）

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────────┐
│  HARNESS 执行外壳                                         │
│  ┌───────────┬──────────┬──────────┬──────────────────┐ │
│  │Context    │State     │Loop      │Observability     │ │
│  │Assembler  │Store     │Controller│(latency/quality) │ │
│  │上下文装配  │状态存储   │循环控制   │可观测性           │ │
│  └───────────┴──────────┴──────────┴──────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  ORCHESTRATOR 编排者 (triz-invention-team-team-lead)      │
│  路由 · 门禁 · 聚合 · 仲裁                                │
└─────────────────────────────────────────────────────────┘
        ↓ fan-out              ↓ fan-in
┌──────────────┬──────────────┬──────────────┐
│ ANALYZER     │ EXECUTOR     │ REVIEWER     │
│ 分析者        │ 执行者        │ 审查者        │
├──────────────┼──────────────┼──────────────┤
│ contradiction│ disclosure   │ examiner-sim │
│ -analyst     │ -architect   │ second-      │
│ search-scout │ attorney     │ opinion      │
│              │ -writer      │ -reviewer    │
└──────────────┴──────────────┴──────────────┘
```

---

## 二、角色矩阵（Role Matrix）

| 角色 | 成员 | 能力边界（能做什么） | 禁止边界（不能做什么） | 输入契约 | 输出契约 |
|------|------|-------------------|---------------------|---------|---------|
| **Orchestrator**<br>编排者 | triz-invention-team-team-lead | 任务解析、子任务拆解、成员调度、门禁裁决、冲突仲裁、结果聚合 | ❌ 代写任何成员的专业产出<br>❌ 跳过门禁推进<br>❌ spawn自己 | 用户请求 | 任务计划 + 最终交付包 |
| **Analyzer**<br>分析者 | contradiction-analyst<br>patent-search-scout | 调查、建模、检索、产出分析结论 | ❌ 撰写申请文件<br>❌ 做最终授权判断 | task_payload + 领域上下文 | analysis_artifact（模型卡/查新报告） |
| **Executor**<br>执行者 | disclosure-architect<br>patent-attorney-writer | 基于分析产出生成交付文档 | ❌ 虚构实验数据<br>❌ 修改已确认的技术特征<br>❌ 自我评价质量 | analysis_artifact + 确认记录 | document（交底书/申请文件） |
| **Reviewer**<br>审查者 | patent-examiner-sim<br>second-opinion-reviewer | 攻击、复核、出具裁决 | ❌ 修改方案（只出裁决+修复建议）<br>❌ 与其他成员直连 | document/analysis + 证据 | verdict（绿/黄/红 + 问题清单） |

**职责不可越界原则**：Analyzer不做Executor的活，Executor不自我评价（评价权归Reviewer），Reviewer不修改只裁决。

---

## 三、Harness 执行外壳

### 3.1 Context Assembler（上下文装配器）

每个agent被spawn时，Harness按**最小充分原则**装配上下文：

```
Context = 角色MD(自身) 
        + 声明的skills references(按需) 
        + task_payload(本任务输入)
        + 前序phase产出(仅依赖部分，非全量)
        + 领域上下文(坍缩结果)
        + TASK_STATE快照
```

**关键约束**：
- 禁止全量灌入所有前序产出——只传本阶段依赖的部分
- Skill按需加载（triz-matrix / patent-law / claims-drafting 按职责挂载）
- 单agent上下文预算 ≤ 20K tokens

### 3.2 State Store（状态存储）

全局唯一状态对象，由编排者维护并随每次调度下发：

```json
{
  "task_id": "T-YYYYMMDD-NNN",
  "phase": 0-5,
  "domain": "已坍缩领域",
  "invention_name": "...",
  "search_rounds": 0-3,
  "verdicts": {
    "examiner": {"result": "green|yellow|red", "confidence": 85},
    "second_opinion": {"result": "agree|conditional|disagree", "confidence": 78}
  },
  "gates": {
    "search_3rounds_complete": false,
    "c1_c8_confirmed": false,
    "disclosure_gap_scan": false
  },
  "retry_counts": {"contradiction-analyst": 0, "patent-attorney-writer": 0},
  "confirmed_items": {"C1": false, "C2": false, "...": false},
  "conflicts": [],
  "metrics": {"total_duration_ms": 0, "agent_calls": 0}
}
```

### 3.3 Loop Controller（循环控制器）

**核心变革：从线性流水线升级为带验证的循环**

```
每个Phase = GATHER → ACT → VERIFY → [ADVANCE | RETRY]

GATHER  装配上下文（依赖产出 + skill + state快照）
  ↓
ACT     调度agent执行（spawn + 下发task_payload）
  ↓
VERIFY  门禁校验（格式/约束/前置条件/质量）
  ↓
  ├─ PASS → 更新state → 下一Phase
  ├─ FAIL & retry<3 → 附反馈重试（同agent）
  ├─ FAIL & retry≥3 → 换策略（换agent/降级路径）
  └─ BLOCKED → 升级给用户
```

**重试上限**：单Phase最多3次（同策略2次 + 换策略1次）

### 3.4 Error Recovery（错误恢复）

| 错误类型 | 检测方式 | 恢复动作 |
|---------|---------|---------|
| 回传超时 | spawn后>120s无SendMessage | 主动SendMessage唤醒；仍失败→静态fallback评估 |
| 门禁违反 | VERIFY阶段校验失败 | 回退至违规agent，附具体违规点 |
| 内容幻觉 | Reviewer检出虚构引用/数据 | 强制重做 + 记录failure-xxx |
| 上下文溢出 | 产出>预算 | 压缩（保留结论，丢弃推演过程） |
| Agent冲突 | 两Reviewer结论不一致 | 触发仲裁协议（见第五节） |

### 3.5 Observability（可观测性）

每次调度记录：
- `duration_ms`：spawn到回传耗时
- `tokens_in/out`：上下文与产出规模
- `status`：success/partial/failed/blocked
- `confidence`：agent自评置信度0-100
- `retry_count`：重试次数

**质量指标**：
- 一次通过率 = 首次VERIFY即PASS的Phase数 / 总Phase数
- 平均重试次数
- 幻觉发生率 = 检出虚构次数 / agent调用次数
- 端到端延迟

---

## 四、接口契约（Interface Contract）

### 4.1 下行契约：编排者 → 成员（task_payload）

```json
{
  "task_id": "T-20260829-001",
  "phase": 2,
  "agent_id": "contradiction-analyst",
  "instruction": "基于Phase1模型卡推演候选方向",
  "input": {
    "dependency_artifacts": ["phase1_model_card"],
    "domain_context": "机械工程视角（重量/强度/可靠性/精度）"
  },
  "output_contract": {
    "required_fields": ["directions", "principle_refs", "comparison_table"],
    "min_directions": 3,
    "format": "markdown"
  },
  "constraints": ["禁止评估新颖性", "禁止凭记忆补全矛盾矩阵"],
  "deadline_hint": "控制在800字内"
}
```

### 4.2 上行契约：成员 → 编排者（result_envelope）

**所有成员回传必须遵循此信封格式**（在产出正文前附加）：

```json
{
  "agent_id": "contradiction-analyst",
  "task_id": "T-20260829-001",
  "phase": 2,
  "status": "success|partial|failed|blocked",
  "confidence": 82,
  "deliverable_summary": "5个候选方向，基于#12/#19/#15等原理",
  "evidence": [
    {"type": "skill_ref", "ref": "triz-matrix.md#常用矛盾对速查", "used_for": "TC1(21/36)查表"},
    {"type": "prior_artifact", "ref": "phase1_model_card"}
  ],
  "issues": ["方向3跨表推演，严谨性略弱"],
  "next_agent_hint": "patent-search-scout（需查新验证方向2）",
  "metrics": {"duration_ms": 36000, "retry_count": 0}
}
```

**status语义**：
- `success`：完整满足output_contract
- `partial`：部分满足，issues非空，需编排者判断是否可用
- `failed`：无法满足，需重试
- `blocked`：前置条件不足，需编排者补齐

### 4.3 门禁契约（Gate Contract）

| 门禁 | 校验点 | 违规处理 |
|------|-------|---------|
| G1 查新完成 | search_rounds ≥ 3 且 state.gates.search_3rounds_complete=true | 禁止进入Phase5 |
| G2 三性通过 | examiner.verdict ∈ {green, yellow} 且 second_opinion ≠ disagree | 黄→需修复清单；红→退回Phase2 |
| G3 C1-C8确认 | state.confirmed_items 全为true | 禁止进入Phase5 |
| G4 交底书完整 | 缺口扫描已执行且待补充清单已列出 | 禁止移交权要达 |
| G5 格式合规 | 无模糊词 + 权项引用正确 + 摘要≤300字 | 退回权要达修正 |

---

## 五、任务分配策略

| 模式 | 适用场景 | 编排方式 | 实例 |
|------|---------|---------|------|
| **Parallel 并行** | 成员间无数据依赖 | 单消息内spawn多个 | Phase1-2分析 + Phase3查新可并行启动（分析产出粗方向即启动检索预热） |
| **Serial 串行** | 强数据依赖 | 前序回传完整产出后启动下一 | analyst → scout → examiner → second-opinion → disclosure → attorney |
| **Conditional 条件触发** | 结果分支 | 按前序verdict路由 | examiner=RED → 退回analyst；GREEN/YELLOW → 触发second-opinion |
| **Fan-out/Fan-in 扇出扇入** | 多维度并行分析 | 编排者分发→汇聚→裁决 | 多方向并行查新，结果汇聚至examiner |
| **Retry Loop 重试循环** | VERIFY失败 | 附反馈重调度同agent | 权项含模糊词 → 附违规点退回重做（≤3次） |
| **Escalate 升级** | 3次失败/仲裁僵局 | 交用户决策 | 查新连续3轮发现X级文件 → 升级用户决定规避设计or放弃 |

---

## 六、冲突检测与仲裁机制

### 6.1 冲突分级

| 级别 | 冲突类型 | 检测方式 | 仲裁规则 |
|------|---------|---------|---------|
| **L1** | Agent vs Gate<br>（产出违反硬约束） | VERIFY门禁校验 | **门禁优先**：自动拒绝，无需仲裁。Gate是宪法级 |
| **L2** | Agent vs Source<br>（产出与检索到的真实专利矛盾） | Reviewer核对证据链 | **证据优先**：以检索源为准，agent必须修正 |
| **L3** | Agent vs Agent<br>（两agent结论不一致） | 编排者比对verdict | 见6.2仲裁协议 |
| **L4** | Agent vs User<br>（产出与用户确认的C1-C8不符） | 编排者比对确认记录 | **用户优先**：用户确认记录为最终依据 |

### 6.2 L3仲裁协议（Agent vs Agent）

**优先级链**（高→低）：
1. **Reviewer > Executor**（审查者判断优于执行者自述）
2. **专业对口 > 通用**（领域专属agent优于跨领域判断）
3. **高置信度 > 低置信度**（confidence字段量化比较，差距>15分则高者胜）
4. **证据充分 > 推理**（有外部证据支撑的结论优于纯推理）

**仲裁流程**：
```
检测到L3冲突
  ↓
编排者提取双方 evidence 与 confidence
  ↓
按优先级链裁定
  ↓
  ├─ 可裁定 → 记录裁定理由至 state.conflicts，推进
  ├─ 不可裁定（confidence差距≤15且证据同级）→ 触发tie-break：
  │     调度 third-party（second-opinion-reviewer）做最终裁决
  └─ tie-break仍僵持 → 升级用户（L4）
```

**冲突记录**：每次仲裁结果写入 `state.conflicts[]`，含双方主张、裁定依据、最终结论——用于后续复盘与failure索引。

### 6.3 二审机制（Anti-Confirmation-Bias）

`second-opinion-reviewer` 是专门对抗**团队集体确认偏误**的设计：
- 不重复examiner的攻击，而是**审视examiner是否尽到职责**
- 二次表态：✅同意 / ⚠附条件同意 / 🔴不同意
- 🔴不同意可直接推翻examiner裁决（这是其核心价值）

---

## 七、Agentic Loop 完整定义

```
LOOP(task):
  state = init_state(task)
  
  PHASE 0 [ORCHESTRATOR 亲执]:
    苏格拉底追问(≤5轮×≤5问)
    IF 充分度 < 80% AND 轮次 < 5: CONTINUE LOOP
    ELSE: 领域坍缩 → state.domain
    VERIFY: 五核心维度已澄清 → GATE
  
  PHASE 1-2 [ANALYZER: contradiction-analyst]:
    GATHER: 需求卡 + 领域上下文 + triz-matrix
    ACT: 建模 + 原理推演
    VERIFY: 方向数≥3 ∧ 原理编号可溯 ∧ 无矩阵幻觉
    IF FAIL: RETRY(max 3) → 换策略: 降级物理矛盾路径
  
  PHASE 3 [ANALYZER: patent-search-scout]:
    GATHER: 方案 + patent-law
    ACT: 3轮递进检索
    VERIFY: G1(search_rounds≥3) ∧ 无捏造专利号
    IF FAIL: RETRY → 换策略: 扩大检索库
  
  PHASE 4 [REVIEWER 双层]:
    GATHER: 方案 + 查新报告 + patent-law
    ACT: examiner-sim 攻击 → 绿/黄/红裁决
    VERIFY: G2(verdict ∈ {green, yellow})
    IF RED: 退回 PHASE 2 (TRIZ二次改进)
    ACT: second-opinion-reviewer 二审
    VERIFY: 二审 ≠ 不同意
    IF 不同意: 退回examiner复审
    通过后: 用户 C1-C8 确认 → VERIFY G3
  
  PHASE 5 [EXECUTOR 串行]:
    5a disclosure-architect: 交底书
       VERIFY: G4(缺口扫描已执行)
    5b patent-attorney-writer: 申请文件
       VERIFY: G5(格式合规)
       IF FAIL: RETRY(max 3)
  
  RETURN 聚合交付包
```

---

## 八、与12-Factor AgentOps的映射

| 因素 | 本架构落地 |
|------|-----------|
| I 上下文即一切 | Context Assembler 最小充分装配 + 按需skill加载 |
| II Git追踪 | （未实现，建议后续） |
| III 一个Agent一个任务 | 每Phase独立spawn，无上下文复用 |
| IV 构建前调研 | Phase0苏格拉底追问 + Phase3查新 |
| V 外部验证 | Reviewer层（examiner + second-opinion双层）+ 用户C1-C8确认 |
| VI 锁定进度 | Gate契约 G1-G5，通过即锁定不可回退 |
| VII 提取教训 | failure索引机制（~/.workbuddy/expert-failures/） |
| VIII 知识复利 | 3个skill references库 + failure索引 |
| IX 衡量重要的事 | Observability（一次通过率/幻觉率/延迟） |
| X 隔离工作单元 | 成员上下文隔离，仅经编排者中转 |
| XI 层级化监督 | L1-L4冲突分级 + 升级路径 |
| XII 失败智慧 | failure-xxx记录 + 仲裁记录复盘 |
