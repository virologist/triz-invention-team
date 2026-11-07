# 任务包 · 回归用例 workflow-c-01（Workflow C 查新+授权前景评估）

## objective
对「一种基于图像识别的鸡球虫卵囊自动计数方法」做三轮查新与授权前景评估。
固定用例，用于回归验证：三轮检索递进 / X-Y-A-R-P-E 分级含 E 类 / 三性对抗审查 / 分级决策树。

## context
- 方案：显微图像采集 → CNN 分割卵囊 → 计数输出；用于鸡球虫病感染强度评估。
- 申请日：假定 2026-01-15，无优先权声明。
- 已有部件清单：显微镜、CMOS 相机、工控机、标注数据集。
- 可接受改造成本量级：≤ 现有镜检人工成本的 30%。
- 失效后果容忍度：漏检率 ≤5% 可接受，>15% 不可接受。

## constraints
- 三轮检索式必须可复现（写出检索式与命中数），search_rounds ≥ 3。
- 对比文件分级必须覆盖 X/Y/A/R/P/E 六类，E 类必须显式给出结论（有/无/未检索）。
- 法条号一律以 skills/patent-law/references/patent-law.md 核对后引用，禁止凭记忆。
- 客体预审：图像识别+计数方法是否落入法25「智力活动规则」须显式判定。
- 禁用模糊词；无法自估耗时填 0 并注明。

## output_format
写入落盘文件，含：search_expressions（三轮）、threat_list（含 X/Y/A/R/P/E 分级）、
xyape_grades、three_property_risk（三性逐项：法条号+结论+依据+待补信息）、
objection_preview（审查意见预判）、result_envelope（置最前）。

## task_boundary
属于本任务：三轮查新、对比文件分级、三性风险评估、布局分析。
不属于：撰写申请文件（属 patent-attorney-writer）、矛盾建模（属 contradiction-analyst）。


## task_package_json（B21 结构化校验源 · 机器可读）

```json
{
  "objective": "对用例给定技术方案执行三轮查新（关键词/分类号/差异化验证），输出威胁分级与三性动态评估（详见 md 正文）",
  "output_format": "markdown 落盘文件（正文最前置 result_envelope JSON 信封，6 必填字段）",
  "constraints": [
    "专利号/公开日/权利要求原文必须来自检索渠道实际返回，禁止凭记忆补齐",
    "引用三要素（号+题+关系）缺一不计入 threat_list",
    "检索渠道节须显式登记主源与档位（Google Patents/himmpat 主源，L1-L4 降档链）",
    "禁用模糊词同 b-01 词表"
  ],
  "task_boundary": "属于：三轮查新、威胁分级、三性动态评估、检索渠道登记；不属于：权项撰写、审查模拟、交底书",
  "acceptance_criteria": [
    {
      "check": "search_rounds >= 3",
      "judge_mode": "机",
      "threshold": ">= 3，源 tests/cases/workflow-c-01.expected.json#A4"
    },
    {
      "check": "E类结论显式（有/无/未检索）",
      "judge_mode": "机",
      "threshold": "required_regex 命中，源 tests/cases/workflow-c-01.expected.json#A5"
    },
    {
      "check": "法25客体预审显式",
      "judge_mode": "机",
      "threshold": "required_regex 命中，源 tests/cases/workflow-c-01.expected.json#A6"
    },
    {
      "check": "检索渠道节显式（主源/档位登记）",
      "judge_mode": "机",
      "threshold": "_check_search_channel 命中，源 scripts/contract_enforce.py（生效日 2026-11-07 后）"
    }
  ]
}
```
