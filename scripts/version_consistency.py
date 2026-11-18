#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
version_consistency.py — 版本号一致性门禁（新增，2026-11-11；第8轮扩为 5 位）

背景（真实缺陷，非推测）：
  2026-11-11 实测发现 `.codebuddy-plugin/marketplace.json` 的 version 停在
  2.10.0，而 `.codebuddy-plugin/plugin.json` 已是 2.11.2、`.claude-plugin/
  marketplace.json` 已是 2.11.2 —— **三处版本漂移，且已连续漂移两轮**。
  根因：既有 bump 提交（1b41fe1 等）只改了 `.claude-plugin/marketplace.json`
  两处 + `plugin.json` 一处，漏了 `.codebuddy-plugin/marketplace.json`；
  而 preflight / self_gate **均无任何版本一致性判据**，漏改不会被拦下。

  本脚本把「版本必须一致」变成可机械复验的门禁，杜绝同类漂移复发。

  第8轮实测扩展（v2.13.0 bump 时再次暴露）：
    `.claude-plugin/marketplace.json` 的 `metadata.description` 里
    **硬编码了「(v2.11.2)」字样** —— 4 个 version 字段全对，
    但描述文字里的版本号落后两个版本。门禁只查 version 字段 → 漏过。
    说明「版本号」不止存在于 version 字段，还内嵌在描述文字里。
    现增加第 5 个检查位：**描述文字内嵌版本号**，一并纳入一致性判定。

检查对象（5 个版本位，全部必须相等）：
  1. .codebuddy-plugin/plugin.json          → .version
  2. .codebuddy-plugin/marketplace.json     → .plugins[0].version
  3. .claude-plugin/marketplace.json        → .metadata.version
  4. .claude-plugin/marketplace.json        → .plugins[0].version
  5. .claude-plugin/marketplace.json        → .metadata.description 内嵌 (vX.Y.Z)

  C11 补修轮（2026-11-15）实测护栏可静默绕过：
    描述位是「正则命中才追加」，若把 description 里的 (vX.Y.Z) **直接删掉**，
    collect_versions() 只返回 4 个固定位，distinct 仍只有 1 个、missing=0，
    main() 会输出「4 个版本位一致」且 RC=0 —— 第 5 位护栏形同虚设
    （原判据只查 distinct==1 && missing==0，不校验检查位数量下限）。
    现补「检查位数量下限」：4 个固定 version 字段位之外，描述内嵌版本号位
    必须至少命中 1 处；位数是动态 4+N（其它清单描述也可能内嵌版本号），
    故用 ≥ 而非 ==：正常 5 位、合法扩展 6 位均通过，删成 4 位即 fail loud 非零。

退出码：0=一致 · 1=不一致 / 缺检查位（有明确失败） · 2=用法/环境错（文件缺失或不可读）
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

# 描述文字里内嵌版本号的匹配形态：(v2.13.0) / v2.13.0 / for CN invention patents v2.13
_DESC_VER_RE = re.compile(r"\bv(\d+\.\d+\.\d+)\b")

# 固定 version 字段位（collect_versions 的真源表；提升为模块级只为了让位数下限
# 由表长派生，取值顺序与内容逐字未变）。文件缺失时仍会追加一条带 error 的记录，
# 故 collect_versions() 的返回恒为「len(FIXED_SITES) + 描述位命中数」。
FIXED_SITES = [
    ("WorkBuddy 插件清单", ".codebuddy-plugin/plugin.json", ("version",)),
    ("WorkBuddy 市场清单·插件项", ".codebuddy-plugin/marketplace.json",
     ("plugins", 0, "version")),
    ("Claude 市场清单·metadata", ".claude-plugin/marketplace.json",
     ("metadata", "version")),
    ("Claude 市场清单·插件项", ".claude-plugin/marketplace.json",
     ("plugins", 0, "version")),
]

