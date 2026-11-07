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
- `approximately|基本.*?(?!设计|物理|常)|整体上.*?可以`
- `建议.*?考虑.*?(?!附法条号|附证据)`

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
- `约\d+字|左右|估计.*?字`（**failure-006 复发防御**）
- `approximately|大致|基本`
- `(显著|大幅|明显|高效).*?(?!附实测|附数据)`

**强制验证**：
1. **摘要 ≤300 字符 + 机械验证证据** `[机械已实现]`：`_check_abstract`（只数「摘要正文」段，附录/证据不计入）
2. **权利要求禁用词零命中** `[机械已实现]`：`_check_claims_banned`（8 词全检，只扫 A 区权项+说明书+摘要）
3. **独立权项须含交底书必要特征（LCS≥60%）** `[暂缓·人工执行]`：已另有独立机械工具 `scripts/check_claim_scope.py`（特征→权项 LCS 映射，阈值 12 字符），本门禁不重复实现；主理人在 Phase 5b 后调用该脚本——此为工具分工，非缺失

## 运行方式

```bash
# 对单成员产出验证
python3 scripts/contract_enforce.py \
  --member contradiction-analyst \
  --output outputs/regression-20261015/a01/T-20261015-A01__contradiction-analyst.md

# 全员 L1/L2 回归时一起跑
python3 scripts/contract_enforce.py \
  --output-dir outputs/regression-20261015/ \
  --exit-on-fail
```

退出码：`0`=全过 · `1`=至少一个成员违反 · `2`=参数错。

## 失败处置

- 首次违反 → 主理人回退该成员（`reverify_with_feedback`）并附具体违反行号
- 二次违反 → 升级用户决策（重做或换成员）
- 3 次违反 → 写入 `failure-XXX` 失败索引 + 调整契约本身

## 维护

- **禁词唯一真源 = 各成员 frontmatter `forbidden_phrases`**（2026-11-07 单源化）：改禁词只改 frontmatter，本文件展示镜像与脚本解析自动跟随；`--self-test` 自测1会校验 6 成员表可解析非空
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

