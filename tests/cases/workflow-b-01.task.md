# 任务包 · 回归用例 workflow-b-01（Workflow B 单点TRIZ突破）

## objective
对「冷链运输箱体保温层厚重导致装载容积不足」做 TRIZ 矛盾建模与发明原理求解。
固定用例，用于回归验证：装配链 / 矛盾矩阵查询 / 方向生成 / 信封合规 / 无模糊词。

## context
- 场景：冷藏车箱体，保温层厚度 100mm，占箱体容积 18%，导致单次装载量下降。
- 现有方案：增厚保温层以提升保温性能（进一步压缩容积）或减薄（保温失效）。
- 已有部件清单（可复用）：聚氨酯保温层、玻璃钢蒙皮、制冷机组、隔板。
- 可接受改造成本量级：≤ 单箱制造成本的 10%。
- 维护频次预期：年检。
- 失效后果容忍度：局部保温性能下降可接受，整箱失冷不可接受。

## constraints
- 原理编号必须来自 `scripts/query_triz_matrix.py` 实跑结果，注明查询命令与退出码。
- 矩阵无推荐的交叉点必须如实说明「矩阵无推荐」，禁止编造。
- 方向 ≥ 3 个，每个标注原理编号。
- 禁用模糊词（大约/左右/等/优选/若干/高效/快速/大幅）。
- 不得撰写专利申请文件（越界）。
- 无法自估耗时时 metrics.duration_ms 填 0 并在 issues 注明。

## output_format
写入落盘文件，含：contradiction_model（改善/恶化参数含 39 参数编号与名称）、
principle_refs（含查询命令与退出码）、directions（≥3）、invention_level、comparison_table、
result_envelope（置于正文最前，JSON 代码块，含 6 必填字段 + metrics）。

## task_boundary
属于本任务：矛盾建模、矩阵查询、原理求解、方向生成、五级水平判定、方案对比。
不属于：专利撰写、查新检索、交底书、三性审查。越界需求在 next_agent_hint 指出后停止。


## task_package_json（B21 结构化校验源 · 机器可读）

```json
{
  "objective": "对「冷链运输箱体保温层厚重导致装载容积不足」做 TRIZ 矛盾建模与发明原理求解，产出 >=3 个候选方向（详见 md 正文 objective 段）",
  "output_format": "markdown 落盘文件（正文最前置 result_envelope JSON 信封，6 必填字段）",
  "constraints": [
    "原理编号必须来自 scripts/query_triz_matrix.py 实跑，注明命令与退出码",
    "矩阵无推荐必须如实说明，禁止编造",
    "方向 >= 3，每个标注原理编号",
    "禁用模糊词（大约/左右/等/优选/若干/高效/快速/大幅）",
    "不得撰写专利申请文件（越界）"
  ],
  "task_boundary": "属于：矛盾建模、矩阵查询、原理求解、方向生成、五级判定、方案对比；不属于：专利撰写、查新检索、交底书、三性审查",
  "acceptance_criteria": [
    {
      "check": "directions >= 3",
      "judge_mode": "机",
      "threshold": ">= 3，源 tests/cases/workflow-b-01.expected.json#A4"
    },
    {
      "check": "禁用模糊词零命中",
      "judge_mode": "机",
      "threshold": "= 0，源 tests/cases/workflow-b-01.expected.json#A5"
    },
    {
      "check": "原理编号实跑（query_triz_matrix + 退出码）",
      "judge_mode": "机",
      "threshold": "required_regex 命中，源 tests/cases/workflow-b-01.expected.json#A6"
    },
    {
      "check": "信封 6 必填齐全",
      "judge_mode": "机",
      "threshold": "schema required，源 skills/agent-protocol/result_envelope.schema.json"
    }
  ]
}
```
