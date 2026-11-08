#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_ci_gate.py — TRIZ发明专家团 CI/CD发布门禁脚本

设计目标：
- 每次git commit前自动跑核心契约+关键不变量校验（默认warn-only）
- 解析outputs/目录下所有*-results.json，提取每个成员产出中的上行信封
- 用JSON Schema自动校验信封完整性
- 输出通过率/失败列表，作为团队交付质量门禁

用法：
  python3 scripts/agent_ci_gate.py [专家包根目录] [--results-dir outputs/] [--strict]
  python3 scripts/agent_ci_gate.py --self-test  # 跑schema自测

设计原则（来自agent-team-inbox-fallback skill）：
- 默认warn-only（首次部署不阻断），验证稳定后切strict
- 所有结果汇总到 CI_REPORT.json 便于追踪
- 缺失字段标红但不强制fail（避免误报）
"""
import sys, os, json, argparse, re, glob, datetime
from pathlib import Path

# 支持无jsonschema库的手动校验（与expert-failures一致：手动校验兼容）
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent / "skills" / "agent-protocol"
ENVELOPE_SCHEMA_PATH = SKILL_DIR / "result_envelope.schema.json"
PAYLOAD_SCHEMA_PATH = SKILL_DIR / "task_payload.schema.json"

# 已知7代理ID（白名单）
KNOWN_AGENTS = {
    "contradiction-analyst", "patent-search-scout", "patent-examiner-sim",
    "disclosure-architect", "patent-attorney-writer",
    "second-opinion-reviewer", "triz-invention-team-team-lead",
}

# 历史归档边界：2026-09-03前归档标记为legacy（pre-v2.0无信封）
LEGACY_CUTOFF = "2026-09-03"

def manual_validate(instance: dict, schema: dict) -> list:
    """无jsonschema依赖的手动校验：必填+枚举+pattern。返回错误列表（空=通过）。"""
    errors = []
    required = schema.get("required", [])
    for f in required:
        if f not in instance:
            errors.append(f"missing required field: {f}")
    props = schema.get("properties", {})
    for k, v in instance.items():
        if k not in props:
            if schema.get("additionalProperties") is False:
                errors.append(f"unknown field (additionalProperties=false): {k}")
            continue
        ptype = props[k].get("type")
        if ptype == "integer":
            if not isinstance(v, int):
                errors.append(f"{k}: expected integer, got {type(v).__name__}")
            else:
                mn, mx = props[k].get("minimum"), props[k].get("maximum")
                if mn is not None and v < mn: errors.append(f"{k}: {v} < min {mn}")
                if mx is not None and v > mx: errors.append(f"{k}: {v} > max {mx}")
        elif ptype == "string":
            if not isinstance(v, str):
                errors.append(f"{k}: expected string, got {type(v).__name__}")
            else:
                if "enum" in props[k] and v not in props[k]["enum"]:
                    errors.append(f"{k}: '{v}' not in enum {props[k]['enum']}")
                pat = props[k].get("pattern")
                if pat and not re.match(pat, v):
                    errors.append(f"{k}: '{v}' doesn't match pattern {pat}")
    return errors


def validate_envelope(envelope: dict, schema: dict) -> list:
    if HAS_JSONSCHEMA:
        try:
            jsonschema.validate(envelope, schema)
            return []
        except jsonschema.ValidationError as e:
            return [str(e.message)]
    return manual_validate(envelope, schema)


# 信封提取：栈平衡JSON扫描（替代贪婪正则，处理嵌套{}）。仅收含 agent_id 的 dict，避免误报。
def extract_envelopes(text: str) -> list:
    """栈平衡JSON扫描（替代贪婪正则，处理嵌套{}）。返回[(envelope_dict, True), ...]列表。"""
    results = []
    i = 0
    while i < len(text):
        if text[i] != '{':
            i += 1
            continue
        depth = 0
        in_str = False
        esc = False
        start = i
        while i < len(text):
            c = text[i]
            if in_str:
                if esc: esc = False
                elif c == '\\': esc = True
                elif c == '"': in_str = False
            else:
                if c == '"': in_str = True
                elif c == '{': depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:i+1]
                        try:
                            env = json.loads(candidate)
                            if isinstance(env, dict) and 'agent_id' in env:
                                results.append((env, True))
                        except Exception:
                            pass
                        break
            i += 1
        i += 1
    return results


def check_wall_clock(envelope: dict) -> list:
    """CYCLE-1 · S-E12：墙钟（duration_ms_wall）口径校验 —— 单一真源实现。

    判据（返回 WARN 列表，空 = 通过）：
      · 有 metrics 但缺 duration_ms_wall → 主理人未回填墙钟，预算熔断依据缺失
      · duration_source 取值不在 {self_report, lead_measured, estimated} → 口径非法

    设计约束：不改 schema 的 required（避免破 9 个历史 failure 归档 + 3 用例基线），
    仅 WARN 不 FAIL——墙钟缺失是流程瑕疵，不是信封结构性违规。
    """
    warnings = []
    m = envelope.get("metrics")
    if not isinstance(m, dict) or not m:
        return warnings
    if "duration_ms_wall" not in m:
        warnings.append("metrics 存在但缺 duration_ms_wall（主理人未回填墙钟·预算熔断依据缺失）")
    src = m.get("duration_source")
    if src is not None and src not in ("self_report", "lead_measured", "estimated"):
        warnings.append(f"duration_source 取值非法：{src}")
    return warnings


def _process_baseline_markdown(md_path: Path, schema: dict) -> dict:
    """CYCLE-1 · S-E22：基线 markdown 信封校验（fallback 扫描路径）。

    基线成员产出（T-*__<member>.md）把上行信封以 ```json 代码块直接埋在正文，
    与 results.json 的 []{from,text} 消息数组结构不同。本函数复用 extract_envelopes
    + validate_envelope，对每个信封逐条判定，产出与 process_results_file 同构的报告。
    """
    report = {"file": md_path.name, "messages": [], "total": 0, "valid": 0, "partial": 0,
              "failed": 0, "legacy": 0, "details": []}
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception as e:
        report["messages"].append(f"read error: {e}")
        return report
    envelopes = extract_envelopes(text)
    if not envelopes:
        report["failed"] = 1
        report["details"].append({"sender": md_path.stem, "result": "no_envelope_found",
                                  "issue": "基线 markdown 中未发现上行信封"})
        return report
    for env, _ok in envelopes:
        report["total"] += 1
        errors = validate_envelope(env, schema)
        agent_id = env.get("agent_id", "?")
        sender = agent_id
        agent_mismatch = (agent_id != sender) and (agent_id not in KNOWN_AGENTS)
        wall_warn = check_wall_clock(env)
        if not errors and not agent_mismatch:
            report["valid"] += 1
            detail = {"sender": sender, "agent_id": agent_id, "result": "PASS"}
            if wall_warn:
                detail["warnings"] = wall_warn
            report["details"].append(detail)
        elif errors:
            if env.get("status") == "partial":
                report["partial"] += 1
            else:
                report["failed"] += 1
            report["details"].append({"sender": sender, "agent_id": agent_id,
                                      "result": "FAIL", "errors": errors[:3]})
        elif agent_mismatch:
            report["failed"] += 1
            report["details"].append({"sender": sender, "agent_id": agent_id, "result": "FAIL",
                                      "errors": [f"agent_id '{agent_id}' unknown"]})
    return report


def process_results_file(results_path: Path, schema: dict) -> dict:
    """处理单个*-results.json文件，返回校验报告。"""
    report = {"file": results_path.name, "messages": [], "total": 0, "valid": 0, "partial": 0, "failed": 0, "legacy": 0, "details": []}
    # legacy判定：文件名以arch/integration/e2e/tiebreak/search-r2等开头且时间早于cutoff视为legacy
    is_legacy = any(prefix in results_path.name for prefix in ("arch-", "tiebreak-", "search-r2-", "integration-")) or "search-r2" in results_path.name
    # CYCLE-1 · S-E22：基线 markdown 形态（fallback 扫描）——信封直接埋在正文里，
    # 不是 results.json 的 []{from,text} 消息数组。走独立分支解析。
    if results_path.suffix == ".md":
        return _process_baseline_markdown(results_path, schema)
    try:
        with open(results_path) as f:
            data = json.load(f)
    except Exception as e:
        report["messages"].append(f"load error: {e}")
        return report

    for msg in data:
        if msg.get("from") == "system":
            continue
        sender = msg.get("from", "unknown")
        text = msg.get("text", "")
        report["total"] += 1
        envelopes = extract_envelopes(text)
        # 兼容旧版函数返回空（保持API稳定）
        if not envelopes:
            if is_legacy:
                report["legacy"] += 1
                report["details"].append({"sender": sender, "result": "LEGACY", "issue": "pre-v2.0归档，不计入合规率分母"})
            else:
                report["failed"] += 1
                report["details"].append({"sender": sender, "result": "no_envelope_found", "issue": "未发现上行信封"})
            continue
        # 取首个可解析信封
        parsed_env = None
        for env, ok in envelopes:
            if ok:
                parsed_env = env
                break
        if parsed_env is None:
            report["failed"] += 1
            report["details"].append({"sender": sender, "result": "envelope_parse_error", "issue": f"发现{envelopes}个信封候选但均无法JSON解析"})
            continue
        # schema校验
        errors = validate_envelope(parsed_env, schema)
        agent_id = parsed_env.get("agent_id", "?")
        # CYCLE-1 · S-E12：墙钟缺失 WARN（不阻断）。判据实现见 check_wall_clock()。
        wall_warn = check_wall_clock(parsed_env)
        # agent_id一致性检查（应与产出from一致或为已知agent）— 探针/测试agent放宽为warn
        agent_mismatch = (agent_id != sender) and (agent_id not in KNOWN_AGENTS)
        if not errors and not agent_mismatch:
            report["valid"] += 1
            report["details"].append({"sender": sender, "agent_id": agent_id, "result": "PASS",
                                      "warnings": wall_warn} if wall_warn else
                                      {"sender": sender, "agent_id": agent_id, "result": "PASS"})
        elif errors:
            if parsed_env.get("status") == "partial":
                report["partial"] += 1
            else:
                report["failed"] += 1
            report["details"].append({"sender": sender, "agent_id": agent_id, "result": "FAIL", "errors": errors[:3]})
        elif agent_mismatch:
            # 探针agent（带"-probe"/"-reg"/"-test"后缀）放宽为warn（partial不算fail）
            is_probe = any(suffix in agent_id for suffix in ("-probe", "-reg", "-test", "-r2"))
            if is_probe:
                report["partial"] += 1
                report["details"].append({"sender": sender, "agent_id": agent_id, "result": "WARN", "errors": [f"agent_id '{agent_id}' is probe/reg (sender={sender}) - allowed"]})
            else:
                report["failed"] += 1
                report["details"].append({"sender": sender, "agent_id": agent_id, "result": "FAIL", "errors": [f"agent_id '{agent_id}' unknown (sender={sender})"]})
    return report


def self_test_schemas(schema: dict) -> bool:
    """schema自测：用一个合规样本+一个不合规样本验证校验逻辑。"""
    good = {"agent_id": "test-agent", "task_id": "T-20260903-001", "phase": 3, "status": "success", "confidence": 85, "deliverable_summary": "test"}
    bad = {"agent_id": "Test_Agent", "task_id": "wrong", "phase": 99, "status": "unknown", "confidence": 200, "deliverable_summary": ""}
    errs_good = validate_envelope(good, schema)
    errs_bad = validate_envelope(bad, schema)
    if errs_good:
        print(f"  ❌ self-test: 合规样本被误判为不合规: {errs_good}")
        return False
    if not errs_bad:
        print(f"  ❌ self-test: 不合规样本被误判为合规")
        return False
    print(f"  ✅ self-test: 合规样本通过，不合规样本检出{len(errs_bad)}条错误")

    # ── S-E12 墙钟 WARN 双向断言（2026-11-09）────────────────────────────────────
    # 有 metrics 但缺 duration_ms_wall → 必须产出 WARN（预算熔断依据缺失），
    # 但不得升级为 FAIL（不改 schema required，避免破历史归档与回归基线）。
    m_wall = dict(good)
    m_wall["metrics"] = {"duration_ms": 1000}
    r1 = check_wall_clock(m_wall)
    if not r1:
        print("  ❌ self-test: metrics 缺 duration_ms_wall 未被检出 WARN")
        return False
    m_ok = dict(good)
    m_ok["metrics"] = {"duration_ms": 1000, "duration_ms_wall": 1200, "duration_source": "lead_measured"}
    if check_wall_clock(m_ok):
        print("  ❌ self-test: 完整墙钟信封被误报 WARN")
        return False
    m_bad = dict(good)
    m_bad["metrics"] = {"duration_ms": 1000, "duration_ms_wall": 1200, "duration_source": "bogus"}
    if not check_wall_clock(m_bad):
        print("  ❌ self-test: duration_source 非法值未被检出")
        return False
    print("  ✅ self-test: 墙钟 WARN 双向断言通过（缺墙钟→WARN / 完整→放行 / 非法口径→WARN）")
    return True


def resolve_results_dir(root: Path, explicit: str | None) -> Path:
    """解析 results 目录（CYCLE-1 · S-E09 失效引用修复）

    历史：默认写死 root/outputs，但 2026-11-08 基线资产化后回归产物已迁至
    tests/baselines/，outputs/ 不复存在 → pre-commit hook 的 agent_ci_gate --strict
    因「results目录不存在」直接 exit 1，阻断一切提交（实测 2026-11-09）。

    策略：显式指定 > baselines 优先 > outputs 兼容 > root（保证目录存在语义）。
    """
    if explicit:
        return Path(explicit)
    baselines = root / "tests" / "baselines"
    if baselines.is_dir():
        return baselines
    legacy = root / "outputs"
    if legacy.is_dir():
        return legacy
    return root


def main():
    ap = argparse.ArgumentParser(description="TRIZ专家团CI门禁：自动校验所有归档test结果的上行信封")
    ap.add_argument("root", nargs="?", default=str(SCRIPT_DIR.parent))
    ap.add_argument("--results-dir", default=None, help="results目录路径（默认 tests/baselines/，兼容 outputs/）")
    ap.add_argument("--strict", action="store_true", help="严格模式：有FAIL则exit 1")
    ap.add_argument("--self-test", action="store_true", help="只跑schema自测")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    results_dir = resolve_results_dir(root, args.results_dir)
    schema_path = SKILL_DIR / "result_envelope.schema.json"

    if not schema_path.exists():
        print(f"❌ schema文件不存在: {schema_path}")
        return 1

    schema = json.load(open(schema_path))
    print(f"📋 schema: {schema.get('title')} v{schema.get('version', '?')}")
    print(f"📂 results_dir: {results_dir}")

    if args.self_test:
        print("\n=== self-test ===")
        return 0 if self_test_schemas(schema) else 1

    if not results_dir.exists():
        print(f"❌ results目录不存在: {results_dir}")
        return 1

    results_files = sorted(glob.glob(str(results_dir / "*-results.json")))
    # CYCLE-1 第2轮交叉验证 · S-E22（幽灵门禁清偿）：此前本脚本只扫 *-results.json，
    # 而全仓该类文件实测为 **0** → 扫描恒为空、门禁恒返回 0、**从未真正校验过任何信封**
    # （S-E16「假绿」同型）。pre-commit hook 的 ① 信封门禁因此是空转。
    # 现补 fallback：results.json 为 0 时，改扫基线 markdown 中的成员产出信封
    # （T-*__<member>.md 形态，extract_envelopes 已支持从任意文本提取栈平衡 JSON）。
    scan_mode = "results-json"
    if not results_files:
        md_candidates = []
        # 排除已知**故意违规**的历史归档（负例基线，非合规产出）：
        #   _pre-fix-b01/ —— task_id 违约束格式的预修复归档（见该目录 NOTE.md）
        #   _archive/    —— spawn 提示词压缩包（非成员产出）
        for md in sorted(results_dir.rglob("T-*__*.md")):
            rel_parts = md.relative_to(results_dir).parts
            if any(p.startswith("_") for p in rel_parts[:-1]):
                continue  # 下划线前缀目录 = 预修复/归档区，不参与合规扫描
            try:
                txt = md.read_text(encoding="utf-8")
            except Exception:
                continue
            if "agent_id" in txt and "deliverable_summary" in txt:
                md_candidates.append(md)
        if md_candidates:
            scan_mode = "baseline-markdown(fallback)"
            results_files = md_candidates
            print(f"ℹ️  未发现 *-results.json（实测该形态文件数为 0）→ "
                  f"回退扫描基线 markdown 信封 {len(results_files)} 个")
    if not results_files:
        print(f"⚠️ 未发现 *-results.json 文件，且回退扫描也无含信封的基线 markdown")
        print(f"    （results_dir={results_dir}）——本门禁本轮**零覆盖**")
        return 0

    print(f"\n=== 校验 {len(results_files)} 个测试结果文件 ===")
    grand_total = grand_valid = grand_partial = grand_failed = grand_legacy = 0
    grand_warn = 0
    file_reports = []
    for rf in results_files:
        rp = process_results_file(Path(rf), schema)
        file_reports.append(rp)
        grand_total += rp["total"]
        grand_valid += rp["valid"]
        grand_partial += rp["partial"]
        grand_failed += rp["failed"]
        grand_legacy += rp["legacy"]
        file_warn = sum(1 for d in rp["details"] if d.get("warnings"))
        grand_warn += file_warn
        status_icon = "✅" if rp["failed"] == 0 and rp["partial"] == 0 else ("⚠️" if rp["valid"] > 0 else "❌")
        warn_suffix = f" warn={file_warn}" if file_warn else ""
        print(f"  {status_icon} {rp['file']}: total={rp['total']} valid={rp['valid']} partial={rp['partial']} failed={rp['failed']} legacy={rp['legacy']}{warn_suffix}")
        for d in rp["details"]:
            if d["result"] != "PASS" or d.get("warnings"):
                print(f"      {d}")

    # 合规率分母扣除legacy
    effective_total = grand_total - grand_legacy
    pass_rate = (grand_valid + grand_partial) / effective_total * 100 if effective_total else 0
    print(f"\n═══ 总计 ═══")
    print(f"  总信封: {grand_total}, 完整合规: {grand_valid}, partial: {grand_partial}, failed: {grand_failed}, legacy(扣除): {grand_legacy}")
    print(f"  合规率(扣除legacy后): {pass_rate:.1f}%")
    if grand_warn:
        print(f"  ⚠️ 墙钟 WARN: {grand_warn} 处（有 metrics 缺 duration_ms_wall / duration_source 非法）——不阻断，供主理人回填")

    # 写入报告
    # CYCLE-1 · S-E22：报告不写进 tests/baselines/（基线目录是只读基线真源，
    # 门禁产物属派生数据，写入会污染基线并触发 preflight README 结构校验漂移）。
    # 改为写入包根 outputs/ 派生目录。
    report_dir = root / "outputs"
    try:
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "ci_gate_report.json"
    except Exception:
        report_path = results_dir / "ci_gate_report.json"
    summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "schema_version": schema.get("version"),
        "scan_mode": scan_mode,
        "results_dir": str(results_dir),
        "grand_total": grand_total,
        "grand_valid": grand_valid,
        "grand_partial": grand_partial,
        "grand_failed": grand_failed,
        "grand_legacy": grand_legacy,
        "grand_wall_warn": grand_warn,
        "pass_rate": pass_rate,
        "files": file_reports,
    }
    with open(report_path, "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  报告: {report_path}")

    if args.strict and grand_failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())