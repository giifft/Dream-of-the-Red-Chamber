#!/usr/bin/env python3
"""
SOP 阶段检查脚本

检查当前项目是否满足进入下一阶段的前置条件。
用于在 SOP 各阶段切换时进行自动化门禁检查。

Usage:
    python scripts/check_sop_phase.py --phase <phase>          # 检查指定阶段前置条件
    python scripts/check_sop_phase.py --list                   # 列出所有阶段及当前状态
    python scripts/check_sop_phase.py --next                   # 检查下一阶段是否就绪

阶段定义:
    phase1 - 需求分析（林黛玉）
    phase2 - UI/UX 设计（惜春）
    phase3 - AI 设计（妙玉）
    phase4 - ML 建模（香菱）
    phase5 - 架构设计（贾宝玉）
    phase6 - 编码实现（薛宝钗）
    phase7 - 测试验证（紫鹃）
    phase8 - 部署（探春）
    phase9 - 交付总结（王熙凤）
"""

import os
import sys
import argparse
from typing import Dict, List, Optional, Tuple


PHASES = {
    "phase1": {"name": "需求分析", "role": "林黛玉", "order": 1},
    "phase2": {"name": "UI/UX 设计", "role": "惜春", "order": 2, "optional": True},
    "phase3": {"name": "AI 设计", "role": "妙玉", "order": 3, "optional": True},
    "phase4": {"name": "ML 建模", "role": "香菱", "order": 4, "optional": True},
    "phase5": {"name": "架构设计", "role": "贾宝玉", "order": 5},
    "phase6": {"name": "编码实现", "role": "薛宝钗", "order": 6},
    "phase7": {"name": "测试验证", "role": "紫鹃", "order": 7},
    "phase8": {"name": "部署", "role": "探春", "order": 8, "optional": True},
    "phase9": {"name": "交付总结", "role": "王熙凤", "order": 9},
}


def get_project_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def check_prd_exists(root: str) -> bool:
    """检查是否存在 PRD 文档"""
    prd_indicators = ["prd", "PRD", "需求文档", "需求分析", "产品需求"]
    for f in os.listdir(root):
        if any(ind in f for ind in prd_indicators) and f.endswith((".md", ".txt", ".docx")):
            return True
    # 也检查 docs/ 目录
    docs_dir = os.path.join(root, "docs")
    if os.path.isdir(docs_dir):
        for f in os.listdir(docs_dir):
            if any(ind in f for ind in prd_indicators) and f.endswith((".md", ".txt")):
                return True
    return False


def check_architecture_exists(root: str) -> bool:
    """检查是否存在架构设计文档"""
    arch_indicators = ["架构", "architecture", "ARCH", "design", "设计文档"]
    for f in os.listdir(root):
        if any(ind in f.lower() for ind in arch_indicators) and f.endswith((".md", ".txt")):
            return True
    docs_dir = os.path.join(root, "docs")
    if os.path.isdir(docs_dir):
        for f in os.listdir(docs_dir):
            if any(ind in f.lower() for ind in arch_indicators) and f.endswith((".md", ".txt")):
                return True
    return False


def check_code_exists(root: str) -> bool:
    """检查是否存在代码文件"""
    code_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".html", ".css", ".vue", ".svelte"}
    src_dirs = ["src", "app", "lib", "components", "pages", "api", "services", "utils"]
    for d in src_dirs:
        p = os.path.join(root, d)
        if os.path.isdir(p):
            for _, _, files in os.walk(p):
                for f in files:
                    if os.path.splitext(f)[1] in code_exts:
                        return True
                break
    # 根目录直接检查
    for f in os.listdir(root):
        if os.path.splitext(f)[1] in code_exts:
            return True
    return False


def check_tests_exist(root: str) -> bool:
    """检查是否存在测试文件"""
    test_dirs = ["tests", "test", "__tests__", "spec"]
    test_prefixes = ["test_", "_test"]
    for d in test_dirs:
        p = os.path.join(root, d)
        if os.path.isdir(p):
            return True
    for f in os.listdir(root):
        if any(f.startswith(p) for p in test_prefixes) and f.endswith(".py"):
            return True
        if f.endswith((".test.js", ".test.ts", ".spec.js", ".spec.ts")):
            return True
    return False


