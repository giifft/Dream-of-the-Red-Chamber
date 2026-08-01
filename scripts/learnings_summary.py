#!/usr/bin/env python3
"""
自进化学习库自动摘要脚本

从 git log 中提取 fix:/feat:/refactor: 等模式的 commit，
自动生成 successful_patterns.md 和 bad_cases.md 条目草稿。

Usage:
    python scripts/learnings_summary.py                    # 分析最近 30 天
    python scripts/learnings_summary.py --days 90          # 分析最近 90 天
    python scripts/learnings_summary.py --since 2026-01-01 # 从指定日期
    python scripts/learnings_summary.py --dry-run          # 仅预览，不写入
"""

import subprocess
import sys
import os
import re
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional


def run_git_log(since: str) -> List[Dict[str, str]]:
    """获取指定日期以来的 git log"""
    cmd = [
        "git", "log",
        f"--since={since}",
        "--pretty=format:%h|%s|%an|%ad",
        "--date=short",
        "--no-merges"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3]
                })
        return commits
    except subprocess.CalledProcessError as e:
        print(f"⚠️  git log 获取失败: {e}", file=sys.stderr)
        return []


def classify_commit(message: str) -> Optional[str]:
    """分类 commit 消息"""
    msg_lower = message.lower()

    success_patterns = [
        r"^feat[\(:]", r"^add[:\s]", r"^implement[:\s]",
        r"^refactor[\(:]", r"^optimize[:\s]", r"^perf[\(:]",
        r"^style[\(:]", r"^chore[\(:]", r"^docs[\(:]",
        r"新增", r"添加", r"实现", r"优化", r"重构"
    ]
    for pat in success_patterns:
        if re.search(pat, msg_lower):
            return "success"

    failure_patterns = [
        r"^fix[\(:]", r"^bug[:\s]", r"^revert[:\s]",
        r"^hotfix[\(:]", r"^rollback[:\s]", r"修复", r"bug", r"回滚"
    ]
    for pat in failure_patterns:
        if re.search(pat, msg_lower):
            return "failure"

    return None


def extract_learnings(commits: List[Dict]) -> tuple:
    """从 commits 提取学习条目"""
    successes = []
    failures = []

    for c in commits:
        category = classify_commit(c["message"])
        if category == "success":
            successes.append(c)
        elif category == "failure":
            failures.append(c)

    return successes, failures


def generate_sp_entry(commit: Dict, index: int) -> str:
    """生成成功模式条目"""
    return f"""### SP-{index:03d}: {commit['message'][:60]}
- **日期**: {commit['date']}
- **提交**: `{commit['hash']}`
- **作者**: {commit['author']}
- **模式**: [待补充具体成功模式描述]
- **复用条件**: [待补充何时可复用]
"""


def generate_bc_entry(commit: Dict, index: int) -> str:
    """生成踩坑条目"""
    return f"""### BC-{index:03d}: {commit['message'][:60]}
- **日期**: {commit['date']}
- **提交**: `{commit['hash']}`
- **作者**: {commit['author']}
- **根因**: [待补充根因分析]
- **防退化检查**: [待补充如何防止复发]
"""


def get_next_number(filepath: str, prefix: str) -> int:
    """获取下一个编号"""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        matches = re.findall(rf"{prefix}-(\d{{3}})", content)
        if matches:
            return max(int(m) for m in matches) + 1
    except FileNotFoundError:
        pass
    return 1


def get_project_root() -> str:
    """获取项目根目录"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def main():
    parser = argparse.ArgumentParser(description="自进化学习库自动摘要")
    parser.add_argument("--days", type=int, default=30, help="分析最近 N 天 (默认 30)")
    parser.add_argument("--since", type=str, help="从指定日期开始 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入文件")
    args = parser.parse_args()

    if args.since:
        since = args.since
    else:
        since = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    print(f"🔍 分析 {since} 以来的 commit 记录...")

    root = get_project_root()
    os.chdir(root)

    commits = run_git_log(since)
    if not commits:
        print("📭 没有找到符合条件的 commit")
        return

    successes, failures = extract_learnings(commits)
    print(f"📊 共 {len(commits)} 个 commit，成功 {len(successes)} 条，踩坑 {len(failures)} 条")

    sp_path = os.path.join(root, "learnings", "successful_patterns.md")
    bc_path = os.path.join(root, "learnings", "bad_cases.md")

    if successes:
        sp_start = get_next_number(sp_path, "SP")
        sp_entries = [generate_sp_entry(c, sp_start + i) for i, c in enumerate(successes)]
        sp_text = "\n".join(sp_entries)

        if args.dry_run:
            print(f"\n📝 预览 successful_patterns.md (SP-{sp_start:03d} 起):\n")
            print(sp_text)
        else:
            with open(sp_path, "a") as f:
                f.write("\n" + sp_text)
            print(f"✅ 已追加 {len(successes)} 条到 {sp_path}")

    if failures:
        bc_start = get_next_number(bc_path, "BC")
        bc_entries = [generate_bc_entry(c, bc_start + i) for i, c in enumerate(failures)]
        bc_text = "\n".join(bc_entries)

        if args.dry_run:
            print(f"\n📝 预览 bad_cases.md (BC-{bc_start:03d} 起):\n")
            print(bc_text)
        else:
            with open(bc_path, "a") as f:
                f.write("\n" + bc_text)
            print(f"✅ 已追加 {len(failures)} 条到 {bc_path}")

    if not successes and not failures:
        print("📭 没有发现可分类的 commit 模式")

    if args.dry_run:
        print("\n💡 以上为预览，去掉 --dry-run 以实际写入")


if __name__ == "__main__":
    main()
