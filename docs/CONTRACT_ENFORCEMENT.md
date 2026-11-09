# 契约执行门禁（P0-S1-1 配套文档）

> **单源化声明（2026-11-07）**：禁止触发词的**唯一真源**是各成员 `agents/<id>.md` frontmatter 的
> `forbidden_phrases` 列表——`scripts/contract_enforce.py` 启动时**解析**该表执行，本文件仅作
> 人类可读展示，**修改禁词一律改 frontmatter**（此前三方手抄漂移，S-Q1 根因）。
> 机械验证项的实现归属 `contract_enforce.py` 的 `VERIFICATIONS` 表；本文件对每项标注实现状态。
> 每个成员 frontmatter 末尾的 `must_verify` 项是**契约**，本文件是其**机器可执行规范**。
> CI gate（`scripts/contract_enforce.py`）按 `member_id` 查本表 → 实测成员产出 → 违反即 fail。

**实现状态标注约定**：`[机械已实现]` = 脚本自动校验；`[暂缓·人工执行]` = grep 无法表达
（语义级/交叉验证级），由主理人 VERIFY 阶段人工执行——**禁止**文档列出却无标注的"幽灵验证项"
（S-Q2 根因：文档承诺超出机械能力=验收标准虚高）。

## 6 成员契约清单

### contradiction-analyst
**禁止触发词**（真源=frontmatter，此处为展示镜像）：
- `approximately|左右|大概|估计|约\d+字`
- `I think|我觉得|可能|也许`
- `凭记忆|未核实`

**强制验证**：
1. **directions ≥3** `[机械已实现]`：`re.findall(r'(#?\d+\.|方向[1-9]|IP #\d+)', out) >= 3`
2. **原理编号实跑** `[机械已实现]`：`re.search(r'(query_triz_matrix|退出码)', out)` 必须命中
3. **无编造** `[暂缓·人工执行]`：所有 IP 编号溯源到 `query_triz_matrix.py exit=0` 输出——grep 只能证命令出现，不能证编号一致；主理人 VERIFY 时抽查矩阵查询回显与产出编号一致

### patent-search-scout
**禁止触发词**（真源=frontmatter；原文档「应用号」系笔误，已修正为「申请号」）：
- `approximately|左右|估计|凭记忆|推测`
- `(申请号|公开号).*?未核实`
- `(我|我们)知道.*?(某专利|某文献)`

**强制验证**：
1. **X/Y/A/R/P/E 6类显式（或复检≥3类）** `[机械已实现]`：`_check_xyarpe_or_recheck`
2. **search_rounds ≥3** `[机械已实现]`：`re.findall(r'(R[123]|第[一二三]轮)', out) >= 3`
3. **检索渠道节显式** `[机械已实现]` `[2026-11-07 Batch4]`：产出含「检索渠道」段且登记实际档位（L1-L4）——降档未登记=契约违反
4. **三要素核验** `[暂缓·人工执行]`：每条引用含「专利号+标题+与方案关系」——逐条语义比对超出 grep 能力，主理人 VERIFY 抽查

### patent-examiner-sim
**禁止触发词**（真源=frontmatter；「应当」经 a04 历史产出实测为法条引用高频误伤，收窄移除）：
- `approximately|基本|整体上.{0,12}可以`（R1 纯净化：原两条前瞻豁免是死代码已删；「基本」合法搭配走 CONTEXT_EXEMPT）

**强制验证**：
1. **裁决显式（绿/黄/红）** `[机械已实现]`：`_check_verdict`（裁决/结论 200 字符窗口内灯色）
2. **每条攻击附证据四元组** `[暂缓·人工执行]`：`攻击数×4` 计数依赖先机械识别"攻击条数"本身（无可靠锚点），降级为人工抽查；辅助信号：产出含 `X级|特征|命中|依据` 词汇密度（a04 实测 89 次命中，人工核样本即可）
3. **修复清单分级** `[机械已实现]`：`re.search(r'(强制|建议)', out)`

### second-opinion-reviewer
**禁止触发词**（真源=frontmatter）：
- `我同意.*?不附理由`
- `基本.*?通过`
- `无需.*?修改`

