---
name: tflow-init
description: 初始化测试流程工作空间（自动状态检测 + 办公流程配置）
argument-hint: "[--auto] [--from-template TEMPLATE-ID]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---
<purpose>
初始化新的测试流程工作空间。通过自动状态检测和统一流程，创建必要的目录结构、状态文件和配置。不涉及代码工程规范，仅面向服务器测试领域的办公流程管理。
</purpose>

<context>
**Flags:**
- `--auto` -- 自动模式。跳过交互式问答，使用默认值或从 @ 引用文档提取配置。
- `--from-template TEMPLATE-ID` -- 从预设模板初始化。适用场景：回归测试、集成测试、预发布验证等标准测试流程。

**Load existing state if exists:**
Check for `.tflow/state.json` -- loads context if workspace already initialized.
</context>

<execution>
Follow '.tflow/workflows/workflow-init.md' completely.

**Report format on completion:**

```
=== TESTING WORKFLOW INITIALIZED ===
Workspace: {workspace_name}
State:   .tflow/state.json (active)

Created:
  .tflow/project.md
  .tflow/state.json
  .tflow/config.json
  .tflow/workflows/
  .tflow/tasks/
  .tflow/artifacts/

Next steps:
  /tflow-standard <测试任务描述>              -- 执行标准测试任务流程
  /tflow-status                               -- 查看工作空间状态
  /tflow-plan <phase>                         -- 规划测试阶段
```
</execution>

<error_codes>
| Code | Severity | Condition | Recovery |
|------|----------|-----------|----------|
| E001 | error | 缺少必要参数（--auto 但没有 @ 引用） | 检查参数格式，重新运行 |
| E002 | error | .tflow/ 已存在（greenfield init） | 检查 .tflow/ 目录状态，解决冲突 |
| E003 | error | 模板不存在（--from-template） | 使用 /tflow-templates 查看可用模板 |
| W001 | warning | Research agent 失败，继续使用部分结果 | 重试或继续 |
</error_codes>

<success_criteria>
- [ ] 交互式问答完成（或从文档/模板提取）
- [ ] `.tflow/project.md` 创建，包含：测试域、目标、流程边界
- [ ] `.tflow/state.json` 创建，artifacts[] 初始化为空
- [ ] `.tflow/config.json` 创建，包含：执行模式、验证偏好、通知设置
- [ ] `.tflow/workflows/` 创建，包含标准工作流模板
- [ ] `.tflow/tasks/` 和 `.tflow/artifacts/` 目录创建
- [ ] 用户了解下一步是 /tflow-standard
</success_criteria>
