# 主理人 VERIFY 记录 · workflow-a-01（L2 全链路回归 · T-20261015-A01）

## 结论：🟡 **条件性通过**（黄区上界 + 二审附条件同意 + K1-K7 + M1-M7 条件）

链路从 L2 起点（"刮粪板耐磨与易更换"）完整跑完 Phase 0→5b 全部阶段并产出 8 份主交付。
**不构成「绿·可立即提交」**——需提交前完成 M7 补检；本文为提交前必办清单 + 已落盘事实核验。

## 链路 8 份交付（全部落盘可验）

| 序 | 阶段 | 成员 | 任务ID | 状态 | 关键事实 |
|---|---|---|---|---|---|
| 1 | Phase 1-2 | contradiction-analyst | T-20261015-A01 | success | 23项技术矛盾+1物理矛盾·24组矩阵查询（2组无推荐已降级）·5方向 D1-D5 |
| 2 | Phase 3 R1-R3 | patent-search-scout | T-20261015-A01 | success | 三轮14检索式·31条引用核验（28过三要素）·**综合红**（4条X级） |
| 3 | Phase 2 iter2 | contradiction-analyst | T-20261015-A02 (重试A02b) | success | 4路径全回应（3采纳+1有限采纳）·8组实跑·必要特征N1-N6 |
| 4 | Phase 3 复检 | patent-search-scout | T-20261015-A03 | success | 30格比对·**红→黄**（N2/N5 5/5未命中） |
| 5 | Phase 4a | patent-examiner-sim | T-20261015-A04 | success | 8条攻击（7附证据）·**黄（黄区上界4/5）**·M1-M7强制修复 |
| 6 | Phase 4b | second-opinion-reviewer | T-20261015-A05 | partial | **⚠附条件同意**·K1-K7七项前置条件 |
| 7 | Phase 5a | disclosure-architect | T-20261015-A06 | success | 交底书·必要4+可选6·缺口7类·M1-M6兑现M7待办·K表4兑现3待办 |
| 8 | Phase 5b | patent-attorney-writer | T-20261015-A07 | success | 申请文件草稿·**摘要258字符（python3实测）**·零禁用词·零自评（防failure-006） |

## 全链成本（机械计量 + 双轨制墙钟）

| 指标 | 数值 |
|---|---|
| 累计产出 | ≈83.8K out-tokens（占预算 70%） |
| 累计墙钟（成员落地实测） | 2,123s（≈35.4min） |
| 累计墙钟（含取消+重试·下界） | 2,423s（≈40.4min） |
| 链式墙钟预算 | ≤ 45 min（符合 A6 断言 A6 120K/45min） |

## 提交前必办（不阻塞本轮回归，但投递前必须完成）

### M7 强制（A04）= K1 + K6 的核心
- **M7a N2 定向检索**：`（刮板 OR 刮粪 OR 刮刀）AND （楔面 OR 楔形面 OR 斜面）AND （自锁 OR 摩擦角 OR 自锁角）AND （行进方向 OR 推进方向）`
- **M7b N1 定向检索**：「承载本体 / 中介座 / 刃条 三级可分离 + 中介座运行期不动」
- **M7b 扩**：A06 附录D 新识别"不含螺栓与开口销"覆盖缺失，须增补两条辅助式
- 完成判据：**权项每一结构限定 ↔ 检索覆盖说明** 对照表（全填不可有空）

### K2 提交前补强
- N2 支撑强度替代方案评估（附录A 已交付·**M3 vs A-1 取舍**应保持"保 M3 作清楚性限定 / 创造性支点上移 F4+F1(a)+F2(b) 组合"）

### C3 程序闭环
- C3_CONFIRMATION.md 已就位；主理人已确认按"黄"放行（时间线见该文件）

## 已知缺陷（诚实登记）

1. **failure-008**（已修·不在本轮触发）：scaffold 违约束 ID / meter 窄正则 / gate 死代码
2. **A02 首次超时**（已修·H4 SOP 强化）：30min 停滞后 TaskStop + brief 重试 2m40s 通过
3. **A07 首次 500 错误**（已修·按H4重试）：平台级错误非成员错误
4. **A04/A05 计分客观性偏弱**（A05 评级）：双方裁决方向一致，结论不敏感

## 文件清单（路径相对 triz-invention-team 根）

```
outputs/regression-20261015/a01/
├── T-20261015-A01__contradiction-analyst.md      (14.7KB)
├── T-20261015-A01__patent-search-scout.md       (31.7KB)
├── T-20261015-A02__contradiction-analyst.md     ( 8.2KB)
├── T-20261015-A03__patent-search-scout.md       (10.9KB)
├── T-20261015-A04__patent-examiner-sim.md       (14.7KB)
├── T-20261015-A05__second-opinion-reviewer.md   (15.4KB)
├── T-20261015-A06__disclosure-architect.md      (25.0KB)
├── T-20261015-A07__patent-attorney-writer.md    (21.6KB)
├── C3_CONFIRMATION.md                            (程序补记)
├── _VERIFY.md                                    (本文件)
├── RUN_INFO.md                                   (派单指引)
└── metrics.jsonl                                 (8行台账)
```

## 结论复核（rank 与建议）

- **本回归 L2 全链路工程价值**：7 PASS / 1 partial / 0 FAIL（runner 视阈）
- **真实可提交性**：🟡 黄，须 M7 补检通过后转绿；M7 阳性则按 K6 转红回退 Phase 2
- **下一轮最小动作**：执行 M7a/M7b 两条定向检索 → 重新跑 Phase 3 复检 + Phase 4 一审二审