**强制验证**：
1. **二次表态显式** `[机械已实现]`：`re.search(r'(✅|⚠|🔴|附条件)', out)`
2. **⚠附条件必须给条件清单** `[机械已实现]`：`re.search(r'(附加条件|条件清单|附条件)', out)`
3. **元审查 ≠ 替一审重做** `[暂缓·人工执行]`：产出含「补强项|元审查」词汇（a05 实测 10 次）可作辅助信号，但"是否越界替审"是语义判断——主理人 VERIFY 抽查

### disclosure-architect
**禁止触发词**（真源=frontmatter；文档另两条负向上下文断言属语义验证，grep 无法表达负向断言，归本表人工层）：
- `estimated|约|估计|大约`
- ~~`实验.*?(?<!本发明|申请人).{0,15}表明`~~ `[暂缓·人工执行]`（变长负向后顾断言，Python re 不支持 `(?<!...)` 变长模式）
- ~~`(优化|显著|大幅).*?(?!附数据|附实施例)`~~ `[暂缓·人工执行]`

**强制验证**：
1. **必要/可选特征分层** `[机械已实现]`：`re.search(r'(必要特征|可选特征)', out)`
2. **缺口清单显式** `[机械已实现]`：`re.search(r'(缺口|待补)', out)`
3. **实施例 ≥2 档** `[机械已实现]`：`re.findall(r'实施例\s*\d', out) >= 2`
4. **无编造实验数据** `[暂缓·人工执行]`：「实验表明」类断言须有出处或标注[INFERRED]——主理人 VERIFY 抽查

### patent-attorney-writer
**禁止触发词**（真源=frontmatter）：
- `约\d+字|左右|估计.{0,6}字`（**failure-006 复发防御**）
- `approximately|大致|基本`
- `显著|大幅|明显|高效`（R1 纯净化；附证据场景走 CONTEXT_EXEMPT 豁免）

**强制验证**：
1. **摘要 ≤300 字符 + 机械验证证据** `[机械已实现]`：`_check_abstract`（只数「摘要正文」段，附录/证据不计入）
2. **权利要求禁用词零命中** `[机械已实现]`：`_check_claims_banned`（8 词全检，只扫 A 区权项+说明书+摘要）
3. **独立权项须含交底书必要特征（LCS≥60%）** `[暂缓·人工执行]`：已另有独立机械工具 `scripts/check_claim_scope.py`（特征→权项 LCS 映射，阈值 12 字符），本门禁不重复实现；主理人在 Phase 5b 后调用该脚本——此为工具分工，非缺失

## 运行方式

```bash
# 对单成员产出验证
python3 scripts/contract_enforce.py \
  --member contradiction-analyst \
  --output tests/baselines/l2-full-a01/T-20261015-A01__contradiction-analyst.md

# 全员 L1/L2 回归时一起跑
python3 scripts/contract_enforce.py \
  --output-dir tests/baselines/ \
  --exit-on-fail

# U2 两级门禁：机械命中 + LLM 语义复核清单（主理人 VERIFY 用）
python3 scripts/contract_enforce.py --member <id> --output <file> --llm-review
```

**两级门禁说明（U2 · 2026-11-07）**：第 1 级 = 机械匹配（禁词 + 清洗层 + 豁免链，秒级、零成本）；
第 2 级 = `--llm-review` 对机械命中项输出语义复核清单（命中行 + 上下文 + 复核问题）——
**机械层只负责"抓"，语义层负责"判"**：豁免链无法覆盖的场景（如引用讨论、反例教学、
法条转述）由主理人在 VERIFY 时逐条判定，判违规回退成员、判豁免记录理由。正则永远
无法完美表达语义边界，两级设计承认这一点并把判定权交还给语义引擎（主理人 LLM）。

退出码：`0`=全过 · `1`=至少一个成员违反 · `2`=参数错。

## 失败处置

- 首次违反 → 主理人回退该成员（`reverify_with_feedback`）并附具体违反行号
- 二次违反 → 升级用户决策（重做或换成员）
- 3 次违反 → 写入 `failure-XXX` 失败索引 + 调整契约本身

## 维护

