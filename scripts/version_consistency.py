#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
version_consistency.py — 版本号三处一致性门禁（新增，2026-11-11）

背景（真实缺陷，非推测）：
  2026-11-11 实测发现 `.codebuddy-plugin/marketplace.json` 的 version 停在
  2.10.0，而 `.codebuddy-plugin/plugin.json` 已是 2.11.2、`.claude-plugin/
  marketplace.json` 已是 2.11.2 —— **三处版本漂移，且已连续漂移两轮**。
  根因：既有 bump 提交（1b41fe1 等）只改了 `.claude-plugin/marketplace.json`
  两处 + `plugin.json` 一处，漏了 `.codebuddy-plugin/marketplace.json`；
  而 preflight / self_gate **均无任何版本一致性判据**，漏改不会被拦下。

  本脚本把「版本必须一致」变成可机械复验的门禁，杜绝同类漂移复发。

检查对象（4 个版本位，全部必须相等）：
  1. .codebuddy-plugin/plugin.json          → .version
  2. .codebuddy-plugin/marketplace.json     → .plugins[0].version
  3. .claude-plugin/marketplace.json        → .version
  4. .claude-plugin/marketplace.json        → .plugins[0].version

退出码：0=一致 · 1=不一致（有明确失败） · 2=用法/环境错（文件缺失或不可读）
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)


def _read_json(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_versions(root=None):
    """返回 [(位名, 文件相对路径, 版本值或 None, 错误信息或 None)]。"""
    root = root or PKG
    sites = [
        ("WorkBuddy 插件清单", ".codebuddy-plugin/plugin.json", ("version",)),
        ("WorkBuddy 市场清单·插件项", ".codebuddy-plugin/marketplace.json",
         ("plugins", 0, "version")),
        ("Claude 市场清单·metadata", ".claude-plugin/marketplace.json",
         ("metadata", "version")),
        ("Claude 市场清单·插件项", ".claude-plugin/marketplace.json",
         ("plugins", 0, "version")),
    ]
    out = []
    for label, rel, path in sites:
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
    return out


def check(root=None):
    sites = collect_versions(root)
    missing = [s for s in sites if s[3]]
    values = [s[2] for s in sites if s[2] is not None]
    distinct = sorted(set(values))
    return sites, distinct, len(missing)


def main():
    ap = argparse.ArgumentParser(description="版本号一致性门禁（三处版本必须相等）")
    ap.add_argument("--root", default="", help="包根目录（默认脚本所在包）")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--self-test", action="store_true",
                    help="判别力自测：故意制造漂移必须被识别")
    args = ap.parse_args()
    root = args.root or PKG

    if args.self_test:
        return self_test(root)

    sites, distinct, n_missing = check(root)
    if args.json:
        print(json.dumps({
            "sites": [{"label": s[0], "file": s[1], "version": s[2], "error": s[3]}
                      for s in sites],
            "distinct": distinct, "missing": n_missing,
            "consistent": len(distinct) == 1 and n_missing == 0,
        }, ensure_ascii=False, indent=2))
    else:
        print("🔢 版本一致性 — %s" % os.path.basename(root))
        for label, rel, ver, err in sites:
            if err:
                print("  ❌ %-24s %-34s %s" % (label, rel, err))
            else:
                print("  ✅ %-24s %-34s %s" % (label, rel, ver))
        if n_missing:
            print("\n❌ %d 个版本位不可读——禁止发布（fail loud）" % n_missing)
            return 1
        if len(distinct) != 1:
            print("\n❌ 版本漂移：%d 个不同版本 %s——禁止发布"
                  % (len(distinct), distinct))
            print("   修复：bump 时必须同时更新上述全部 %d 个版本位" % len(sites))
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
        print("  %s 基线四版本位一致 | 实得 distinct=%s missing=%d"
              % ("✅" if ok0 else "❌", distinct, n_missing))
        if not ok0:
            fails.append("基线不一致")

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
