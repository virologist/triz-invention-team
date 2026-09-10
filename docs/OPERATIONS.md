# Expert Package Operations Playbook

> 跨会话/平台时序问题的可观测性补全。直接解决FAIL-005"silent file loss"模式。

## 症状

打开新会话时，专家包git tracked记录显示`settings.json`和`.created-by-session`存在，但平台工作树显示"deleted"。直接执行`validate_expert.py`会失败：

```
❌ 1 error(s):
   • Team type must have settings.json
```

## 根因

平台层工作树快照在跨会话切换时可能丢失git-tracked files（不是文件本身丢失，是工作树引用断链）。git log完整保留历史，但working tree未同步。

## 恢复playbook（30秒可解决）

```bash
cd /Users/biodog/.workbuddy/plugins/marketplaces/my-experts/plugins/triz-invention-team

# 1. 恢复settings.json（内容永不变）
cat > settings.json << 'EOF'
{
  "agent": "triz-invention-team-team-lead"
}
EOF

# 2. 恢复.created-by-session（用最近一次注册时的session-id）
# 从git log恢复：
PREV_SESSION=$(git log -1 --format=%s --diff-filter=A -- .created-by-session 2>/dev/null | head -1)
# 或直接用固定session（如果使用固定session）：
echo "f17264fb-02e5-46a0-b51b-f910fa523033" > .created-by-session

# 3. 验证+注册+打包
python3 ~/.workbuddy/plugins/cache/workbuddy-builtin/skill-expert-manager/0.1.0/scripts/validate_expert.py .  # 期望 ✅
python3 ~/.workbuddy/plugins/cache/workbuddy-builtin/skill-expert-manager/0.1.0/scripts/register_expert.py . --session-id f17264fb-02e5-46a0-b51b-f910fa523033  # 期望 🎉
python3 ~/.workbuddy/plugins/cache/workbuddy-builtin/skill-expert-manager/0.1.0/scripts/package_expert.py . /path/to/outputs/  # 期望 ✅
```

## 验证清单（5条全过才算系统可加载）

1. `python3 scripts/agent_ci_gate.py --results-dir outputs/ --self-test` → `✅ self-test: 合规样本通过，不合规样本检出N条错误`
2. `python3 scripts/agent_ci_gate.py --results-dir outputs/` → `合规率(扣除legacy后): 100.0%`
3. `git status` → `working tree clean`
4. `validate_expert.py` → `✅ Expert package is valid!`
5. `register_expert.py` → `🎉 Expert 'triz-invention-team' is now registered`

## 已知相关failure索引

- **failure-005** (settings.json/.created-by-session跨会话丢失) — 4次记录于2026-09-03~10
- **failure-003** (ACP双协议冲突) — 2026-09-02修复
- **failure-004** (tie-break利益冲突边界) — 2026-09-03修复

## 自动化建议（未来）

1. **pre-session health check**：新会话开始时自动跑恢复playbook
2. **跨会话git hash对比**：v2.2系统的"已注册"状态应该能跨会话持久（当前依赖注册脚本在每次新会话调用）
3. **将settings.json和.created-by-session纳入CI gate脚本校验范围**——`agent_ci_gate.py`应同时校验settings.json存在+内容正确