- **禁词唯一真源 = 各成员 frontmatter `forbidden_phrases`**（2026-11-07 单源化）：改禁词只改 frontmatter，本文件展示镜像与脚本解析自动跟随；`--self-test` 自测1会校验 6 成员表可解析非空
- **三源一致性已兑现为真校验（CYCLE-1 · S-E06/S-E17 · 2026-11-08）**：此前 `DOCS` 变量定义却从不读取，「三源一致性」是幽灵验证项；现自测1 真读取本文件镜像段与 frontmatter 逐条比对，任一漂移即 FAIL
- **DRIFT_PROBE 反向验证已兑现为真实探针（CYCLE-1 第2轮交叉验证 · 2026-11-09 · S-E21）**：此前本行仅**声称**「反向验证：注入 `DRIFT_PROBE` → exit 1」，但全仓 grep 仅命中本行本身，脚本内并无该探针——即该反向验证**从未被真实执行**（幽灵验证项·违反哲学④）。现 `contract_enforce.py` **自测4** 落地真实探针：① 基线一致（未注入 → 无漂移）② 注入 `DRIFT_PROBE_CANARY` → 三源比对必须检出漂移（期望 exit 1）③ 镜像同步后 → 无漂移（期望 exit 0，证明探针有判别力、非恒真）。实测：`python3 scripts/contract_enforce.py --self-test` → 自测4 三项全 ✅，exit 0
- **禁止边界下沉契约 `[机械已实现]`（CYCLE-1 · S-E11 · 2026-11-09）**：`task_payload.schema.json` 增 `forbidden_boundary`（非 required，不破历史信封）；**自测1b** 校验 ① schema 含该字段 ② `docs/architecture.md` §二 角色矩阵覆盖 6 成员 ③ 禁止边界非空 ④ 角色归类（Analyzer/Executor/Reviewer）与矩阵一致。真源 = 角色矩阵「禁止边界」列
- **Workflow D 前置闸机械校验已落地（CYCLE-1 第2轮交叉验证 · 2026-11-09 · S-E21）**：主理人 MD 曾声称「由 `preflight_check.py` 第9项机械校验」，实测 preflight 全文不含 G1/G2/G3/search_3rounds/trinity 任一字符串——**该机械校验从未存在**（幽灵验证项）。现落地为 `preflight_check.py` **第 12 项**（真源 = `state_store.GATE_ALIASES`）：G1/G2/G3 全关 ∧ `state.evidence` 的查新/裁决落盘文件真实存在 → 才放行；否则 BLOCK
- **frontmatter 契约字段完整性 `[机械已实现]`（CYCLE-1 · S-E07 · 2026-11-08）**：6 成员必须含 `schema_version / contract_owner / verified_at / forbidden_phrases / must_verify / declared_skills` 六字段，缺任一 → 自测 FAIL；此前这 6 字段零机械消费者（声明与机械能力脱钩）
- **失败即失败（CYCLE-1 · S-E15 · 2026-11-08）**：违规默认即 `exit 1`，无需 `--exit-on-fail`；此前无该开关时违规也返回 0（fail-open），与本文件「0=全过 · 1=至少一个成员违反」的契约相悖
- **禁止边界的**验收侧**机械拦截已落地（CYCLE-1 第4轮 · S-E59 · 2026-11-09）**：S-E11 只把 `forbidden_boundary` 下沉到**下发侧**（`task_payload.schema.json`），**验收侧零机械校验**——成员写出申请文件正文 / 越权出具授权断言 / 自我评价 / 越权改写方案，**没有任何脚本会报错**。现落地 `scripts/boundary_guard.py`：
  - **角色矩阵真源** = `docs/architecture.md` §二（Analyzer 2 / Executor 2 / Reviewer 2 / Orchestrator 1）
  - **5 个越界信号**：B1 撰写申请文件正文（权项书/说明书）· B2 肯定性授权断言 · B3 自我评价质量 · B4 越权修改方案 · B5 非职责角色出具三性评级
  - **判据基于产出结构**（章节标题 / 裁决字段 / 改写措辞），**不基于成员自述**；同一份产出**按其 agent_id 角色**判（Executor 本就要写权项书，Analyzer 写了才叫越界）
  - **verdict 四态**：`clean` / `violation` / `unknown_role`（成员不在矩阵内）/ `unreadable`——**不可判定 ≠ 放过**
  - **引用语境豁免**：B5 判定按**句级**上下文排除转述（详见/参见/据…报告/由…更新为）；B2 不豁免（断言句式即代表自己下断言）
  - 退出码：`0`=无越界 · `1`=存在越界 · `2`=用法/环境错误
  - 实测：`python3 scripts/boundary_guard.py --run-dir tests/baselines/l2-full-a01` → 8 份产出全部 `clean`（含 A01 scout 的「综合评级：红」——**三性风险评级属其职责内**，不误报）
