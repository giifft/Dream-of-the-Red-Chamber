# 红楼智数专家团 — CLAUDE.md

你已进入 **红楼智数专家团 (RedChamber-Swarm)** 运行环境。在响应开发、调试或系统分析任务时，你必须遵守本项目的多角色协作规范。

## 核心指引

- **协作铁律**：阅读并遵守 [AGENTS.md](./AGENTS.md) 中的四条正则、五条红线与工作流路由规则
- **主理人 Agent**：`agents/dream-of-the-red-chamber-team-lead.md` 定义了完整 SOP 编排逻辑
- **成员 Agent**：所有成员 Agent 定义在 `agents/` 目录下

## 自进化学习流

1. **前置检索**：接收任务前优先读取 `learnings/evolution_log.md`（提取硬约束）、`learnings/successful_patterns.md`（可复用模式）、`learnings/bad_cases.md`（防退化卡点）
2. **后置总结**：任务完成后将成功设计写入 `successful_patterns.md`，缺陷写入 `bad_cases.md`，更新 `evolution_log.md`

## 开发底线

- 依赖下载和模型拉取优先使用**国内高速源**（Python 推荐清华 PyPI，Node.js 推荐 `npmmirror.com`，Java 推荐阿里云 Maven；大模型国内开源首选**魔搭社区 ModelScope**，国外开源强制配置 `hf-mirror.com` 镜像）
- 数据安全：SQL 参数化防注入，PII 字段脱敏，敏感变更审计日志上报
- 渐进式开发：先调研、理清疑点再动手
