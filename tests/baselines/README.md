# tests/baselines/ — 回归基线归档

> 2026-11-08 工作区整理：`outputs/regression-*` 历史运行产物迁入本目录（outputs/ 只留给未来的运行产物）。
> 目录组织由并发整理会话完成，路径引用同步由整理会话收口。

## 目录结构

| 目录 | 内容 | 来源 |
|---|---|---|
| `l2-full-a01/` | **L2 全链路基线**（workflow-a-01 · 刮粪板耐磨 · 8 阶段全交付 + _VERIFY + metrics） | outputs/regression-20261015/a01 |
| `l1-analyst-b01/` | L1 analyst 基线（workflow-b-01 · 冷链保温层） | outputs/regression-20261015/b01 |
| `20261014-p0-2/` | P0-2 定向回归归档（2026-10-14 · 肉鸡舍地暖域） | outputs/regression-20261014 |
| `_pre-fix-b01/` | failure-008 违约 ID 首跑归档（缺陷发现即价值的证据） | outputs/regression-20261015/_pre-fix-b01 |
| `RUN_INFO-20261015.md` | 20261015 批次顶层派单指引 | outputs/regression-20261015/RUN_INFO.md |
| `_archive/spawn-prompts-20261015.tar.gz` | 当批 spawn 文案打包存档 | 并发整理会话归档 |

## 硬依赖警示（移动前必查）

以下脚本**硬编码引用本目录**，再移动需同步改码：

- `scripts/contract_enforce.py --self-test` → `l2-full-a01/T-20261015-A07__patent-attorney-writer.md`（自测2 样本）
- `scripts/check_claim_scope.py --l2` → `l2-full-a01/T-20261015-A06/A07`（默认输入路径）
- `scripts/preflight_check.py` L40 注释 → `l2-full-a01 metrics.jsonl`（预算校准口径）

## 基线内的旧路径说明

本目录内历史产物（T-\*信封/spawn 文案/RUN_INFO）正文中保留着迁移前的 `outputs/regression-*` 路径——
这是**历史快照原样**（当时真实运行路径），不随迁移改写；引用它们时以本 README 的映射为准。

## 使用方式

```bash
# L1 回归对比
python3 scripts/run_regression.py --case workflow-b-01 --dir tests/baselines/l1-analyst-b01
# L2 全链路对比
python3 scripts/run_regression.py --case workflow-a-01 --dir tests/baselines/l2-full-a01
# 契约门禁自测（读 l2-full-a01 基线）
python3 scripts/contract_enforce.py --self-test
# 权项范围 LCS 校验（默认读 l2-full-a01 A06/A07）
python3 scripts/check_claim_scope.py --l2
```