- **X/E 级威胁判定收敛为唯一真源（CYCLE-1 第4轮 · S-E53/S-E60/S-E61 · 2026-11-09）**：此前 preflight 用宽松正则 `X\s*[\W_]*\s*(\d+)`、patent_knowledge 用结构化判据，**对同一语义给出不同答案**（preflight 对 7 个真实场景误判 4 例，最严重「本产出无 X 级威胁」被读成 1 条 X 级 → **假触发 C3 阻断**）。现落地 `scripts/threat_grade.py`：
  - **只认结构载体**：JSON `xyape_grades`（数组 + 字符串两形态）/ Markdown 分级表节；专利号必须过 `PAT_NO_RE`
  - **跨载体按专利号去重**（同一批文献同时出现在 JSON 数组与 Markdown 表 → 10 实为 5）；**跨等级不去重**（同文献可同属 X 与 Y）
  - **专利号形态全覆盖**：`CN223231803U`（授权公告号）· `US…B1`/`EP…A1`（kind code 两段）· `CN202311321256.8`（申请号小数点校验码）；**纯数字号段不计**（非任何法域标准形态）
  - **多轮产出聚合（S-E60）**：查新是多轮迭代的——首轮带完整分级载体，复检轮只引用首轮结论；只看最新一份会**漏掉首轮 X 级 → C3 不触发 → 假放行**。假放行比假阻断危险（阻断是流程摩擦，放行是带着 X 级威胁进撰写），故聚合该成员的**全部**产出
  - **verdict 三态**：`determined` / `no_carrier`（未识别到分级载体 → **不可判定**，不等于「确实无威胁」）/ `unreadable`
- **豁免机制重建（R1 · 2026-11-07）**：frontmatter 禁词**纯净化**——禁写 `.*?(?!...)` 前瞻豁免（实测死代码：`.*?` 匹配空串时前瞻恒成立，豁免从未生效）。豁免职能统一收敛到 `contract_enforce.py` 的 `CONTEXT_EXEMPT` 上下文窗口豁免表（命中后查前后 30 字符窗口含豁免词即放行）+ 既有清洗层 + EXEMPT_WORDS + 反例标记；`--self-test` 自测3做双向断言（豁免样本放行 ∧ 违规样本命中）
- **禁词单字误伤修复（CYCLE-1 · S-E20 · 2026-11-08）**：`可能` / `估计` 等单字在否定与风险语境（"不可能结垢" / "可能出现的可靠性损失" / "估计.{0,6}字"）会误伤合法技术表述 → 豁免词限定为明确的非猜测语境搭配，与 R1 修单字「约」同机制
- 验证项实现状态标注：新增验证项时必须同步标 `[机械已实现]`（进 contract_enforce.py VERIFICATIONS）或 `[暂缓·人工执行]`（写明人工执行点）——禁止无标注幽灵项（S-Q2 教训）
- 禁止触发词与 failure-006/007 教训同步：所有新失败都回灌到**对应成员 frontmatter** 的 `forbidden_phrases` 段
---

## deliverable_summary 格式规范（S5-4 · 2026-10-15）

信封 `deliverable_summary` 全员统一格式（便于跨成员可比与复盘检索）：

```
「<对象>」完成<动作>：<关键结论A>；<关键结论B>；<关键结论C>（≤60字符·含裁决/评级时必含）
```

- 长度 40–60 字符（中文计）；超长截断到完整分句
- 必含元素（按成员）：analyst→推荐方向；scout→X级数+综合评级；examiner→裁决灯色；
  reviewer→二次表态；architect→必要特征数；writer→摘要实测字符数
- 反例：`完成了分析`（无结论）/ 150字流水账（超长）——均为契约违反（WARN级）