def check_learnings_updated(root: str) -> bool:
    """检查 learnings 是否在本次会话中更新过"""
    learnings_dir = os.path.join(root, "learnings")
    if not os.path.isdir(learnings_dir):
        return False
    # 检查三个核心文件是否存在
    required = ["successful_patterns.md", "bad_cases.md", "evolution_log.md"]
    return all(os.path.exists(os.path.join(learnings_dir, f)) for f in required)


def get_phase_status(root: str) -> Dict[str, str]:
    """获取所有阶段当前状态"""
    status = {}

    status["phase1"] = "✅" if check_prd_exists(root) else "⬜"
    status["phase2"] = "⬜  (可选)"
    status["phase3"] = "⬜  (可选)"
    status["phase4"] = "⬜  (可选)"
    status["phase5"] = "✅" if check_architecture_exists(root) else "⬜"
    status["phase6"] = "✅" if check_code_exists(root) else "⬜"
    status["phase7"] = "✅" if check_tests_exist(root) else "⬜"
    status["phase8"] = "⬜  (可选)"
    status["phase9"] = "✅" if check_learnings_updated(root) else "⬜"

    return status


def list_phases(root: str):
    """列出所有阶段及状态"""
    status = get_phase_status(root)
    print("📋 SOP 阶段状态检查\n")
    print(f"{'阶段':<10} {'角色':<12} {'状态':<15} {'必需':<8}")
    print("-" * 50)
    for phase_id, info in sorted(PHASES.items(), key=lambda x: x[1]["order"]):
        required = "否" if info.get("optional") else "是"
        print(f"{info['name']:<10} {info['role']:<12} {status[phase_id]:<15} {required:<8}")


def check_phase(readiness: Dict[str, str], phase_id: str) -> Tuple[bool, List[str]]:
    """检查指定阶段的前置条件"""
    issues = []
    root = get_project_root()

    prerequisites = {
        "phase1": [],  # 无前置条件
        "phase2": ["phase1"],
        "phase3": ["phase1"],
        "phase4": ["phase1"],
        "phase5": ["phase1"],
        "phase6": ["phase5"],
        "phase7": ["phase6"],
        "phase8": ["phase6"],
        "phase9": ["phase7"],
    }

    pre = prerequisites.get(phase_id, [])
    for p in pre:
        if p == "phase1" and not check_prd_exists(root):
            issues.append("Phase 1 未完成：缺少 PRD/需求文档")
        if p == "phase5" and not check_architecture_exists(root):
            issues.append("Phase 5 未完成：缺少架构设计文档")
        if p == "phase6" and not check_code_exists(root):
            issues.append("Phase 6 未完成：缺少代码文件")
        if p == "phase7" and not check_tests_exist(root):
            issues.append("Phase 7 未完成：缺少测试文件")

    if phase_id == "phase9":
        if not check_learnings_updated(root):
            issues.append("learnings 目录不完整，请先完成自进化复盘")

    return len(issues) == 0, issues


def main():
    parser = argparse.ArgumentParser(description="SOP 阶段检查脚本")
    parser.add_argument("--phase", type=str, help="检查指定阶段")
    parser.add_argument("--list", action="store_true", help="列出所有阶段状态")
    parser.add_argument("--next", action="store_true", help="检查下一阶段是否就绪")
    args = parser.parse_args()

    root = get_project_root()

    if args.list:
        list_phases(root)
        return

    if args.next:
        status = get_phase_status(root)
        for phase_id in sorted(PHASES.keys(), key=lambda x: PHASES[x]["order"]):
            if status[phase_id] == "⬜" or "⬜" in status[phase_id]:
                print(f"👉 下一阶段: {PHASES[phase_id]['name']} ({PHASES[phase_id]['role']})")
                ok, issues = check_phase(status, phase_id)
                if ok:
                    print("✅ 前置条件已满足，可以进入")
                else:
                    print("⚠️  前置条件未满足:")
                    for i in issues:
                        print(f"   - {i}")
                return
        print("✅ 所有阶段已完成")
        return

    if args.phase:
        phase_id = args.phase
        if phase_id not in PHASES:
            print(f"❌ 无效阶段: {phase_id}，可用阶段: {', '.join(PHASES.keys())}")
            sys.exit(1)
        status = get_phase_status(root)
        ok, issues = check_phase(status, phase_id)
        info = PHASES[phase_id]
        print(f"🔍 检查 {info['name']} ({info['role']}) 前置条件...")
        if ok:
            print("✅ 前置条件已满足")
        else:
            print("❌ 前置条件未满足:")
            for i in issues:
                print(f"   - {i}")
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
