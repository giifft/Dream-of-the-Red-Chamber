#!/usr/bin/env python3
"""
工作流路由脚本 - Workflow Router

根据用户需求自动判断应使用的工作流类型：
- 快速模式：小型需求、≤10 文件
- BugFix：Bug 修复
- 敏捷战队(AI)：Prompt/RAG 调优
- 敏捷战队(建模)：数据清洗/建模
- 敏捷战队(安全)：4A/脱敏/权限漏洞修复
- AI-Agent 战队：Agent 工作流设计、Tool 开发、记忆架构、HITL
- MCP Server 战队：MCP 服务器开发、工具设计、传输协议、评测
- 标准SOP：中大型需求
- LLMOps：线上反馈

Usage:
    python route_workflow.py "帮我开发一个贪吃蛇游戏"
    python route_workflow.py --analyze "用户报告登录后显示403"
    python route_workflow.py "设计一个带 HITL 的客服 Agent 工作流"
    python route_workflow.py "帮我开发一个 GitHub MCP 服务器"
"""

import re
import sys
import unicodedata
from typing import Tuple, List, Dict


# 工作流类型枚举
class WorkflowType:
    QUICK = "quick"           # 快速模式
    BUGFIX = "bugfix"         # Bug修复
    AGILE_AI = "agile_ai"     # 敏捷战队(AI)
    AGILE_ML = "agile_ml"     # 敏捷战队(建模)
    AGILE_SEC = "agile_sec"   # 敏捷战队(安全)
    AGILE_AGENT = "agile_agent"  # AI-Agent 战队
    AGILE_MCP = "agile_mcp"    # MCP Server 战队
    STANDARD = "standard"     # 标准SOP
    LLMOPS = "llmops"         # LLMOps反馈闭环
    PARTIAL = "partial"       # 部分工作流


# 工作流路由规则
# 注意：本表是路由关键词的权威参考表（供 server.py 等外部实现对齐），
# route_workflow() 的实际路由逻辑在 analyze_request() 的内联 patterns 中，
# 两处必须保持语义一致。模式一律小写（匹配前先 lower()），通配符用 regex 语法。
WORKFLOW_RULES = [
    # BugFix 优先
    (WorkflowType.BUGFIX, [
        r"bug", r"报错", r"崩溃", r"闪退", r"出错了", r"不能用了",
        r"403", r"404", r"500", r"error", r"fix", r"修复",
        r"bad case", r"幻觉", r"漂移", r"跑不通", r"报错信息", r"编译失败"
    ], "must_match_one"),


    # 线上反馈 - LLMOps
    (WorkflowType.LLMOPS, [
        r"线上", r"生产", r"bad case", r"模型幻觉",
        r"知识库更新", r"知识库增删", r"模型漂移",
        r"线上监控", r"生产环境"
    ], "must_match_one"),

    # 安全加固专项
    (WorkflowType.AGILE_SEC, [
        r"4a", r"权限", r"鉴权", r"脱敏", r"越权",
        r"安全漏洞", r"注入", r"sso", r"rbac", r"abac"
    ], "must_match_one"),

    # AI-Agent 战队专项
    # 注意：需与"敏捷战队(AI)"区分——后者面向 Prompt/RAG，前者面向 Agent 本体
    # 命中以下任一强信号即路由到 AI-Agent 战队
    (WorkflowType.AGILE_AGENT, [
        r"agent工作流", r"agent拓扑", r"工具注册", r"tool registry",
        r"记忆架构", r"memory架构", r"checkpoint", r"状态持久化",
        r"hitl", r"human.?in.?the.?loop", r"黄金轨迹", r"golden trajectory",
        r"langgraph", r"autogen", r"crewai", r"agent评估",
        r"agent工具开发", r"agent重构", r"多agent", r"agent协作",
        r"agentops", r"agent.*可观测", r"agent.*护栏",
        r"long.?running", r"长时.*agent", r"异步编排",
        r"computer.?use", r"browser.?agent", r"浏览器操作",
        r"agentic.*rag", r"graphrag", r"图检索",
        r"inference.?time", r"reasoning.*model", r"推理时"
    ], "must_match_one"),

    # MCP Server 战队专项
    # 命中以下任一强信号即路由到 MCP Server 战队
    (WorkflowType.AGILE_MCP, [
        r"mcp", r"model context protocol", r"mcp server", r"mcp服务",
        r"mcp服务器", r"fastmcp", r"mcp sdk", r"stdio",
        r"streamable http", r"mcp工具", r"mcp tool",
        r"mcp inspector", r"mcp transport", r"mcp传输",
        r"oauth 2\.1", r"pkce", r"elicitation",
        r"mcp registry", r"mcp注册", r"server\.json",
        r"mcp-ui", r"mcp app", r"ui://", r"mcp 2026",
        r"stateless", r"无状态", r"mcp无状态"
    ], "must_match_one"),

    # AI/RAG 专项
    (WorkflowType.AGILE_AI, [
        r"prompt", r"rag", r"nl2sql", r"text.?to.?sql",
        r"知识库", r"向量", r"embedding", r"检索",
        r"幻觉", r"ai评估", r"agent"
    ], "must_match_one"),

    # 数据建模专项
    (WorkflowType.AGILE_ML, [
        r"数据分析", r"数据清洗", r"eda", r"特征工程",
        r"建模", r"机器学习", r"模型训练", r"训练集",
        r"csv", r"excel", r"数据处理", r"数据画像",
        r"可视化", r"bi", r"报表", r"统计"
    ], "must_match_one"),

    # 大型项目 - 标准SOP
    (WorkflowType.STANDARD, [
        r"电商平台", r"管理系统", r"平台架构", r"企业级",
        r"高并发", r"秒杀", r"日活", r"微服务",
        r"多模块", r"前后端分离", r"架构设计",
        r"部署方案", r"云原生", r"kubernetes",
        r"ci/cd", r"devops", r"容器化"
    ], "must_match_one"),

    # 小型项目 - 快速模式
    (WorkflowType.QUICK, [
        r"帮我开发", r"开发一个", r"做一个", r"写一个",
        r"贪吃蛇", r"todo", r"待办", r"笔记",
        r"计算器", r"闹钟", r"小游戏", r"小工具",
        r"cli", r"脚本", r"单页", r"landing"
    ], "must_match_one"),
]


