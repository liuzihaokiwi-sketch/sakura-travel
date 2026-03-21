#!/usr/bin/env python3
"""
🔄 智能 Git Commit 脚本
========================

自动分析 git diff，按模块分组，生成规范的 commit message 并提交。

用法:
  python scripts/smart_commit.py              # 交互模式，逐组确认
  python scripts/smart_commit.py --auto       # 全自动提交
  python scripts/smart_commit.py --dry-run    # 只预览，不提交
  python scripts/smart_commit.py --push       # 提交后自动 push
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ── 模块分组规则 ─────────────────────────────────────────────────────────────

MODULE_RULES: list[tuple[str, str, str]] = [
    # (glob/prefix, 模块名, commit type)
    ("app/api/",               "api",        "feat"),
    ("app/core/",              "core",       "feat"),
    ("app/db/",                "db",         "feat"),
    ("app/domains/",           "domain",     "feat"),
    ("web/app/",               "web-page",   "feat"),
    ("web/components/",        "web-ui",     "feat"),
    ("web/lib/",               "web-lib",    "feat"),
    ("web/scripts/",           "web-script", "feat"),
    ("web/",                   "web",        "feat"),
    ("scripts/crawlers/",      "crawler",    "feat"),
    ("scripts/",               "scripts",    "feat"),
    ("openspec/",              "openspec",   "chore"),
    ("tests/",                 "test",       "test"),
    ("docs/",                  "docs",       "docs"),
    (".github/",               "ci",         "ci"),
    ("docker",                 "infra",      "chore"),
    ("pyproject.toml",         "deps",       "chore"),
    ("package.json",           "deps",       "chore"),
    (".env",                   "config",     "chore"),
    (".gitignore",             "config",     "chore"),
    ("hooks/",                 "config",     "chore"),
    ("alembic",                "db",         "feat"),
    ("data/",                  "data",       "chore"),
]


def classify_file(path: str) -> tuple[str, str]:
    """返回 (模块名, commit_type)"""
    for prefix, module, ctype in MODULE_RULES:
        if path.startswith(prefix) or path == prefix:
            return module, ctype
    return "misc", "chore"


# ── Git 操作 ─────────────────────────────────────────────────────────────────

def run_git(*args: str, check: bool = True) -> str:
    """执行 git 命令"""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True, text=True, encoding="utf-8",
        cwd=Path(__file__).resolve().parent.parent,
    )
    if check and result.returncode != 0:
        print(f"❌ git {' '.join(args)} 失败:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def get_changed_files() -> list[tuple[str, str]]:
    """获取所有改动文件: [(status, path), ...]"""
    # 已暂存
    staged = run_git("diff", "--cached", "--name-status")
    # 未暂存
    unstaged = run_git("diff", "--name-status")
    # 未跟踪
    untracked = run_git("ls-files", "--others", "--exclude-standard")

    files: list[tuple[str, str]] = []
    seen = set()

    for line in (staged + "\n" + unstaged).strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            status, path = parts
            if path not in seen:
                files.append((status[0], path))
                seen.add(path)

    for line in untracked.strip().split("\n"):
        if line.strip() and line not in seen:
            files.append(("?", line))
            seen.add(line)

    return files


@dataclass
class CommitGroup:
    """一组要提交的文件"""
    module: str
    commit_type: str
    files: list[tuple[str, str]] = field(default_factory=list)  # [(status, path)]

    @property
    def summary(self) -> str:
        """自动生成 commit message"""
        actions = []
        added = [p for s, p in self.files if s in ("A", "?")]
        modified = [p for s, p in self.files if s == "M"]
        deleted = [p for s, p in self.files if s == "D"]
        renamed = [p for s, p in self.files if s == "R"]

        if added:
            names = [Path(p).stem for p in added[:3]]
            suffix = f" 等{len(added)}个" if len(added) > 3 else ""
            actions.append(f"新增 {', '.join(names)}{suffix}")
        if modified:
            names = [Path(p).stem for p in modified[:3]]
            suffix = f" 等{len(modified)}个" if len(modified) > 3 else ""
            actions.append(f"更新 {', '.join(names)}{suffix}")
        if deleted:
            actions.append(f"删除 {len(deleted)} 个文件")
        if renamed:
            actions.append(f"重命名 {len(renamed)} 个文件")

        return "; ".join(actions) if actions else "更新"

    @property
    def commit_message(self) -> str:
        return f"{self.commit_type}({self.module}): {self.summary}"

    @property
    def file_list_str(self) -> str:
        lines = []
        icons = {"A": "➕", "M": "✏️", "D": "🗑️", "?": "🆕", "R": "🔄"}
        for status, path in sorted(self.files, key=lambda x: x[1]):
            icon = icons.get(status, "❓")
            lines.append(f"  {icon} {path}")
        return "\n".join(lines)


def group_files(files: list[tuple[str, str]]) -> list[CommitGroup]:
    """按模块分组"""
    groups: dict[str, CommitGroup] = {}

    for status, path in files:
        module, ctype = classify_file(path)
        if module not in groups:
            groups[module] = CommitGroup(module=module, commit_type=ctype)
        groups[module].files.append((status, path))

    # 按优先级排序: feat > fix > test > docs > chore
    type_order = {"feat": 0, "fix": 1, "test": 2, "docs": 3, "ci": 4, "chore": 5}
    return sorted(groups.values(), key=lambda g: (type_order.get(g.commit_type, 9), g.module))


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="智能 Git Commit")
    parser.add_argument("--auto", action="store_true", help="全自动提交，不确认")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不提交")
    parser.add_argument("--push", action="store_true", help="提交后自动 push")
    parser.add_argument("--single", action="store_true", help="所有改动合成一个 commit")
    args = parser.parse_args()

    # 1. 获取改动
    files = get_changed_files()
    if not files:
        print("✅ 没有需要提交的改动")
        return

    print(f"\n📋 检测到 {len(files)} 个文件改动\n")

    # 2. 分组
    if args.single:
        # 单次提交模式
        group = CommitGroup(module="all", commit_type="feat")
        group.files = files
        groups = [group]
    else:
        groups = group_files(files)

    # 3. 预览
    print(f"📦 将分成 {len(groups)} 个 commit:\n")
    print("=" * 60)
    for i, g in enumerate(groups, 1):
        print(f"\n{'─'*60}")
        print(f"  📌 Commit {i}/{len(groups)}")
        print(f"  💬 {g.commit_message}")
        print(f"  📁 {len(g.files)} 个文件:")
        print(g.file_list_str)
    print(f"\n{'='*60}\n")

    if args.dry_run:
        print("🔍 Dry run 模式，不执行提交")
        return

    # 4. 提交
    for i, g in enumerate(groups, 1):
        if not args.auto:
            answer = input(f"\n🔸 Commit {i}/{len(groups)}: {g.commit_message}\n   确认? [Y/n/e(编辑)/s(跳过)] ").strip().lower()
            if answer == "s":
                print("   ⏭️  跳过")
                continue
            if answer == "e":
                msg = input("   输入新的 commit message: ").strip()
                if not msg:
                    msg = g.commit_message
            elif answer in ("", "y", "yes"):
                msg = g.commit_message
            else:
                print("   ⏭️  跳过")
                continue
        else:
            msg = g.commit_message

        # git add
        paths = [p for _, p in g.files]
        for path in paths:
            run_git("add", path, check=False)

        # git commit
        result = subprocess.run(
            ["git", "commit", "--no-verify", "-m", msg],
            capture_output=True, text=True, encoding="utf-8",
            cwd=Path(__file__).resolve().parent.parent,
        )
        if result.returncode == 0:
            # 提取 commit hash
            match = re.search(r"\[[\w-]+ ([a-f0-9]+)\]", result.stdout)
            short_hash = match.group(1) if match else "?"
            print(f"   ✅ [{short_hash}] {msg}")
        else:
            print(f"   ❌ 提交失败: {result.stderr[:100]}")

    # 5. Push
    if args.push:
        print("\n🚀 Pushing to remote...")
        result = subprocess.run(
            ["git", "push"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=Path(__file__).resolve().parent.parent,
        )
        if result.returncode == 0:
            print("   ✅ Push 成功")
        else:
            print(f"   ❌ Push 失败: {result.stderr[:200]}")

    # 6. 完成
    print(f"\n{'='*60}")
    log = run_git("log", "--oneline", "-5")
    print(f"📜 最近 5 条 commit:\n{log}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
