#!/usr/bin/env python3
"""
红楼智数专家团 MCP Server

提供 4 个核心工具，供 Codex、Claude、Cursor 等 MCP 兼容 AI 工具调用：
1. sop_phase_check    — 检查当前项目 SOP 阶段完成状态
2. learnings_search   — 检索自进化学习库（成功模式、踩坑记录、进化规约）
3. workflow_route     — 根据用户需求判断应使用的工作流类型
4. team_role_info     — 获取指定团队角色的详细信息

启动方式：
    python mcp_server/server.py
    # 或通过 fastmcp run mcp_server/server.py
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEARNINGS_DIR = PROJECT_ROOT / "learnings"
AGENTS_DIR = PROJECT_ROOT / "agents"

mcp = FastMCP("红楼智数专家团")


# ──────────────────────────────────────────────
# 工具 1: SOP 阶段检查
# ──────────────────────────────────────────────

PHASES = {
    "phase1": {"name": "需求分析", "role": "林黛玉", "order": 1, "optional": False},
    "phase2": {"name": "UI/UX 设计", "role": "惜春", "order": 2, "optional": True},
    "phase3": {"name": "AI 设计", "role": "妙玉", "order": 3, "optional": True},
    "phase4": {"name": "ML 建模", "role": "香菱", "order": 4, "optional": True},
    "phase5": {"name": "架构设计", "role": "贾宝玉", "order": 5, "optional": False},
    "phase6": {"name": "编码实现", "role": "薛宝钗", "order": 6, "optional": False},
    "phase7": {"name": "测试验证", "role": "紫鹃", "order": 7, "optional": False},
    "phase8": {"name": "部署", "role": "探春", "order": 8, "optional": True},
    "phase9": {"name": "交付总结", "role": "王熙凤", "order": 9, "optional": False},
}


def _check_prd_exists(target_dir: Optional[str] = None) -> bool:
    root = Path(target_dir) if target_dir else PROJECT_ROOT
    prd_indicators = ["prd", "PRD", "需求文档", "需求分析", "产品需求"]
    for f in list(root.glob("*")) + list((root / "docs").glob("*") if (root / "docs").is_dir() else []):
        if f.is_file() and any(ind in f.name for ind in prd_indicators):
            return True
    return False


def _check_code_exists(target_dir: Optional[str] = None) -> bool:
    root = Path(target_dir) if target_dir else PROJECT_ROOT
    code_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".html", ".css", ".vue"}
    src_dirs = ["src", "app", "lib", "components", "pages", "api", "services", "utils"]
    for d in src_dirs:
        p = root / d
        if p.is_dir():
            for f in p.rglob("*"):
                if f.suffix in code_exts:
                    return True
            break
    for f in root.iterdir():
        if f.is_file() and f.suffix in code_exts:
            return True
    return False


def _check_tests_exist(target_dir: Optional[str] = None) -> bool:
    root = Path(target_dir) if target_dir else PROJECT_ROOT
    test_dirs = ["tests", "test", "__tests__", "spec"]
    for d in test_dirs:
        if (root / d).is_dir():
            return True
    for f in root.iterdir():
        if f.is_file() and (f.name.startswith("test_") or ".test." in f.name or ".spec." in f.name):
            return True
    return False


def _check_learnings_updated(target_dir: Optional[str] = None) -> bool:
    root = Path(target_dir) if target_dir else PROJECT_ROOT
    learnings = root / "learnings"
    required = ["successful_patterns.md", "bad_cases.md", "evolution_log.md"]
    return learnings.is_dir() and all((learnings / f).exists() for f in required)


@mcp.tool()
def sop_phase_check(target_dir: Optional[str] = None) -> str:
    """检查当前项目的 SOP 各阶段完成状态。

    Args:
        target_dir: 可选，要检查的项目目录路径。默认使用红楼专家团项目自身目录。

    Returns:
        各阶段状态表格，标注 ✅ 已完成 / ⬜ 未完成。
    """
    root = Path(target_dir) if target_dir else PROJECT_ROOT

    statuses = {}
    statuses["phase1"] = "✅" if _check_prd_exists(str(root)) else "⬜"
    statuses["phase2"] = "⬜ (可选)"
    statuses["phase3"] = "⬜ (可选)"
    statuses["phase4"] = "⬜ (可选)"
    statuses["phase5"] = "⬜"
    statuses["phase6"] = "✅" if _check_code_exists(str(root)) else "⬜"
    statuses["phase7"] = "✅" if _check_tests_exist(str(root)) else "⬜"
    statuses["phase8"] = "⬜ (可选)"
    statuses["phase9"] = "✅" if _check_learnings_updated(str(root)) else "⬜"

    lines = ["📋 SOP 阶段状态", f"📁 项目: {root}", "", "阶段 | 角色 | 状态 | 必需"]
    lines.append("-" * 50)
    for pid, info in sorted(PHASES.items(), key=lambda x: x[1]["order"]):
        req = "否" if info["optional"] else "是"
        lines.append(f"{info['name']:<10} | {info['role']:<10} | {statuses[pid]:<12} | {req}")

    # 建议下一阶段
    for pid in sorted(PHASES.keys(), key=lambda x: PHASES[x]["order"]):
        if "⬜" in statuses[pid] and not PHASES[pid]["optional"]:
            lines.append(f"\n👉 建议进入: {PHASES[pid]['name']} ({PHASES[pid]['role']})")
            break
    else:
        lines.append("\n✅ 所有必需阶段已完成")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 工具 2: 学习库检索
# ──────────────────────────────────────────────

@mcp.tool()
def learnings_search(query: str, category: str = "all") -> str:
    """检索自进化学习库，查找历史成功模式、踩坑记录或进化规约。

    Args:
        query: 搜索关键词（中文或英文）
        category: 检索范围，可选值: "all"(全部), "success"(成功模式), "bad_cases"(踩坑记录), "evolution"(进化规约)
    
    Returns:
        匹配的学习条目，包含编号、日期、描述。
    """
    files = {
        "success": LEARNINGS_DIR / "successful_patterns.md",
        "bad_cases": LEARNINGS_DIR / "bad_cases.md",
        "evolution": LEARNINGS_DIR / "evolution_log.md",
    }

    if category == "all":
        targets = list(files.values())
    elif category in files:
        targets = [files[category]]
    else:
        return f"❌ 无效分类: {category}，可选: all, success, bad_cases, evolution"

    results = []
    query_lower = query.lower()

    for filepath in targets:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        # 按 ### 标题分割条目
        entries = re.split(r"\n(?=### )", content)
        for entry in entries:
            if not entry.strip():
                continue
            if query_lower in entry.lower():
                # 提取前 3 行作为摘要
                lines = entry.strip().split("\n")
                header = lines[0].replace("### ", "").strip()
                summary = " | ".join(l.strip("- ") for l in lines[1:4] if l.strip().startswith("-"))
                source = filepath.name.replace(".md", "")
                results.append(f"【{source}】{header}\n  {summary}")

    if not results:
        return f"📭 未找到与「{query}」相关的学习记录"

    return "\n\n".join(results[:10])  # 最多返回 10 条


# ──────────────────────────────────────────────
# 工具 3: 工作流路由
# ──────────────────────────────────────────────

WORKFLOW_RULES = [
    # (regex 模式列表, 工作流名称, 描述)
    # 模式与 route_workflow.py WORKFLOW_RULES 语义对齐（route_workflow.py 匹配前
    # 先 lower()，模式一律用小写；通配符语义如 .? / .* 保留 regex 写法）。
    # 匹配方式：re.search(pattern, req_lower)，见 workflow_route()。

    # BugFix 优先 — 与 route_workflow.py BUGFIX 组对齐（18个）
    ([r"bug", r"修复", r"fix", r"报错", r"崩溃",
      r"闪退", r"出错了", r"不能用了", r"403", r"404", r"500", r"error",
      r"bad case", r"幻觉", r"漂移", r"跑不通", r"报错信息", r"编译失败"],
     "🔧 BugFix 快捷路径", "明确 Bug 报告，非新功能"),

    # 线上反馈 - LLMOps — 与 route_workflow.py LLMOPS 组对齐（9个）
    ([r"线上", r"生产", r"生产环境", r"bad case", r"模型幻觉", r"模型漂移",
      r"知识库更新", r"知识库增删", r"线上监控"],
     "🔄 LLMOps 反馈闭环", "线上 Bad Case 反馈"),

    # 安全加固专项 — 与 route_workflow.py AGILE_SEC 组对齐（10个）
    ([r"4a", r"权限", r"鉴权", r"脱敏", r"越权",
      r"安全漏洞", r"注入", r"sso", r"rbac", r"abac"],
     "🎯 安全加固敏捷战队", "4A/脱敏/权限修复"),

    # AI-Agent 战队专项 — 与 route_workflow.py AGILE_AGENT 组对齐（35个）
    ([r"agent工作流", r"agent拓扑", r"工具注册", r"tool registry",
      r"记忆架构", r"memory架构", r"checkpoint", r"状态持久化",
      r"hitl", r"human.?in.?the.?loop", r"黄金轨迹", r"golden trajectory",
      r"langgraph", r"autogen", r"crewai", r"agent评估",
      r"agent工具开发", r"agent重构", r"多agent", r"agent协作",
      r"agentops", r"agent.*可观测", r"agent.*护栏",
      r"long.?running", r"长时.*agent", r"异步编排",
      r"computer.?use", r"browser.?agent", r"浏览器操作",
      r"agentic.*rag", r"graphrag", r"图检索",
      r"inference.?time", r"reasoning.*model", r"推理时"],
     "🤖 AI-Agent 战队", "Agent 拓扑设计、工具注册、记忆架构、HITL、AgentOps"),

    # MCP Server 战队专项 — 与 route_workflow.py AGILE_MCP 组对齐（27个）
    ([r"mcp", r"model context protocol", r"mcp server", r"mcp服务",
      r"mcp服务器", r"fastmcp", r"mcp sdk", r"stdio",
      r"streamable http", r"mcp工具", r"mcp tool",
      r"mcp inspector", r"mcp transport", r"mcp传输",
      r"oauth 2\.1", r"pkce", r"elicitation",
      r"mcp registry", r"mcp注册", r"server\.json",
      r"mcp-ui", r"mcp app", r"ui://", r"mcp 2026",
      r"stateless", r"无状态", r"mcp无状态"],
     "🔌 MCP Server 战队", "MCP 服务器开发、工具设计、传输协议、无状态协议"),

    # AI/RAG 专项 — 与 route_workflow.py AGILE_AI 组对齐（11个）
    ([r"prompt", r"rag", r"nl2sql", r"text.?to.?sql",
      r"知识库", r"向量", r"embedding", r"检索",
      r"幻觉", r"ai评估", r"agent"],
     "🎯 AI-RAG 敏捷战队", "Prompt/RAG 调优，无大规模编码"),

    # 数据建模专项 — 与 route_workflow.py AGILE_ML 组对齐（16个）
    ([r"数据分析", r"数据清洗", r"eda", r"特征工程",
      r"建模", r"机器学习", r"模型训练", r"训练集",
      r"csv", r"excel", r"数据处理", r"数据画像",
      r"可视化", r"bi", r"报表", r"统计"],
     "🎯 算法建模敏捷战队", "数据清洗、特征工程、模型训练"),

    # 大型项目 - 标准SOP — 与 route_workflow.py STANDARD 组对齐（17个）
    ([r"电商平台", r"管理系统", r"平台架构", r"企业级", r"高并发", r"秒杀",
      r"日活", r"微服务", r"多模块", r"前后端分离", r"架构设计",
      r"部署方案", r"云原生", r"kubernetes", r"ci/cd", r"devops", r"容器化"],
     "🏗️ 标准 SOP", "中大型全栈项目"),

    # Spring AI 项目 — server.py 特有组（route_workflow.py 通过 STANDARD 组
    # 的架构设计类关键词路由后，由架构师启用 Spring AI 选型；此处为 MCP 端
    # 提供显式 Spring 技术栈识别，归入标准 SOP）
    ([r"spring", r"spring ai", r"springai", r"spring boot", r"springboot", r"java"],
     "🏗️ 标准 SOP", "Java/Spring AI 技术栈项目，架构师启用 Spring AI 选型"),

    # 小型项目 - 快速模式 — 与 route_workflow.py QUICK 组对齐（16个）
    ([r"帮我开发", r"开发一个", r"做一个", r"写一个",
      r"贪吃蛇", r"todo", r"待办", r"笔记",
      r"计算器", r"闹钟", r"小游戏", r"小工具",
      r"cli", r"脚本", r"单页", r"landing"],
     "⚡ 快速模式", "单页面/小工具/CLI/≤10文件"),
]


@mcp.tool()
def workflow_route(requirement: str) -> str:
    """根据用户需求描述，自动判断应使用哪种工作流。

    Args:
        requirement: 用户需求描述（中文或英文）

    Returns:
        推荐的工作流类型、描述和路由理由。
    """
    req_lower = requirement.lower()
    scores = {}

    for patterns, workflow, desc in WORKFLOW_RULES:
        score = sum(1 for p in patterns if re.search(p, req_lower))
        if score > 0:
            scores[workflow] = (score, desc)

    if not scores:
        # 默认判断：短需求 → 快速模式，长需求 → 标准 SOP
        if len(requirement) < 30:
            return "⚡ 快速模式\n描述: 单页面/小工具/CLI/≤10文件\n理由: 需求简短，建议快速交付"

        # 检查是否包含编码相关关键词
        code_keywords = ["开发", "实现", "代码", "写", "build", "implement", "code", "create"]
        if any(kw in req_lower for kw in code_keywords):
            return "🏗️ 标准 SOP\n描述: 中大型全栈项目\n理由: 需求涉及编码实现，建议走完整 SOP 流程"

        return "🏗️ 标准 SOP\n描述: 中大型全栈项目\n理由: 建议走完整 SOP 流程以确保质量"

    # 取最高分
    best = max(scores.items(), key=lambda x: x[1][0])
    return f"{best[0]}\n描述: {best[1][1]}\n理由: 匹配关键词得分 {best[1][0]}"


# ──────────────────────────────────────────────
# 工具 4: 团队角色信息
# ──────────────────────────────────────────────

ROLE_INFO = {
    "王熙凤": {
        "id": "dream-of-the-red-chamber-team-lead",
        "role": "交付总监",
        "responsibilities": ["全局调度与流程编排", "安全合规审计", "质量把关与交付总结", "自进化复盘执行"],
        "trigger": "所有项目均需",
    },
    "林黛玉": {
        "id": "dream-of-the-red-chamber-product-manager",
        "role": "产品经理",
        "responsibilities": ["PRD 撰写", "需求分析", "数据指标体系设计", "脱敏口径定义"],
        "trigger": "仅需 PRD / 需求分析",
    },
    "惜春": {
        "id": "dream-of-the-red-chamber-ui-designer",
        "role": "UI/UX 设计师",
        "responsibilities": ["视觉设计与交互流程", "BI 大屏设计", "多租户与脱敏展示"],
        "trigger": "仅需 UI / BI 大屏设计",
    },
    "妙玉": {
        "id": "dream-of-the-red-chamber-ai-engineer",
        "role": "AI 工程师",
        "responsibilities": ["Prompt/RAG 设计", "防注入策略", "NL2SQL 设计", "MCP 工具 Schema 设计"],
        "trigger": "仅需 Prompt / RAG / NL2SQL / MCP 设计",
    },
    "香菱": {
        "id": "dream-of-the-red-chamber-ml-engineer",
        "role": "ML 工程师",
        "responsibilities": ["数据清洗与特征工程", "模型训练与微调", "差分隐私建模"],
        "trigger": "仅需 Python 建模 / 微调",
    },
    "贾宝玉": {
        "id": "dream-of-the-red-chamber-architect",
        "role": "架构师",
        "responsibilities": ["系统架构设计", "4A 鉴权与 RLS 设计", "技术选型", "增量任务分解"],
        "trigger": "仅需架构评审",
    },
    "薛宝钗": {
        "id": "dream-of-the-red-chamber-engineer",
        "role": "工程师",
        "responsibilities": ["业务编码实现", "安全编码（参数化 SQL、脱敏）", "审计日志埋点"],
        "trigger": "仅需代码实现",
    },
    "紫鹃": {
        "id": "dream-of-the-red-chamber-qa-engineer",
        "role": "QA 工程师",
        "responsibilities": ["功能测试与安全测试", "权限渗透测试", "防退化回归测试", "数据画像"],
        "trigger": "仅需测试 / 数据洞察报告",
    },
    "探春": {
        "id": "dream-of-the-red-chamber-devops",
        "role": "DevOps 工程师",
        "responsibilities": ["CI/CD 配置", "容器化部署", "云原生配置", "环境变量管理"],
        "trigger": "仅需部署 / CI/CD",
    },
}

SINGLE_AGENT_ROUTES = {
    "prd": "林黛玉", "需求": "林黛玉", "需求分析": "林黛玉",
    "ui": "惜春", "设计": "惜春", "大屏": "惜春", "界面": "惜春",
    "prompt": "妙玉", "rag": "妙玉", "nl2sql": "妙玉", "注入": "妙玉", "mcp": "妙玉",
    "建模": "香菱", "微调": "香菱", "特征": "香菱", "训练": "香菱", "数据清洗": "香菱",
    "架构": "贾宝玉", "architecture": "贾宝玉", "鉴权": "贾宝玉", "rls": "贾宝玉",
    "代码": "薛宝钗", "编码": "薛宝钗", "实现": "薛宝钗",
    "测试": "紫鹃", "qa": "紫鹃", "数据画像": "紫鹃",
    "部署": "探春", "ci/cd": "探春", "devops": "探春", "容器": "探春",
}


@mcp.tool()
def team_role_info(role_name: Optional[str] = None) -> str:
    """获取红楼智数专家团成员的角色信息。

    Args:
        role_name: 可选，角色中文名（如"林黛玉"、"贾宝玉"）。不传则列出全部 9 位成员。

    Returns:
        角色详细信息：ID、职责、触发场景。
    """
    if role_name:
        if role_name in ROLE_INFO:
            info = ROLE_INFO[role_name]
            duties = "\n".join(f"  - {r}" for r in info["responsibilities"])
            return f"**{role_name}** — {info['role']}\nAgent ID: `{info['id']}`\n职责:\n{duties}\n触发场景: {info['trigger']}"
        return f"❌ 未找到角色「{role_name}」，可用角色: {', '.join(ROLE_INFO.keys())}"

    lines = ["## 红楼智数专家团 — 9 角色总览\n"]
    lines.append("| 角色 | 姓名 | Agent ID | 触发场景 |")
    lines.append("|------|------|----------|---------|")
    for name, info in ROLE_INFO.items():
        lines.append(f"| {info['role']} | {name} | `{info['id']}` | {info['trigger']} |")

    return "\n".join(lines)



# ──────────────────────────────────────────────
# 工具 5: Spring AI 架构与编码规范速查
# ──────────────────────────────────────────────

SPRING_AI_GUIDE = {
    "架构设计": {
        "框架": "Spring Boot 3.x + Spring AI 1.x",
        "依赖管理": "Maven/Gradle，`spring-ai-bom` 必须在 `<dependencyManagement>` 中声明版本",
        "核心模块": [
            "`spring-ai-openai-spring-boot-starter` — 模型调用",
            "`spring-ai-pgvector-spring-boot-starter` — pgvector 向量存储",
            "`spring-ai-mcp-client-spring-boot-starter` — MCP Client 集成",
        ],
        "向量存储选型": {
            "pgvector": "已有 PostgreSQL 的关系型场景",
            "Redis Stack": "低延迟缓存场景",
            "Milvus": "大规模向量检索场景",
        },
        "安全层": "Spring Security + OAuth2 Resource Server + JWT，`SecurityFilterChain` 配置 4A 鉴权拦截",
        "审计": "Spring AOP + Micrometer，`@Aspect` 切面采集审计日志",
    },
    "编码规范": {
        "ChatClient": "编写 `ChatClient` 调用层，含 `defaultSystem` 系统提示词与 `Advisor` 链",
        "Advisor链": "`QuestionAnswerAdvisor`（RAG 检索增强）+ `SafeGuardAdvisor`（内容安全过滤）链式调用",
        "VectorStore": "`@Bean VectorStore` 配置（pgvector / Redis Stack）",
        "Tool注册": "`@Tool` 函数注册，自动生成 JSON Schema 供 LLM 调用",
        "MCP集成": "`spring-ai-mcp-client-spring-boot-starter` 集成外部 MCP Server",
        "安全拦截": "Spring Security `SecurityFilterChain` 必须配置 JWT 解析 + 4A 权限拦截，API 路径按 `/api/**` 统一拦截",
    },
    "AI方案设计": {
        "ChatClient提示词": "设计 `ChatClient` 系统提示词与 `Advisor` 链编排方案",
        "Tool方案": "设计 `@Tool` 函数注册方案（含工具描述、参数 Record 定义、返回 Schema）",
        "MCP集成方案": "设计 `spring-ai-mcp-client-spring-boot-starter` 集成方案以调用外部 MCP Server",
    },
}


@mcp.tool()
def spring_ai_guide(topic: str = "all") -> str:
    """获取 Spring AI 企业级架构与编码规范速查。

    Args:
        topic: 查询主题，可选值: "all"(全部), "架构设计", "编码规范", "AI方案设计"

    Returns:
        Spring AI 架构设计、编码规范或 AI 方案设计指南。
    """
    if topic == "all":
        lines = ["## Spring AI 企业级开发规范速查\n"]
        for section, items in SPRING_AI_GUIDE.items():
            lines.append(f"### {section}")
            if isinstance(items, dict):
                for k, v in items.items():
                    if isinstance(v, list):
                        lines.append(f"- **{k}**:")
                        for vi in v:
                            lines.append(f"  - {vi}")
                    elif isinstance(v, dict):
                        lines.append(f"- **{k}**:")
                        for vk, vv in v.items():
                            lines.append(f"  - {vk}: {vv}")
                    else:
                        lines.append(f"- **{k}**: {v}")
            lines.append("")
        return "\n".join(lines)

    if topic in SPRING_AI_GUIDE:
        items = SPRING_AI_GUIDE[topic]
        lines = [f"## Spring AI {topic}\n"]
        if isinstance(items, dict):
            for k, v in items.items():
                if isinstance(v, list):
                    lines.append(f"- **{k}**:")
                    for vi in v:
                        lines.append(f"  - {vi}")
                elif isinstance(v, dict):
                    lines.append(f"- **{k}**:")
                    for vk, vv in v.items():
                        lines.append(f"  - {vk}: {vv}")
                else:
                    lines.append(f"- **{k}**: {v}")
        return "\n".join(lines)

    return f"❌ 无效主题: {topic}，可选: all, 架构设计, 编码规范, AI方案设计"



# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