# 描述内嵌版本号位至少命中 1 处（堵「直接删掉版本号 → 退回 4 位且门禁全绿」）。
# 用 ≥ 而非固定 ==5：描述位是动态 4+N，塞第 2 个描述位得 6 位仍属合法。
MIN_DESC_SITES = 1
# 检查位数量下限（单一真源）：数字由结构派生，不在 self_gate.py 等处重复硬编码。
MIN_VERSION_SITES = len(FIXED_SITES) + MIN_DESC_SITES


def _read_json(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def _extract_desc_versions(root):
    """扫描所有清单 JSON 的 description 字段，返回 [(标签, 相对路径, 版本值)]。

    描述文字里出现的**所有**版本号都必须与 version 字段一致。
    只取**最后一个**出现：描述通常写作「... v2.13: 特性说明」，
    前面若有历史版本引用（如「自 v2.11 引入」）不应误判。
    """
    root = root or PKG
    targets = [
        ("WorkBuddy 插件清单·描述", ".codebuddy-plugin/plugin.json",
         lambda d: d.get("description")),
        ("WorkBuddy 市场清单·描述", ".codebuddy-plugin/marketplace.json",
         lambda d: d.get("plugins", [{}])[0].get("description")),
        ("Claude 市场清单·描述", ".claude-plugin/marketplace.json",
         lambda d: d.get("metadata", {}).get("description")),
    ]
    out = []
    for label, rel, getter in targets:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            continue
        try:
            data = _read_json(full)
        except Exception:  # noqa: BLE001 —— 已在 version 位检查里报过
            continue
        desc = getter(data) or ""
        hits = _DESC_VER_RE.findall(desc)
        if hits:
            out.append((label, rel, hits[-1]))
    return out


def collect_versions(root=None):
    """返回 [(位名, 文件相对路径, 版本值或 None, 错误信息或 None)]。"""
    root = root or PKG
    out = []
    for label, rel, path in FIXED_SITES:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            out.append((label, rel, None, "文件不存在"))
            continue
        try:
            data = _read_json(full)
        except Exception as exc:  # noqa: BLE001 —— 门禁必须 fail loud
            out.append((label, rel, None, "解析失败：%s" % exc))
            continue
        cur = data
        try:
            for key in path:
                cur = cur[key]
        except (KeyError, IndexError, TypeError):
            out.append((label, rel, None, "缺少字段 %s" % ".".join(map(str, path))))
            continue
        out.append((label, rel, str(cur), None))
    # 第 5 位起：描述文字内嵌版本号
    for label, rel, ver in _extract_desc_versions(root):
        out.append((label, rel, ver, None))
    return out


def check(root=None):
    """返回 (sites, distinct, n_missing)，签名保持三元组不变（外部复现脚本依赖）。

    n_missing 除「不可读的固定位」外，还计入「缺检查位」：描述内嵌版本号位
    一个都没命中时，仅凭 distinct==1 && missing==0 会假绿（护栏被静默绕过）。
    位数判据用 ≥（描述位动态 4+N），不把合法的 6 位扩展误判红。
    """
    sites = collect_versions(root)
    n_desc = len(sites) - len(FIXED_SITES)
    missing = [s for s in sites if s[3]]
    values = [s[2] for s in sites if s[2] is not None]
    distinct = sorted(set(values))
    too_few = n_desc < MIN_DESC_SITES
    return sites, distinct, len(missing) + (1 if too_few else 0)


def main():
    ap = argparse.ArgumentParser(description="版本号一致性门禁（5 个版本位必须相等）")
    ap.add_argument("--root", default="", help="包根目录（默认脚本所在包）")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--self-test", action="store_true",
                    help="判别力自测：故意制造漂移必须被识别")
    args = ap.parse_args()
    root = args.root or PKG

    if args.self_test:
        return self_test(root)

    sites, distinct, n_missing = check(root)
    # 描述内嵌版本号位命中数（固定位恒为 len(FIXED_SITES) 条，缺失也占位）。
    n_desc = len(sites) - len(FIXED_SITES)
    if args.json:
        print(json.dumps({
            "sites": [{"label": s[0], "file": s[1], "version": s[2], "error": s[3]}
                      for s in sites],
            "distinct": distinct, "missing": n_missing,
            "consistent": len(distinct) == 1 and n_missing == 0
                          and n_desc >= MIN_DESC_SITES,
        }, ensure_ascii=False, indent=2))
    else:
        print("🔢 版本一致性 — %s" % os.path.basename(root))
        for label, rel, ver, err in sites:
            if err:
                print("  ❌ %-26s %-34s %s" % (label, rel, err))
            else:
                print("  ✅ %-26s %-34s %s" % (label, rel, ver))
        if n_desc < MIN_DESC_SITES:
            print("  ❌ %-26s %-34s %s"
                  % ("描述内嵌版本号位·缺检查位", "(0 命中)",
                     "缺检查位：期望至少 %d 处命中" % MIN_DESC_SITES))
        # 缺检查位优先于不可读判据：这里必须明确报「缺检查位」，不能静默退回 4 位。
        if n_desc < MIN_DESC_SITES:
            print("\n❌ 缺检查位：仅检测到 %d 个版本位（期望 ≥%d = %d 个固定 version 字段位"
                  " + ≥%d 个描述内嵌版本号位）——禁止发布（fail loud）"
                  % (len(sites), MIN_VERSION_SITES, len(FIXED_SITES), MIN_DESC_SITES))
            print("   修复：不能删掉 description 内嵌的 (vX.Y.Z) 版本号；"
                  "bump 时须同步更新全部版本位")
            return 1
        if n_missing:
            print("\n❌ %d 个版本位不可读——禁止发布（fail loud）" % n_missing)
            return 1
        if len(distinct) != 1:
            print("\n❌ 版本漂移：%d 个不同版本 %s——禁止发布"
                  % (len(distinct), distinct))
            print("   修复：bump 时必须同时更新上述全部 %d 个版本位" % len(sites))
            print("   注意：description 内嵌的 (vX.Y.Z) 字样也算一个版本位")
            return 1
        print("\n结论：%d 个版本位一致（%s）" % (len(sites), distinct[0]))
    if n_missing:
        return 1
    return 0 if len(distinct) == 1 else 1


