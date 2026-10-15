# L2 回归交付摘要 · T-20261015-A01

> 任务：从「猪舍粪沟刮粪板耐磨与易更换」发明想法出发，跑完 8 个阶段并产出可投递申请文件草稿。

## 输入
- 任务包：tests/cases/workflow-a-01.task.md
- 装配链：assemble_spawn_prompt.py（shared-core 联邦）
- 失败记忆注入：failure_memory.py（按成员+任务域筛）
- 门禁：preflight_check.py + agent_ci_gate.py + verify_triz_data.py

## 主交付（按用途）

| 阶段 | 用途 | 路径 |
|---|---|---|
| 矛盾建模 | 技术矛盾识别与发明方向 | `T-20261015-A01__contradiction-analyst.md` |
| 查新 | 三轮递进检索与威胁清单 | `T-20261015-A01__patent-search-scout.md` |
| 差异化改进 | 应对X级的TRIZ二次求解 | `T-20261015-A02__contradiction-analyst.md` |
| 复检评级 | 定向复检与评级更新 | `T-20261015-A03__patent-search-scout.md` |
| 一审三性 | 严三性对抗攻击与裁决 | `T-20261015-A04__patent-examiner-sim.md` |
| 二审附条件 | 元审查+附加条件 | `T-20261015-A05__second-opinion-reviewer.md` |
| 交底书 | 必要/可选特征分层固化 | `T-20261015-A06__disclosure-architect.md` |
| 申请文件草稿 | 权利要求+说明书+摘要 | `T-20261015-A07__patent-attorney-writer.md` |

## 最终裁决
**🟡 黄**（黄区上界 4/5）——可推进但**须提交前完成 M7 补检**（N2/N1 定向检索）
- M7 阳性 → 按 K6 约定回退 Phase 2
- M7 阴性 → 可投递

## 核心防御点（写作时着重说明）
- F1 三级体（承载本体 / 中介座 / 耐磨刃条）+ 封闭式固定连接（焊接/过盈/螺纹）
- F2 楔面自锁（β ≤ arctan(μ) + 垂直推入限定）
- F3 F2 绑定的免工具解脱复合限定（不能单独成句）
- F4 单向行程 / 防倒抽限位

## 后续最小动作
1. 跑 M7a/M7b 两条定向检索
2. 重新跑 Phase 3 复检（更新评级）
3. 必要时 Phase 4 一审 + 二审（按 M7 结果处置）