def analyze_request(request: str) -> Dict:
    """分析用户请求，返回关键特征"""
    request_lower = request.lower()

    features = {
        "has_bug_report": False,
        "has_ai_requirement": False,
        "has_data_requirement": False,
        "has_security_requirement": False,
        "has_agent_requirement": False,
        "has_mcp_requirement": False,
        "has_deployment": False,
        "has_large_scale": False,
        "is_small_project": False,
        "is_llmops_feedback": False,
    }

    # 检测 Bug 报告
    bug_patterns = [r"bug", r"报错", r"崩溃", r"出错了", r"403", r"404", r"error"]
    for pattern in bug_patterns:
        if re.search(pattern, request_lower):
            features["has_bug_report"] = True
            break

    # 检测 AI/RAG 需求
    ai_patterns = [r"ai", r"rag", r"llm", r"prompt", r"大模型", r"知识库", r"agent", r"gpt", r"chat", r"spec.?driven", r"sdd", r"raas", r"按结果计费", r"ag.?ui", r"generative.?ui", r"test.?as.?code", r"测试即代码", r"agentic.?qa", r"自愈测试"]
    for pattern in ai_patterns:
        if re.search(pattern, request_lower):
            features["has_ai_requirement"] = True
            break

    # 检测数据分析需求 (排除单纯的"数据库")
    data_patterns = [r"数据分析", r"csv", r"excel", r"数据清洗", r"数据统计", r"数据建模", r"数据画像", r"bi", r"可视化", r"报表", r"eda", r"特征工程"]
    for pattern in data_patterns:
        if re.search(pattern, request_lower):
            features["has_data_requirement"] = True
            break

    # 检测安全需求
    security_patterns = [r"4a", r"权限", r"鉴权", r"脱敏", r"越权", r"安全", r"sso", r"rbac", r"abac"]
    for pattern in security_patterns:
        if re.search(pattern, request_lower):
            features["has_security_requirement"] = True
            break

    # 检测 Agent 本体需求（注意：与 AI/RAG 区分，这里聚焦 Agent 拓扑/工具/记忆/HITL）
    agent_patterns = [
        r"agent工作流", r"agent拓扑", r"工具注册", r"tool registry",
        r"记忆架构", r"memory架构", r"checkpoint", r"状态持久化",
        r"hitl", r"human.?in.?the.?loop", r"黄金轨迹", r"golden trajectory",
        r"langgraph", r"autogen", r"crewai", r"agent评估",
        r"agent工具", r"agent重构", r"多agent", r"agent协作",
        r"agentops", r"agent.*可观测", r"agent.*护栏",
        r"long.?running", r"长时.*agent", r"异步编排",
        r"computer.?use", r"browser.?agent", r"浏览器操作",
        r"agentic.*rag", r"graphrag", r"图检索",
        r"inference.?time", r"reasoning.*model", r"推理时"
    ]
    for pattern in agent_patterns:
        if re.search(pattern, request_lower):
            features["has_agent_requirement"] = True
            break

    # 检测 MCP Server 开发需求
    mcp_patterns = [
        r"mcp", r"model context protocol", r"fastmcp", r"mcp sdk",
        r"stdio", r"streamable http", r"mcp server", r"mcp服务",
        r"mcp服务器", r"mcp工具", r"mcp tool", r"mcp inspector",
        r"oauth 2\.1", r"pkce", r"elicitation",
        r"mcp registry", r"mcp注册", r"server\.json",
        r"mcp-ui", r"mcp app", r"ui://", r"mcp 2026",
        r"stateless", r"无状态", r"mcp无状态"
    ]
    for pattern in mcp_patterns:
        if re.search(pattern, request_lower):
            features["has_mcp_requirement"] = True
            break

    # 检测部署需求
    deploy_patterns = [r"部署", r"devops", r"docker", r"kubernetes", r"ci/cd", r"容器", r"self.?healing", r"自愈", r"可观测", r"运维"]
    for pattern in deploy_patterns:
        if re.search(pattern, request_lower):
            features["has_deployment"] = True
            break

    # 检测大型项目
    large_patterns = [r"电商平台", r"管理系统", r"高并发", r"日活", r"微服务", r"架构设计", r"问答系统", r"分析系统", r"业务系统", r"企业级", r"self.?healing", r"自愈"]
    for pattern in large_patterns:
        if re.search(pattern, request_lower):
            features["has_large_scale"] = True
            break

    # 如果同时具备AI和安全需求，或者AI和数据需求，视为中大型复杂项目
    active_requirements = sum([
        features["has_ai_requirement"],
        features["has_data_requirement"],
        features["has_security_requirement"]
    ])
    if active_requirements >= 2:
        features["has_large_scale"] = True

    # 检测小型项目
    small_patterns = [r"小游戏", r"贪吃蛇", r"todo", r"待办", r"单页", r"cli", r"脚本"]
    for pattern in small_patterns:
        if re.search(pattern, request_lower):
            features["is_small_project"] = True
            break

    # 检测 LLMOps 反馈
    llmops_patterns = [r"线上", r"生产环境", r"bad case", r"模型幻觉", r"知识库更新"]
    for pattern in llmops_patterns:
        if re.search(pattern, request_lower):
            features["is_llmops_feedback"] = True
            break

    return features