def self_test(root=None):
    """判别力自测：改坏任一版本位，本测试必须报错。"""
    import shutil
    import tempfile
    fails = []
    print("🧪 版本一致性判别力自测\n")
    with tempfile.TemporaryDirectory() as td:
        # 复制最小必要结构
        for rel in (".codebuddy-plugin/plugin.json",
                    ".codebuddy-plugin/marketplace.json",
                    ".claude-plugin/marketplace.json"):
            src = os.path.join(root, rel)
            dst = os.path.join(td, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)

        # 基线：当前仓库本身应该一致（若不一致，先修好再谈门禁）
        sites, distinct, n_missing = check(td)
        ok0 = (n_missing == 0 and len(distinct) == 1)
        print("  %s 基线各版本位一致 | 实得 distinct=%s missing=%d（%d 位）"
              % ("✅" if ok0 else "❌", distinct, n_missing, len(sites)))
        if not ok0:
            fails.append("基线不一致")

        # 变异4（2026-11-11 v2.13.0 bump 实测暴露）：描述文字内嵌版本号落后
        #   → 必须检出。这是**真实漏改**：4 个 version 字段全对，
        #   但 metadata.description 里仍写着 (v2.11.2)。
        cp = os.path.join(td, ".claude-plugin/marketplace.json")
        data_c = _read_json(cp)
        orig_desc = data_c["metadata"]["description"]
        data_c["metadata"]["description"] = orig_desc.replace(
            "v%s" % distinct[0], "v2.11.2")
        _write_json(cp, data_c)
        sites, distinct2, n_missing2 = check(td)
        ok4 = (len(distinct2) > 1)
        print("  %s 描述内嵌版本号落后 → 检出漂移 | 实得 distinct=%s"
              % ("✅" if ok4 else "❌", distinct2))
        if not ok4:
            fails.append("描述内嵌版本号漂移未检出")
        shutil.copyfile(os.path.join(root, ".claude-plugin/marketplace.json"), cp)

        # 变异5（C11 补修轮新增，2026-11-15）：**直接删掉**描述内嵌版本号。
        #   修复前：描述位 0 命中 → 门禁退回 4 位、distinct==1、missing==0
        #   → 输出「4 个版本位一致」且 RC=0（S-E78 护栏被静默绕过）。
        #   修复后：check() 必须报「缺检查位」（missing>0 且位数低于下限）。
        data_c = _read_json(cp)
        desc_backup = data_c["metadata"]["description"]
        data_c["metadata"]["description"] = re.sub(
            _DESC_VER_RE, "无版本号", desc_backup)
        _write_json(cp, data_c)
        sites5, distinct5, n_missing5 = check(td)
        ok5 = (n_missing5 > 0 and len(sites5) < MIN_VERSION_SITES)
        print("  %s 删描述内嵌版本号 → 报缺检查位 | 实得 %d 位 distinct=%s missing=%d（下限 %d）"
              % ("✅" if ok5 else "❌", len(sites5), distinct5, n_missing5,
                 MIN_VERSION_SITES))
        if not ok5:
            fails.append("删描述内嵌版本号未报缺检查位")
        # 还原 → 必须恢复 PASS（含位数达标），证明判据不是一律判红
        data_c["metadata"]["description"] = desc_backup
        _write_json(cp, data_c)
        sites5r, distinct5r, n_missing5r = check(td)
        ok5r = (n_missing5r == 0 and len(distinct5r) == 1
                and len(sites5r) - len(FIXED_SITES) >= MIN_DESC_SITES)
        print("  %s 还原描述内嵌版本号 → 恢复 PASS | 实得 %d 位 distinct=%s missing=%d"
              % ("✅" if ok5r else "❌", len(sites5r), distinct5r, n_missing5r))
        if not ok5r:
            fails.append("还原描述内嵌版本号未恢复 PASS")

        # 变异1：把其中一处改小 → 必须判为漂移
        p = os.path.join(td, ".codebuddy-plugin/marketplace.json")
        data = _read_json(p)
        data["plugins"][0]["version"] = "0.0.1"
        _write_json(p, data)
        sites, distinct, n_missing = check(td)
        ok1 = (len(distinct) > 1)
        print("  %s 单点改小 → 检出漂移 | 实得 distinct=%s"
              % ("✅" if ok1 else "❌", distinct))
        if not ok1:
            fails.append("单点漂移未检出")
        shutil.copyfile(os.path.join(root, ".codebuddy-plugin/marketplace.json"), p)

        # 变异2：删掉一个版本字段 → 必须报「缺少字段」
        data = _read_json(p)
        del data["plugins"][0]["version"]
        _write_json(p, data)
        sites, distinct, n_missing = check(td)
        ok2 = (n_missing > 0)
        print("  %s 缺版本字段 → 报缺字段 | 实得 missing=%d"
              % ("✅" if ok2 else "❌", n_missing))
        if not ok2:
            fails.append("缺字段未检出")

        # 变异3：文件缺失 → 必须报「文件不存在」
        os.remove(p)
        sites, distinct, n_missing = check(td)
        ok3 = (n_missing > 0)
        print("  %s 文件缺失 → 报缺失 | 实得 missing=%d"
              % ("✅" if ok3 else "❌", n_missing))
        if not ok3:
            fails.append("文件缺失未检出")

    if fails:
        print("\n❌ 自测失败：%s" % fails)
        return 1
    print("\n✅ 自测全通过")
    return 0


def _write_json(path, data):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
