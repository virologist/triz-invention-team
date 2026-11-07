# 任务包 · 回归用例 workflow-a-01（Workflow A 全流程 · 仅 L2 级人工触发）

## objective
从发明想法到申请文件草稿的全流程陪跑：猪舍粪沟刮粪板耐磨与易更换。
**本用例为 L2 级**：涉及 6 成员全链路，耗时与 token 开销大，**默认不由 CI 自动跑**，
仅在版本发布前由人工触发（`python3 scripts/run_regression.py --level L2`）。

## context
- 场景：猪舍粪沟刮粪板，聚氨酯板面磨损快，更换需停栏清空。
- 已有部件清单：刮粪板本体、牵引链条、驱动减速机、导轨。
- 可接受改造成本量级：≤ 单套刮粪系统造价的 20%。
- 维护频次预期：季检。
- 失效后果容忍度：单条粪沟停运可接受，全场停运不可接受。

## constraints
- 全流程 6 成员：解其纷→甄无遗→严三性→审外审→谭无隐→权要达。
- G1-G5 门禁逐项校验，任一未过不得进入下一 Phase。
- 摘要 ≤300 字必须机械计量；权项禁用词正则零命中。
- 全流程 token ≤120K、墙钟 ≤45min，超 80% 预警。

## output_format
各 Phase 落盘 outputs/regression-<date>/T-<id>__<member>.md；主理人汇编 _VERIFY.md。

## task_boundary
见各成员 MD 的能力/禁止边界；跨 Phase 交接必须经主理人中转（禁止横直连）。


## task_package_json（B21 结构化校验源 · 机器可读）

```json
{
  "objective": "L2 全链路：发明想法 -> TRIZ建模 -> 三轮查新 -> 对抗审查+二审 -> 交底书 -> 申请文件草稿（详见 md 正文各阶段定义）",
  "output_format": "markdown 落盘文件（正文最前置 result_envelope JSON 信封，6 必填字段）",
  "constraints": [
    "未完成3轮查新禁止撰写申请文件",
    "X级威胁出现须走 C3 检查点确认",
    "摘要须附 python len() 机械验证证据",
    "全程走主理人装配链派单，禁止成员直连"
  ],
  "task_boundary": "属于 Workflow A 全部 6 阶段编排；不属于：成员自发跳阶段、绕过门禁推进",
  "acceptance_criteria": [
    {
      "check": "6 成员全部落盘",
      "judge_mode": "机",
      "threshold": "all landed，源 tests/cases/workflow-a-01.expected.json#A2"
    },
    {
      "check": "G1-G5 门禁登记",
      "judge_mode": "机+人",
      "threshold": "gates 语义匹配，源 tests/cases/workflow-a-01.expected.json#A3"
    },
    {
      "check": "摘要 <= 300 字符（机械计量）",
      "judge_mode": "机",
      "threshold": "<= 300，源 tests/cases/workflow-a-01.expected.json#A4"
    },
    {
      "check": "二审条件逐条兑现对账",
      "judge_mode": "机",
      "threshold": "conditions_closed，源 tests/cases/workflow-a-01.expected.json#A7"
    }
  ]
}
```