def route_workflow(request: str) -> Tuple[str, str, List[str]]:
    """
    根据用户请求路由到最合适的工作流

    Returns:
        Tuple[workflow_type, description, involved_roles]
    """
    features = analyze_request(request)

    # BugFix 优先（但安全相关漏洞应由安全战队处理，不走 BugFix）
    if features["has_bug_report"] and not features["is_llmops_feedback"] and not features["has_security_requirement"]:
        return (
            WorkflowType.BUGFIX,
            "Bug 修复快捷路径：工程师定位修复 → QA 回归测试",
            ["工程师", "QA工程师"]
        )

    # LLMOps 反馈闭环
    if features["is_llmops_feedback"]:
        return (
            WorkflowType.LLMOPS,
            "LLMOps 反馈闭环：收集 Bad Case → 优化 → 回归评测 → 影子部署",
            ["QA工程师", "AI工程师/ML工程师", "工程师", "DevOps"]
        )

    # 安全加固专项
    if features["has_security_requirement"] and not features["has_large_scale"]:
        return (
            WorkflowType.AGILE_SEC,
            "敏捷战队(安全加固)：架构评审 → 代码修复 → 越权测试 → 网关更新",
            ["架构师", "工程师", "QA工程师", "DevOps"]
        )

    # AI-Agent 战队专项（Agent 本体设计优先于 AI/RAG，因为 Agent 是更高维度的交付物）
    if features["has_agent_requirement"] and not features["has_large_scale"]:
        return (
            WorkflowType.AGILE_AGENT,
            "AI-Agent 战队：Agent拓扑设计 → 工具注册表 → 记忆架构 → HITL节点 → 黄金轨迹评估",
            ["AI工程师", "架构师", "工程师", "QA工程师"]
        )

    # MCP Server 战队专项（MCP 服务器开发优先于 AI/RAG，因为是独立的交付物类型）
    if features["has_mcp_requirement"] and not features["has_large_scale"]:
        return (
            WorkflowType.AGILE_MCP,
            "MCP Server 战队：MCP工具设计 → 服务器架构 → 代码实现 → Inspector测试+评测",
            ["AI工程师", "架构师", "工程师", "QA工程师"]
        )

    # AI/RAG 专项
    if features["has_ai_requirement"] and not features["has_large_scale"] and not features["has_data_requirement"]:
        return (
            WorkflowType.AGILE_AI,
            "敏捷战队(AI-RAG)：PM 增量PRD → AI工程师设计 → 编码实现 → AI评测",
            ["产品经理", "AI工程师", "工程师", "QA工程师"]
        )

    # 数据建模专项
    if features["has_data_requirement"] and not features["has_ai_requirement"]:
        return (
            WorkflowType.AGILE_ML,
            "敏捷战队(算法建模)：PM 数据口径 → ML建模方案 → 数据脚本 → 数据校验",
            ["产品经理", "ML工程师", "工程师", "QA工程师"]
        )

    # 大型项目 - 标准SOP
    if features["has_large_scale"]:
        # 严格按 PM→UI→AI→ML→Architect→Engineer→QA→DevOps 顺序构建
        roles = ["产品经理"]
        if features["has_data_requirement"]:
            roles.append("UI/UX设计师")
        if features["has_ai_requirement"]:
            roles.append("AI工程师")
        if features["has_data_requirement"]:
            roles.append("ML工程师")
        roles.append("架构师")
        roles.append("工程师")
        roles.append("QA工程师")
        if features["has_deployment"]:
            roles.append("DevOps")
        return (
            WorkflowType.STANDARD,
            "标准SOP工作流：PRD → 设计 → 架构 → 编码 → 测试 → 部署",
            roles
        )

    # 小型项目 - 快速模式
    if features["is_small_project"]:
        return (
            WorkflowType.QUICK,
            "快速模式：工程师直接实现 → QA 验证",
            ["工程师", "QA工程师"]
        )

    # 默认：快速模式（大多数简单需求）
    return (
        WorkflowType.QUICK,
        "快速模式：工程师直接实现 → QA 验证",
        ["工程师", "QA工程师"]
    )


