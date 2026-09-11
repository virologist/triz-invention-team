# T1-T7 生产就绪测试矩阵（v2.2.0）

> 设计日期：2026-09-11 · 执行环境：macOS (darwin) · 源包：my-experts/triz-invention-team @ v2.2.0
> GitHub镜像：virologist/triz-invention-team（PRIVATE，tag v2.2.0）

## 矩阵总览

| 维度 | 用例 | 方式 | 状态 |
|------|------|------|------|
| T1 兼容性 | T1.1 三端安装结构验证 | 静态 | ✅ PASS |
| T1 兼容性 | T1.2 版本一致性+回滚边界 | 静态 | ✅ PASS |
| T2 边界角色 | T2.1 单成员：contradiction-analyst | spawn | ✅ PASS |
| T2 边界角色 | T2.2 单成员：patent-attorney-writer | spawn | ✅ PASS |
| T3 异常路径 | T3.1 上游产出JSON损坏 | spawn | ✅ PASS |
| T3 异常路径 | T3.2 成员失联→inbox直读 | 静态+历史证据 | ✅ PASS |
| T4 并发 | T4.1 scout∥analyst 同时启动 | spawn×2 | ✅ PASS |
| T5 幂等性 | T5.1 同payload二次执行一致性 | spawn×2 | ✅ PASS |
| T6 资源限制 | T6.1 10倍大输入→预算熔断 | spawn | ✅ PASS |
| T7 恢复性 | T7.1 spawn失败重试链 | 静态（skill证据） | ✅ PASS |
| T7 恢复性 | T7.2 跨会话平台文件丢失 | 实测观察 | ✅ PASS |

判定标准：每用例 PASS / FAIL / N-A（不适用需说明）。

---

## T1 兼容性

### T1.1 三端安装结构验证（静态）
验证点：
1. GitHub远端 marketplace.json 可解析，source 路径存在
2. 插件自包含：agents(7)/skills(4)/avatars(8)/settings.json/双plugin.json
3. Claude Code 布局 `.claude-plugin/` ✓
4. WorkBuddy 布局 `.codebuddy-plugin/` ✓

### T1.2 版本一致性（静态）
验证点：源包plugin.json / GitHub plugin.json / GitHub marketplace.json ×2 四处版本号一致；git tag v2.2.0 存在；降级边界=tag回滚可用。

---

## T3 异常路径

### T3.2 成员失联→inbox直读（静态+历史证据）
证据来源：2026-09-10 RedTeam 8-spawn实测，全部产出均在 `/teams/{name}/inboxes/team-lead.json`；
四层防御第0层inbox直读法（agent-team-inbox-fallback skill）。

---

## T7 恢复性

### T7.1 spawn失败重试链（静态）
验证点：agent-team-inbox-fallback skill 四层防御完备性（第0层直读→预防→探测→替代）。

### T7.2 跨会话平台文件丢失（实测观察）
验证点：FAIL-005复现计数+OPERATIONS.md playbook 30秒恢复有效性。
已知：本测试开始时第6次复现（.created-by-session 被删）。

---

## Spawn用例 payload 规范

所有spawn用例遵守：
- prompt含task_payload JSON + RedTeam探针
- 要求result_envelope完整（6必填字段）
- 结束后CI gate跑一遍归档目录回归


---

## 执行结果（2026-09-11 15:11-16:00）

| 维度 | 用例 | 判定 | 关键证据 |
|------|------|------|----------|
| T1 兼容性 | T1.1 三端安装结构 | ✅ PASS | 远端marketplace可解析；source=./plugins/triz-invention-team；远端main=本地HEAD(0801090)；7agents/4skills/8avatars/双清单 |
| T1 兼容性 | T1.2 版本一致性 | ✅ PASS | 五处版本号=2.2.0；远端tag v2.2.0存在 |
| T2 边界角色 | T2.1 analyst单成员 | ✅ PASS | 6必填完整；"仅建模未调度"；C2越表降级正确；[INFERRED]标注规范 |
| T2 边界角色 | T2.2 attorney单成员 | ✅ PASS | 仅撰写未越权审查；法33特征全来自input；摘要≤300字 |
| T3 异常路径 | T3.1 上游JSON损坏 | ✅ PASS | **status=blocked conf=0**；损坏自暴露于issues；零编造；退回上游重产出 |
| T3 异常路径 | T3.2 成员失联→inbox直读 | ✅ PASS | 四层防御skill完备；RedTeam归档15条全在inbox |
| T4 并发 | T4.1 scout∥analyst | ✅ PASS | 双侧独立完成；analyst明示"未消费scout产出"；同task_id不冲突 |
| T5 幂等性 | T5.1 同payload双run | ✅ PASS | 结构/规则/类别一致（status=success；conf差3；gap≥3类×2；点位规则×2）；措辞差异可接受 |
| T6 资源限制 | T6.1 10倍大输入 | ✅ PASS | 12必要特征零遗漏；404字守≤500字预算；缺口≥3类 |
| T7 恢复性 | T7.1 spawn重试链 | ✅ PASS | 四层防御+陷阱A-D；**测试中发现并修复skill阈值90s→120s与team-lead不同步** |
| T7 恢复性 | T7.2 FAIL-005跨会话 | ✅ PASS | 第6次复现活证据（07:59平台删.created-by-session）；printf恢复<30s |

**envelope合规终检：8/8成员100%**（栈平衡提取+按成员聚合）

## 结论

**11/11 全PASS · v2.2.0 生产就绪（PRODUCTION READY）**

测试中发现并当场修复1个真缺陷：agent-team-inbox-fallback skill的等待阈值（90s）与team-lead H4判定阈值（120s）不同步——已对齐修复，复验通过。

回传统计：8成员全部回传。自动通知4/8准点；广播唤醒+2（t41b/t61）；定向唤醒+2（t51-runA重发、t21-analyst 8m45s后回传）——**四层防御第0/2层全部实战验证**。
