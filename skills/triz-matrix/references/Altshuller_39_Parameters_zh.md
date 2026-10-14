# TRIZ 39工程参数 · 中英对照

> 英文原名权威源：Altshuller_39_Parameters.csv（jenson500/triz-prompt-engineering）。
> 中文译名为英文标准译名的直译对照，**仅用于从中文场景定位参数编号**；编号为准，译名不引入新事实。
>
> ⚠️ **2026-10-14 缺陷修复（回归实测发现，failure-007）**：#34、#35 两行中文译名曾错填为
> #36、#37 的译名（#34 误作"装置复杂性"、#35 误作"监控与测试的复杂性"）。因
> `scripts/query_triz_matrix.py` 会把本表译名直接打进查询结果，该错误会注入成员上下文——
> 且 #34 可维修性是高频参数。**编号列始终正确，错误仅限译名列**。
> 防复发：改动本表后必须跑 `python3 scripts/verify_triz_data.py`（39 行编号连续 + 译名不重复 + 与 CSV 英文列对齐）。

| # | 英文 | 中文对照 |
|---|---|---|
| 01 | Weight of moving object | 运动物体重量 |
| 02 | Weight of stationary object | 静止物体重量 |
| 03 | Length of moving object | 运动物体长度 |
| 04 | Length of stationary object | 静止物体长度 |
| 05 | Area of moving object | 运动物体面积 |
| 06 | Area of stationary object | 静止物体面积 |
| 07 | Volume of moving object | 运动物体体积 |
| 08 | Volume of stationary object | 静止物体体积 |
| 09 | Speed | 速度 |
| 10 | Force (Intensity) | 力 |
| 11 | Stress or pressure | 应力或压力 |
| 12 | Shape | 形状 |
| 13 | Stability of the object composition | 结构稳定性 |
| 14 | Strength | 强度 |
| 15 | Duration of action of moving object | 运动物体作用时间 |
| 16 | Duration of action of stationary object | 静止物体作用时间 |
| 17 | Temperature | 温度 |
| 18 | Illumination intensity | 光照强度 |
| 19 | Use of energy by moving object | 运动物体能耗 |
| 20 | Use of energy by stationary object | 静止物体能耗 |
| 21 | Power | 功率 |
| 22 | Loss of energy | 能量损失 |
| 23 | Loss of substance | 物质损失 |
| 24 | Loss of information | 信息损失 |
| 25 | Loss of time | 时间损失 |
| 26 | Quantity of substance | 物质数量 |
| 27 | Reliability | 可靠性 |
| 28 | Measurement accuracy | 测试精度 |
| 29 | Manufacturing precision | 制造精度 |
| 30 | Object-affected harmful factor | 作用于物体的有害因素 |
| 31 | Object-generated harmful factor | 物体产生的有害因素 |
| 32 | Ease of manufacture | 可制造性 |
| 33 | Ease of operation | 操作便利性 |
| 34 | Ease of repair | 可维修性 |
| 35 | Adaptability or Versatility | 适应性及多用性 |
| 36 | Device complexity | 装置的复杂性 |
| 37 | Difficulty of detection | 检测与测量的复杂性 |
| 38 | Extent of automation | 自动化程度 |
| 39 | Productivity | 生产率 |
