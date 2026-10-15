# 契约执行门禁（P0-S1-1 配套文档）

> 每个成员 frontmatter 末尾的 `must_verify` 项是**契约**，本文件是其**机器可执行规范**。
> CI gate（`scripts/contract_enforce.py`）按 `member_id` 查本表 → 实测成员产出 → 违反即 fail。

## 6 成员契约清单

### contradiction-analyst
**禁止触发词**（产出全文 grep 命中即违反）：
- `approximately|左右|大概|估计|约\d+字`
- `I think|我觉得|可能|也许`
- 矩阵无推荐未标注`已降级`

**强制验证**（CI gate 解析）：
1. **directions ≥3**：`re.findall(r'(#?\d+\.|方向[1-9]|IP #\d+)', out) >= 3`
2. **原理编号实跑**：`re.search(r'(query_triz_matrix|退出码)', out)` 必须命中
3. **无编造**：所有 IP 编号必须能溯源到 `query_triz_matrix.py exit=0` 的输出（自检指令：解析 `principle_refs` 段，对每条 IP 编号跑 `python3 scripts/query_triz_matrix.py --improve N --worsen M` 比对）

### patent-search-scout
**禁止触发词**：
- `approximately|左右|估计|凭记忆|推测`
- `应用号|公开号.*?未核实`
- `(我|我们)知道.*?(某专利|某文献)`（无引用三要素的"我们知道"）

**强制验证**：
1. **X/Y/A/R/P/E 六类全部显式**：`re.search(r'[XYARPE]\s*类', out)` 命中 ≥6
2. **search_rounds ≥3**：`re.findall(r'(R[123]|第[一二三]轮)', out) >= 3`
3. **三要素核验**：每条引用必须含「专利号+标题+与方案关系」（正则不强制，由CI 跑交叉验证）

### patent-examiner-sim
**禁止触发词**：
- `approximately|基本|整体上.*?可以|应当`
- `建议.*?考虑.*?(?!附法条号|附证据)`

**强制验证**：
1. **裁决显式（绿/黄/红）**：`re.search(r'(裁决[：:].*?(绿|黄|红)|结论[：:].*?(绿|黄|红))', out)` 必须命中
2. **每条攻击附证据四元组**：`re.findall(r'(X级|特征|命中|依据)', out) >= 攻击数*4`
3. **修复清单分级**：`re.search(r'(强制|建议)', out)` 必须显式

### second-opinion-reviewer
**禁止触发词**：
- `我同意.*?不附理由`
- `基本.*?通过`
- `无需.*?修改`

**强制验证**：
1. **二次表态显式**：`re.search(r'(✅同意|⚠附条件|🔴不同意)', out)` 必须命中
2. **⚠附条件必须给条件清单**：`re.search(r'(附加条件|条件清单)', out)` 必须命中
3. **元审查 ≠ 替一审重做**：`re.search(r'(补强项|元审查)', out)` 必须命中

### disclosure-architect
**禁止触发词**：
- `estimated|约|估计|大约`
- `实验.*?(?<!本发明|申请人).{0,15}表明`（编造实验数据）
- `(优化|显著|大幅).*?(?!附数据|附实施例)`

**强制验证**：
1. **必要/可选特征分层**：`re.search(r'(必要特征|可选特征)', out)` 必须显式
2. **缺口清单显式**：`re.search(r'(缺口|待补)', out)` 必须命中
3. **实施例 ≥2 档**：`re.findall(r'实施例\s*\d', out) >= 2`

### patent-attorney-writer
**禁止触发词**：
- `约\d+字|左右|估计.*?字`（**failure-006 复发防御**）
- `approximately|大致|基本`
- `(显著|大幅|明显|高效).*?(?!附实测|附数据)`

**强制验证**：
1. **摘要 ≤300 字符 + 机械验证证据**：
   - 抽取「说明书摘要」段文本 → `len(txt) <= 300`
   - 全文必须出现 `python3.*len\(.*\)\s*=\s*\d+` 或 `len(.*)=\d+ 字符` 字样
2. **权利要求禁用词零命中**：8 词全检（grep claims 段）
3. **独立权项须含交底书必要特征**：按交底书段取必要特征，与独立权项做最长公共子串 ≥ 60%

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

- 契约字段与本表必须同步：改 frontmatter `must_verify` 时同步改本表
- 禁止触发词与 failure-006/007 教训同步：所有新失败都回灌到 `forbidden_phrases` 段
