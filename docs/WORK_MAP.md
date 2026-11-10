# 工作地图（Work Map · 唯一结构化执行清单）

> 本文件把「主理人 MD 里的散文操作说明」映射为**阶段 → 输入 → 命令 → 验收 → 证据 → 确认点**。
> 它不替代 `agents/triz-invention-team-team-lead.md`（SOP/红线/契约仍以 MD 为权威），
> 只解决「哪一步该跑什么、跑完拿什么证明」——由 `scripts/harness.py` 机械消费。
>
> 建立依据：真实运行（2026-11-10 17:05/17:48，`docs/routing-log.md` R-20261110-001~005）
> 暴露「平台 502 / 墙钟超预算 / 紧凑模式抢救」只留在决策叙述里，未进入反馈闭环；
> 且 22 个脚本中 13 个未出现在主理人操作说明中，工具与执行链脱节。

## 一、状态标注（四种，报告必须逐项标注）

| 状态 | 含义 | 判据 |
|---|---|---|
| `AUTO_PASS` 自动验证通过 | 机械检查有证据且通过 | 脚本读文件/真值比对，输出证据路径与值 |
| `AI_PASS` AI 评估通过 | 语义判断，由主理人给出结论 | 主理人显式写入结论 + 理由，不冒充机械检查 |
| `HUMAN_PASS` 人工确认通过 | 管家节点拍板 | 用户明确确认记录 |
| `UNVERIFIED` 尚未验证 | 缺输入/缺证据/缺确认 | **不得**当作通过；阻断项缺证据即禁止推进 |

## 二、阶段表

| 阶段 | 输入 | 确定性动作（工具） | 自动验收 | 证据落点 | 人工确认 |
|---|---|---|---|---|---|
| 0 需求锁定 | 用户想法 | `harness.py verify --stage 0 --run-dir D` | 需求卡五要素 Q1-Q5 齐全、工程参数 5 项已答或标「待定」 | `D/phase0_requirement.md` | Q1-Q5 内容正确性、领域坍缩 |
| 1 TRIZ建模 | Phase0 需求卡 | `assemble_spawn_prompt.py` 装配 → spawn | 模型卡落盘、信封必填字段 | `D/T-*__contradiction-analyst.md` | 矛盾类型/工具选择是否恰当 |
| 2 原理引导 | Phase1 模型卡 | 同上 | 方向数 ≥3（结构计数）、组合策略三线标签齐全 | 同上 | 方向价值、可授权可能性 |
| 2.5 汇聚校准 | R1 查新 + Phase1-2 | `harness.py verify --stage 2.5` | **校准记录存在**且含「覆盖/空白/上调/降级」决策字段 | `D/calibration__phase2.5.md` | 校准结论（语义判断） |
| 3 三轮查新 | 方向清单 | `threat_grade.py` / `patent_knowledge.py query` | R1/R2/R3 三轮产出落盘、分级载体可解析、X/E 级计数可判定 | `D/T-*__patent-search-scout.md` | 检索渠道降档、威胁分级语义 |
| 4 对抗三性 | 查新绿/黄 | `harness.py verify --stage 4` | examiner + second-opinion 双产出、二审条件逐键登记、**G2 真值** | `D/T-*__patent-examiner-sim.md` 等 | 红/黄裁决、仲裁、L4 升级 |
| 5 撰写 | G1-G3 全 true | `boundary_guard.py` / `check_claim_scope.py` / `contract_enforce.py` | 摘要 ≤300字、无模糊词、权项引用、越界 B1-B5、G3/G4/G5 真值 | `D/T-*__disclosure-architect.md` 等 | **C1-C8 技术含义**、法律判断 |
| 交付 | 全流程产出 | `harness.py verify --all` + `self_gate.py` | 门禁 G1-G5 真值、路由决策已落盘、人设注入痕迹、失败记忆注入痕迹、墙钟双轨 | `D/verify__*.json` + `docs/routing-log.md` | 交付包是否可用 |

## 三、C1-C8 边界（管家节点确认「部分转自动」）

**默认假设（可推翻，未经逐项确认）**：把**结构可判定**部分转自动，**技术含义**保留人工。

| 项 | 自动检查（结构） | 人工判断（语义，不自动替代） |
|---|---|---|
| C1 发明名称 | 非空、无占位符 | 名称是否准确、是否落入客体排除 |
| C2 技术领域 | 章节存在、非空 | 领域归属是否正确 |
| C3 背景 | 章节存在、非空 | 现有技术描述是否真实 |
| C4 必要技术特征 | 清单条目数 ≥1、与交底书一致 | **哪些特征真的必要**（保护范围取舍） |
| C5 优选特征 | 章节/清单存在 | 优选层次是否合理 |
| C6 技术效果 | 有条目、带数据或证据引用 | 效果真实性、是否夸大 |
| C7 实施方式 | 条目数 ≥1 | 是否可实施、是否充分公开 |
| C8 附图需求 | 二值明确（需要/不需要） | 图稿内容与充分性 |

> 自动项只判「有没有 / 格式对不对」，**不判「对不对」**。自动全通过 ≠ C1-C8 确认完成；
> `harness.py` 对 C1-C8 一律额外输出 `HUMAN_REQUIRED`，不把结构检查冒充用户确认。

## 四、反馈闭环

| 环节 | 落点 | 工具 |
|---|---|---|
| 真实运行故障/降级 | `.learnings/FEEDBACK.jsonl` | `harness.py feedback add` |
| 单次要求 | `scope=once`，只记录，不进规则集 | 同上 |
| 长期规则 | `scope=rule` **必须**绑定 `convert-to`（认可样例 / 程序检查 / 工具修复）与 `check-id`，否则拒绝 | 同上（防规则膨胀） |
| 认可样例 | `tests/cases/runtime-*.md` + 回归断言 | `harness.py verify --sample` |
| 内容变化后重验 | 检查对象 sha256 指纹存 `.harness/verify_state.json` | `harness.py verify`（自动比对，变化项标 stale） |
| 反馈进入下一轮 | 报告末「待改进」段列出未闭环条目 | `harness.py feedback list --open` |

## 五、明确不改造（保留有效设计）

6 阶段 SOP、4 Workflow 与串行查新约束、三档置信度路由、JSON Schema 双向契约、
preflight 15 项、三用例回归 + 变异测试、failure 索引、U2 两级门禁、
诊断登记表 48h 回检 /「评估后不实施」机制、宿主门禁安装器 `install_gate_hooks.py`。
