# Dream Team Workflow Skill

红楼梦智数团队协作技能 - 基于 SOP 驱动的全栈开发与数据智能团队工作流。

## 功能特性

- ⚡ **快速模式**：适用于小型需求（≤10 文件）
- 🔧 **BugFix**：Bug 修复快捷路径
- 🎯 **敏捷战队**：AI-RAG / 算法建模 / 安全加固专项
- 🏗️ **标准 SOP**：中大型企业级项目
- 🔄 **LLMOps**：线上 AI 系统持续优化

## 团队角色

| 角色 | 职责 |
|------|------|
| 交付总监 | 全局调度、流程编排 |
| 产品经理 | PRD、需求分析 |
| UI/UX 设计师 | 视觉设计、BI 大屏 |
| AI 工程师 | Prompt/RAG、NL2SQL |
| ML 工程师 | 数据建模、模型训练 |
| 架构师 | 系统架构、4A 鉴权 |
| 工程师 | 业务编码 |
| QA 工程师 | 测试、数据画像 |
| DevOps | 部署、CI/CD |

## 目录结构

```
dream-team-workflow/
├── SKILL.md           # 主技能文件
├── README.md          # 说明文档
├── evals/
│   └── evals.json     # 测试用例
├── learnings/         # 自进化复盘记录（强制写入）
│   ├── successful_patterns.md  # 成功模式（SP 编号）
│   ├── bad_cases.md            # 踩坑记录（BC 编号）
│   └── evolution_log.md        # 规约提取 + 版本快照（EP 编号）
└── scripts/
    ├── route_workflow.py  # 工作流路由脚本
    └── run_evals.py       # 自动化评估测试
```

## 使用方法

当用户在 WorkBuddy 中发送开发相关请求时，skill 会自动触发并推荐合适的工作流。

### 命令行测试

```bash
# 测试单个工作流路由
python scripts/route_workflow.py "帮我开发一个贪吃蛇游戏"
```

## 自动化评估测试

可以使用内置的评估脚本自动对 `evals/evals.json` 中的所有测试用例进行路由准确性校验：

```bash
# 运行自动化路由匹配评测
python scripts/run_evals.py
```

## 工作流类型

| 类型 | 适用场景 | 流程 |
|------|---------|------|
| 快速模式 | 小工具、单页应用 | 工程师 → QA |
| BugFix | Bug 修复 | 工程师 → QA |
| 敏捷战队(AI) | Prompt/RAG 调优 | PM → AI → 工程师 → QA |
| 敏捷战队(建模) | 数据分析建模 | PM → ML → 工程师 → QA |
| 敏捷战队(安全) | 4A/脱敏/权限修复 | 架构 → 工程师 → QA → DevOps |
| AI-Agent 战队 | Agent 拓扑/工具/记忆/HITL | AI → 架构 → 工程师 → QA |
| MCP Server 战队 | MCP 服务器开发 | AI → 架构 → 工程师 → QA |
| 标准 SOP | 中大型项目 | PM → 设计 → 架构 → 编码 → 测试 |
| LLMOps | 线上反馈 | 收集 → 优化 → 回归 → 部署 |