def _display_width(s: str) -> int:
    """计算字符串在终端中的显示宽度（中文/全角占2，ASCII占1）"""
    width = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def _pad_to_width(s: str, target_width: int) -> str:
    """按显示宽度补齐到 target_width（中文按2列计）；超长时截断并加省略号"""
    current = _display_width(s)
    if current > target_width:
        # 截断到 target_width-1 并加省略号
        result = ""
        w = 0
        for ch in s:
            ch_w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
            if w + ch_w > target_width - 1:
                break
            result += ch
            w += ch_w
        return result + "…"
    pad = max(0, target_width - current)
    return s + " " * pad


def print_workflow_recommendation(request: str) -> None:
    """打印工作流推荐结果"""
    workflow_type, description, roles = route_workflow(request)

    workflow_names = {
        WorkflowType.QUICK: "⚡ 快速模式",
        WorkflowType.BUGFIX: "🔧 BugFix 快捷路径",
        WorkflowType.AGILE_AI: "🎯 敏捷战队(AI-RAG)",
        WorkflowType.AGILE_ML: "🎯 敏捷战队(算法建模)",
        WorkflowType.AGILE_SEC: "🎯 敏捷战队(安全加固)",
        WorkflowType.AGILE_AGENT: "🤖 AI-Agent 战队",
        WorkflowType.AGILE_MCP: "🔌 MCP Server 战队",
        WorkflowType.STANDARD: "🏗️ 标准 SOP",
        WorkflowType.LLMOPS: "🔄 LLMOps 反馈闭环",
        WorkflowType.PARTIAL: "📋 部分工作流",
    }

    wf_name = workflow_names.get(workflow_type, workflow_type)
    roles_str = ", ".join(roles)

    # 按显示宽度对齐（中文占2列），内框内容宽度 48
    inner_w = 48
    line_wf = _pad_to_width(f" 推荐工作流: {wf_name}", inner_w)
    line_desc = _pad_to_width(f" 流程说明: {description}", inner_w)
    line_roles = _pad_to_width(f" 涉及角色: {roles_str}", inner_w)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    工作流推荐结果                              ║
╠══════════════════════════════════════════════════════════════╣
║{line_wf}║
║{line_desc}║
╠══════════════════════════════════════════════════════════════╣
║{line_roles}║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python route_workflow.py <用户需求>")
        print("示例: python route_workflow.py '帮我开发一个贪吃蛇游戏'")
        sys.exit(1)

    # 合并所有参数作为请求
    request = " ".join(sys.argv[1:])

    # 检查是否带 --analyze 参数
    if request.startswith("--analyze "):
        request = request[10:]

    print_workflow_recommendation(request)
