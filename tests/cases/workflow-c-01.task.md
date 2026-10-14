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
